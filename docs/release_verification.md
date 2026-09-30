# Distribution verification and release boundary

The 0.3.0 source candidate is not published merely because these checks pass.
Publishing remains a separately authorized step against an exact reviewed
commit/tag and set of files. Do not overwrite the frozen public cohort or
change the published-version labels before registry readback.

## Local and CI gates

1. Build in an isolated build environment into a new output directory. Use
   `python -m build --outdir <new-directory>`: the default builds the wheel
   from the source distribution, exercising its completeness.
2. Run `python -m twine check <wheel> <source-archive>` and
   `python scripts/verify_distributions.py <new-directory>`. The verifier
   checks exact reviewed source membership/content, metadata/version agreement
   including dependencies/extras/markers, paths, regular files, archive tails
   and the wheel RECORD checksums. It does not detect
   secrets in intentionally included source or prove runtime correctness.
3. Install the exact wheel, non-editably, into a fresh virtual environment
   with test dependencies. Run `scripts/verify_installed.py` with that Python
   from a separate temporary directory; the module paths must be under that
   environment, not this checkout. Exercise cohort/scoring/time-series and
   both exporters using synthetic inputs only.
4. Run the full test suite against the installed package with
   `python -m pytest --import-mode=importlib -o pythonpath= <absolute-tests-path>`
   from the separate directory. Do not inherit PYTHONPATH from a source checkout.
   Tests still read reviewed documentation/fixtures beside the test files;
   that does not mean the package is imported from source.
5. Retain distributions, inventory/hashes, runtime versions, installation
   receipts, test results and the reviewed source commit together. The source
   archive includes test fixtures and the frozen benchmark to support repeatable
   source-package checks, not to relabel the benchmark's generator version.

Run the verifier in the build/test environment with `packaging` available
(and `tomli` on Python 3.10). The supported wheel envelope is the bounded
pure-Python Hatch output: no ZIP64, links, comments, preambles, gaps or appended
payloads. TAR is decompressed in full and only zero padding may follow its EOF.
This deliberately narrow gate is not a general-purpose untrusted-archive service.

## Recorded numerical-runtime limitation

On the tested macOS/Accelerate environment, Python 3.10 with NumPy 2.2.6 emits
`matmul` divide/overflow/invalid warnings even for identity matrices. A separate
probe reproduced that upstream-library behavior without HEARTLAND: identity
products were exact, a 1,000-by-6 product agreed with scalar `math.fsum` within
4.45e-16, and all numeric cells in a 1,000-row cohort were finite. This is
consistent with [NumPy's reported backend issue](https://github.com/numpy/numpy/issues/28687),
not proof that every warning on every input is harmless.

The tested Python 3.12/NumPy 2.5.3 runtime did not emit those warnings. Prefer a
verified modern runtime for this candidate's local research examples; preserve
environment versions with results. No warnings are globally suppressed, and no
sampling expression/distribution is changed to work around the older backend.
These local receipts do not imply that every OS/dependency combination was tested.

## Package membership

The wheel contains only the Python package and generated distribution metadata.
The source archive contains the reviewed Python modules/tests, fixture JSON,
four export/model documents plus this runbook, the release verification scripts,
README/changelog/license/pyproject/Zenodo metadata, the tracked `.gitignore`
(also included automatically by Hatch), and the exact frozen CSV.
It excludes the website implementation/build output, CI configuration, local
instructions, graph data, environments, backups and credentials. An allowlist
and an exact archive-to-source comparison are complementary: neither is a
general secret scanner.

## Automated publication

CI and release preparation must run distribution and installed-package tests
before an artifact reaches the publishing job. The public-release event can
trigger PyPI Trusted Publishing and repository integrations such as Zenodo;
creating a GitHub release is therefore itself an external publishing action.
The release tag must match both version locations. Prereleases do not run the
PyPI publishing job. Preserve the environment approval gate and least-privilege
permissions; never treat a local test as approval of external accounts.

After authorized publication, verify the actual registry version, downloaded
artifact hashes, installation from the registry, website labels/downloads and
the existing Zenodo version family independently. A successful action does not
prove that another service's webhook completed. No upload is performed by the
verification scripts.

References: [Hatch file selection](https://hatch.pypa.io/1.13/config/build/),
[build's default sdist-to-wheel flow](https://build.pypa.io/en/latest/how-to/basic-usage.html),
[pytest installed-package practices](https://pytest.org/en/stable/explanation/goodpractices.html).
