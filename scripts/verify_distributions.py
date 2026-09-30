"""Inspect local distributions without extracting or uploading them."""
from __future__ import annotations

import argparse
import ast
import base64
import csv
from email.parser import BytesParser
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import struct
import tarfile
import zipfile
import zlib

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 test environments
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
MODULES = tuple("""
__init__.py _rng.py clinical.py comorbid.py config.py demographics.py gdmt.py
generator.py outcomes.py registries.py rural.py scoring.py timeseries.py
exports/__init__.py exports/_validation.py exports/fhir.py exports/redcap.py
""".split())
TESTS = tuple("""
conftest.py test_distributions.py test_export_inputs.py test_exports.py
test_fhir_semantics.py test_gdmt.py test_outcomes.py test_packaging.py
test_provenance.py test_redcap_semantics.py test_reproducibility.py test_rural.py
test_scoring.py test_timeseries.py fixtures/hand_computed_cases.json
""".split())
DOCS = tuple("""
export_input_contract.md fhir_export_mapping.md model_assumptions.md
redcap_template_crosswalk.md release_verification.md
""".split())
SOURCE_FILES = frozenset(
    [f"src/heartland_synthetic/{name}" for name in MODULES]
    + [f"tests/{name}" for name in TESTS]
    + [f"docs/{name}" for name in DOCS]
    + ["scripts/verify_distributions.py", "scripts/verify_installed.py",
       "README.md", "CHANGELOG.md", "LICENSE", "pyproject.toml", ".zenodo.json", ".gitignore",
       "site/public/data/heartland-synthetic-cohort-1000-seed42.csv"]
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_name(name):
    path = PurePosixPath(name)
    require(bool(path.parts) and not path.is_absolute() and "\\" not in name and ":" not in name
            and str(path) == name and ".." not in path.parts
            and all(ord(c) >= 32 and ord(c) != 127 for c in name),
            f"Non-canonical archive path: {name!r}")
    return name


def package_version(root=ROOT):
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    assignments = [node for node in ast.parse((root / "src/heartland_synthetic/__init__.py").read_text()).body
                   if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets)]
    require(len(assignments) == 1, "Expected one __version__ assignment")
    require(ast.literal_eval(assignments[0].value) == project["version"], "Source versions disagree")
    version = project["version"]
    require(isinstance(version, str) and version and all(c.isascii() and (c.isalnum() or c in ".+-!") for c in version), "Unsafe version")
    return version


def read_wheel(path):
    files = {}
    payload = path.read_bytes()
    with zipfile.ZipFile(path) as archive:
        require(not archive.comment, "Wheel archive comment is not permitted")
        cursor = 0
        for item in archive.infolist():
            name = safe_name(item.filename)
            mode = stat.S_IFMT(item.external_attr >> 16)
            require(not item.is_dir() and mode in (0, stat.S_IFREG), "Wheel contains a non-regular member")
            require(name not in files, "Duplicate wheel member")
            require(item.header_offset == cursor and not item.extra and not item.comment, "Unexpected wheel envelope data")
            header = struct.unpack_from("<4s5H3I2H", payload, cursor)
            encoded_name = name.encode("utf-8" if item.flag_bits & 0x800 else "cp437")
            require(header[0] == b"PK\x03\x04" and header[2] == item.flag_bits
                    and not item.flag_bits & 0x9 and header[3] == item.compress_type
                    and header[6:9] == (item.CRC, item.compress_size, item.file_size)
                    and header[9:] == (len(encoded_name), 0)
                    and payload[cursor + 30:cursor + 30 + len(encoded_name)] == encoded_name,
                    "Unexpected wheel local header")
            start = cursor + 30 + len(encoded_name)
            cursor = start + item.compress_size
            require(item.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED), "Unsupported wheel compression")
            if item.compress_type == zipfile.ZIP_DEFLATED:
                stream = zlib.decompressobj(-15)
                stream.decompress(payload[start:cursor])
                require(stream.eof and not stream.unused_data and not stream.unconsumed_tail, "Hidden wheel compressed suffix")
            files[name] = archive.read(item)
        # This bounded pure-Python wheel needs neither ZIP64 nor preambles,
        # comments, gaps or trailing data outside its declared members.
        require(cursor == archive.start_dir and len(payload) >= 22, "Unexpected wheel directory offset")
        end = struct.unpack_from("<4s4H2IH", payload, len(payload) - 22)
        require(end == (b"PK\x05\x06", 0, 0, len(files), len(files), len(payload) - 22 - cursor, cursor, 0), "Unexpected wheel archive suffix")
        expected_directory_size = sum(46 + len(i.filename.encode("utf-8" if i.flag_bits & 0x800 else "cp437")) for i in archive.infolist())
        require(end[5] == expected_directory_size, "Unexpected wheel central-directory data")
    return files


