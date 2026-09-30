"""Archive-verifier negatives, independent of a live registry/build backend."""
import base64
import csv
import importlib.util
import io
from pathlib import Path
import hashlib
import gzip
import stat
import tarfile
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("distribution_verifier", ROOT / "scripts/verify_distributions.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def record(files, record_name):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    for name, value in files.items():
        writer.writerow([name, "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(value).digest()).rstrip(b"=").decode(), len(value)])
    writer.writerow([record_name, "", ""])
    return buffer.getvalue().encode()


def write_wheel(path, files):
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)


def write_sdist(path, files):
    with tarfile.open(path, "w:gz") as archive:
        for name, data in files.items():
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            archive.addfile(entry, io.BytesIO(data))


@pytest.fixture
def archives(tmp_path):
    version = verifier.package_version(ROOT)
    prefix = f"heartland_synthetic-{version}"
    info = f"{prefix}.dist-info"
    project = verifier.tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    dependencies = "".join(f"Requires-Dist: {value}\n" for value in verifier.expected_requirements(project))
    extras = "".join(f"Provides-Extra: {value}\n" for value in project["optional-dependencies"])
    metadata = (f"Metadata-Version: 2.4\nName: {project['name']}\nVersion: {version}\nRequires-Python: {project['requires-python']}\nSummary: {project['description']}\n" + dependencies + extras + "\n" + (ROOT / "README.md").read_text()).encode()
    files = {f"heartland_synthetic/{name}": (ROOT / "src/heartland_synthetic" / name).read_bytes() for name in verifier.MODULES}
    files.update({f"{info}/METADATA": metadata, f"{info}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n", f"{info}/licenses/LICENSE": (ROOT / "LICENSE").read_bytes()})
    files[f"{info}/RECORD"] = record(files, f"{info}/RECORD")
    source_files = {f"{prefix}/{name}": (ROOT / name).read_bytes() for name in verifier.SOURCE_FILES}
    source_files[f"{prefix}/PKG-INFO"] = metadata
    wheel = tmp_path / f"{prefix}-py3-none-any.whl"
    source = tmp_path / f"{prefix}.tar.gz"
    write_wheel(wheel, files)
    write_sdist(source, source_files)
    return tmp_path, wheel, source, files, source_files, info, prefix


def test_exact_source_and_wheel_are_accepted(archives):
    directory, _, _, wheel, source, _, _ = archives
    result = verifier.verify(directory)
    assert result["wheel_members"] == len(wheel)
    assert result["source_members"] == len(source)
    assert len(result["artifacts"]) == 2


@pytest.mark.parametrize("kind", ["wheel", "source"])
@pytest.mark.parametrize("mutation", ["extra", "missing", "content", "metadata", "unsafe", "duplicate", "symlink"])
def test_archive_mutations_are_rejected(archives, kind, mutation):
    directory, wheel, source, wheel_files, source_files, info, prefix = archives
    files = wheel_files if kind == "wheel" else source_files
    path = wheel if kind == "wheel" else source
    module = "heartland_synthetic/scoring.py" if kind == "wheel" else f"{prefix}/src/heartland_synthetic/scoring.py"
    if mutation == "extra":
        files[f"{prefix}/AGENTS.md"] = b"unreviewed"
    elif mutation == "missing":
        del files[module]
    elif mutation == "content":
        files[module] += b"\n# changed\n"
    elif mutation == "metadata":
        key = f"{info}/METADATA" if kind == "wheel" else f"{prefix}/PKG-INFO"
        files[key] = files[key].replace(f"Version: {verifier.package_version()}".encode(), b"Version: 99.0.0")
    elif mutation == "unsafe":
        files["../outside"] = b"unreviewed"
    if kind == "wheel":
        write_wheel(path, files)
        if mutation in {"duplicate", "symlink"}:
            with zipfile.ZipFile(path, "a") as archive:
                entry = zipfile.ZipInfo(module if mutation == "duplicate" else "linked")
                if mutation == "symlink":
                    entry.create_system = 3
                    entry.external_attr = (stat.S_IFLNK | 0o777) << 16
                    archive.writestr(entry, "target")
                else:
                    with pytest.warns(UserWarning, match="Duplicate name"):
                        archive.writestr(entry, files[module])
    else:
        with tarfile.open(path, "w:gz") as archive:
            for name, data in files.items():
                entry = tarfile.TarInfo(name)
                entry.size = len(data)
                archive.addfile(entry, io.BytesIO(data))
            if mutation in {"duplicate", "symlink"}:
                entry = tarfile.TarInfo(module if mutation == "duplicate" else "linked")
                if mutation == "symlink":
                    entry.type = tarfile.SYMTYPE
                    entry.linkname = "target"
                archive.addfile(entry, io.BytesIO())
    with pytest.raises(ValueError):
        verifier.verify(directory)


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "hash", "size", "empty", "self_hash"])
def test_record_authenticates_every_member(archives, mutation):
    directory, wheel, _, files, _, info, _ = archives
    key = f"{info}/RECORD"
    rows = list(csv.reader(io.StringIO(files[key].decode())))
    if mutation == "missing":
        rows.pop(0)
    elif mutation == "extra":
        rows.append(["missing.py", "sha256=none", "0"])
    elif mutation == "duplicate":
        rows.append(rows[0])
    elif mutation == "hash":
        rows[0][1] = "sha256=invalid"
    elif mutation == "size":
        rows[0][2] = "0"
    elif mutation == "empty":
        rows[0][1:] = ["", ""]
    else:
        rows[-1][1] = "sha256=invalid"
    buffer = io.StringIO()
    csv.writer(buffer).writerows(rows)
    files[key] = buffer.getvalue().encode()
    write_wheel(wheel, files)
    with pytest.raises(ValueError, match="RECORD"):
        verifier.verify(directory)


