"""Exercise only the installed distribution, without a checkout import path."""
import importlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
import tempfile

from verify_distributions import MODULES, package_version, require


def verify():
    expected = package_version()
    require(sys.prefix != sys.base_prefix, "Run inside a fresh virtual environment")
    prefix = Path(sys.prefix).resolve()
    paths = {}
    for filename in MODULES:
        module_name = "heartland_synthetic." + filename.removesuffix(".py").replace("/", ".")
        module_name = module_name.removesuffix(".__init__")
        module = importlib.import_module(module_name)
        origin = Path(module.__file__).resolve()
        require(origin.is_relative_to(prefix), f"Module is not installed in this environment: {module_name}")
        paths[module_name] = str(origin)
    import heartland_synthetic as package
    require(version("heartland-synthetic") == package.__version__ == expected, "Installed version mismatch")
    cohort = package.generate_cohort(package.HeartlandCohortConfig(n_patients=12, seed=42))
    rescored = package.apply_heartland_scoring(cohort)
    require(cohort.equals(rescored), "Installed scoring disagrees")
    require(len(package.generate_time_series(cohort, months=3, seed=42)) == 36, "Installed time-series shape mismatch")
    with tempfile.TemporaryDirectory(prefix="heartland-installed-") as temporary:
        root = Path(temporary)
        require(len(package.export_fhir_bundle(cohort, root / "fhir")) == 12, "Installed FHIR export failed")
        require(all(p.is_file() for p in package.export_redcap(cohort, root / "redcap")), "Installed REDCap export failed")
    return {"version": expected, "python": sys.version, "executable": sys.executable,
            "dependencies": {name: version(name) for name in ("numpy", "pandas", "scipy")}, "module_paths": paths}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