def read_sdist(path):
    files = {}
    # TAR readers stop at the first EOF block; do not publish an ignored second
    # archive or hidden nonzero suffix inside the fully decompressed stream.
    payload = gzip.decompress(path.read_bytes())
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
        for item in archive.getmembers():
            name = safe_name(item.name)
            require(item.isfile(), "Source archive contains a non-regular member")
            require(name not in files, "Duplicate source member")
            files[name] = archive.extractfile(item).read()
        require(not any(payload[archive.offset:]), "Nonzero data after source archive EOF")
    return files


def check_record(files, record_name):
    rows = list(csv.reader(io.StringIO(files[record_name].decode("utf-8"))))
    require(all(len(row) == 3 for row in rows), "Malformed RECORD row")
    names = [row[0] for row in rows]
    require(len(set(names)) == len(names) and set(names) == set(files), "RECORD is not bijective")
    for name, digest, size in rows:
        if name == record_name:
            require(digest == size == "", "RECORD self-entry must be unhashed")
        else:
            expected = "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(files[name]).digest()).rstrip(b"=").decode("ascii")
            require(digest == expected and size == str(len(files[name])), f"RECORD mismatch: {name}")


def expected_requirements(project):
    requirements = [Requirement(value) for value in project["dependencies"]]
    for extra, values in project.get("optional-dependencies", {}).items():
        for value in values:
            requirement = Requirement(value)
            marker = f'extra == "{canonicalize_name(extra)}"'
            requirement.marker = Marker(f"({requirement.marker}) and {marker}" if requirement.marker else marker)
            requirements.append(requirement)
    return requirements


def check_metadata(content, root, version):
    metadata = BytesParser().parsebytes(content)
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    for key, expected in [("Name", project["name"]), ("Version", version),
                          ("Requires-Python", project["requires-python"]),
                          ("Summary", project["description"])]:
        require(metadata.get_all(key) == [expected], f"Metadata mismatch: {key}")
    require(metadata.get_payload(decode=True).decode("utf-8").strip() == (root / "README.md").read_text().strip(), "Metadata README mismatch")
    actual = [Requirement(value) for value in metadata.get_all("Requires-Dist", [])]
    expected = expected_requirements(project)
    require(len(set(actual)) == len(actual) and set(actual) == set(expected), "Metadata dependencies mismatch")
    extras = [canonicalize_name(value) for value in metadata.get_all("Provides-Extra", [])]
    require(len(set(extras)) == len(extras) and set(extras) == {canonicalize_name(value) for value in project.get("optional-dependencies", {})}, "Metadata extras mismatch")


def verify(directory, root=ROOT):
    version = package_version(root)
    prefix = f"heartland_synthetic-{version}"
    expected_names = {f"{prefix}.tar.gz", f"{prefix}-py3-none-any.whl"}
    entries = list(directory.iterdir())
    require({p.name for p in entries} == expected_names and all(p.is_file() and not p.is_symlink() for p in entries), "Distribution directory must contain exactly one wheel and one source archive")
    wheel_path = directory / f"{prefix}-py3-none-any.whl"
    sdist_path = directory / f"{prefix}.tar.gz"
    wheel, sdist = read_wheel(wheel_path), read_sdist(sdist_path)
    info = f"{prefix}.dist-info"
    expected_wheel = {f"heartland_synthetic/{name}" for name in MODULES} | {
        f"{info}/{name}" for name in ("METADATA", "WHEEL", "RECORD", "licenses/LICENSE")
    }
    require(set(wheel) == expected_wheel, "Unexpected or missing wheel members")
    require(set(sdist) == {f"{prefix}/{name}" for name in SOURCE_FILES | {"PKG-INFO"}}, "Unexpected or missing source members")
    for name in SOURCE_FILES:
        source = root / name
        require(source.is_file() and not source.is_symlink(), f"Non-regular reviewed source: {name}")
        require(sdist[f"{prefix}/{name}"] == source.read_bytes(), f"Source content mismatch: {name}")
    for name in MODULES:
        require(wheel[f"heartland_synthetic/{name}"] == (root / "src/heartland_synthetic" / name).read_bytes(), f"Wheel content mismatch: {name}")
    require(wheel[f"{info}/licenses/LICENSE"] == (root / "LICENSE").read_bytes(), "Wheel license mismatch")
    check_metadata(wheel[f"{info}/METADATA"], root, version)
    check_metadata(sdist[f"{prefix}/PKG-INFO"], root, version)
    check_record(wheel, f"{info}/RECORD")
    wheel_metadata = BytesParser().parsebytes(wheel[f"{info}/WHEEL"])
    require(wheel_metadata.get_all("Tag") == ["py3-none-any"] and wheel_metadata.get("Root-Is-Purelib") == "true", "Unexpected wheel compatibility tags")
    return {"version": version, "wheel_members": len(wheel), "source_members": len(sdist),
            "artifacts": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(entries)}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.directory.resolve()), indent=2))