@pytest.mark.parametrize("name", ["../file", "/file", "a/../file", "a//file", "./file", "a\\file", "a\nfile", "", ".", "C:/file"])
def test_noncanonical_member_name_rejected(name):
    with pytest.raises(ValueError):
        verifier.safe_name(name)


def test_extra_distribution_refused(archives):
    directory = archives[0]
    (directory / "unreviewed.whl").write_bytes(b"unreviewed")
    with pytest.raises(ValueError, match="exactly one"):
        verifier.verify(directory)


@pytest.mark.parametrize("member_type", [tarfile.LNKTYPE, tarfile.DIRTYPE, tarfile.FIFOTYPE])
def test_source_hardlinks_and_special_members_refused(archives, member_type):
    directory, _, source, _, files, _, _ = archives
    with tarfile.open(source, "w:gz") as archive:
        for name, data in files.items():
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            archive.addfile(entry, io.BytesIO(data))
        entry = tarfile.TarInfo("special")
        entry.type = member_type
        entry.linkname = next(iter(files)) if member_type == tarfile.LNKTYPE else ""
        archive.addfile(entry)
    with pytest.raises(ValueError, match="non-regular"):
        verifier.verify(directory)


def test_versions_must_agree_before_build(tmp_path):
    (tmp_path / "src/heartland_synthetic").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="0.3.0"\n')
    (tmp_path / "src/heartland_synthetic/__init__.py").write_text('__version__="0.2.2"\n')
    with pytest.raises(ValueError, match="versions disagree"):
        verifier.package_version(tmp_path)


@pytest.mark.parametrize("mutation", ["remove", "add", "change", "marker", "extra", "duplicate"])
@pytest.mark.parametrize("kind", ["wheel", "source"])
def test_installable_dependency_metadata_must_match_source(archives, kind, mutation):
    directory, wheel, source, wheel_files, source_files, info, prefix = archives
    files = wheel_files if kind == "wheel" else source_files
    key = f"{info}/METADATA" if kind == "wheel" else f"{prefix}/PKG-INFO"
    metadata = files[key]
    if mutation == "remove":
        metadata = metadata.replace(b"Requires-Dist: numpy>=1.24\n", b"")
    elif mutation == "add":
        metadata = b"Requires-Dist: unreviewed-dependency>=1\n" + metadata
    elif mutation == "change":
        metadata = metadata.replace(b"numpy>=1.24", b"numpy==1.24")
    elif mutation == "marker":
        metadata = metadata.replace(b'python_version < "3.11"', b'python_version >= "3.11"')
    elif mutation == "extra":
        metadata = metadata.replace(b"Provides-Extra: dev", b"Provides-Extra: other")
    else:
        metadata = b"Requires-Dist: numpy>=1.24\n" + metadata
    assert metadata != files[key]
    files[key] = metadata
    if kind == "wheel":
        # An attacker can recompute RECORD; it must not bypass the source contract.
        record_key = f"{info}/RECORD"
        del files[record_key]
        files[record_key] = record(files, record_key)
        write_wheel(wheel, files)
    else:
        write_sdist(source, files)
    with pytest.raises(ValueError, match="Metadata (dependencies|extras) mismatch"):
        verifier.verify(directory)


@pytest.mark.parametrize("kind", ["nonzero", "concatenated_tar", "concatenated_gzip"])
def test_hidden_source_suffix_rejected(archives, kind):
    directory, _, source, _, _, _, _ = archives
    original = source.read_bytes()
    if kind == "nonzero":
        source.write_bytes(gzip.compress(gzip.decompress(original) + b"unreviewed context"))
    else:
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:") as archive:
            entry = tarfile.TarInfo("AGENTS.md")
            entry.size = 7
            archive.addfile(entry, io.BytesIO(b"private"))
        source.write_bytes(gzip.compress(gzip.decompress(original) + stream.getvalue()) if kind == "concatenated_tar" else original + gzip.compress(stream.getvalue()))
    with pytest.raises(ValueError, match="after source archive EOF"):
        verifier.verify(directory)


@pytest.mark.parametrize("kind", ["prefix", "suffix", "comment"])
def test_hidden_wheel_envelope_rejected(archives, kind):
    directory, wheel, *_ = archives
    if kind == "comment":
        with zipfile.ZipFile(wheel, "a") as archive:
            archive.comment = b"unreviewed context"
    elif kind == "prefix":
        wheel.write_bytes(b"unreviewed context" + wheel.read_bytes())
    else:
        wheel.write_bytes(wheel.read_bytes() + b"unreviewed context")
    with pytest.raises(ValueError, match="wheel|Wheel"):
        verifier.verify(directory)
