# Validation record

Checked locally on 10 November 2026, Linux, Python 3.12.14.

| Check | Observed result |
|---|---|
| `ruff check .` | Passed |
| `ruff format --check .` | Passed |
| `pytest` | 48 passed |
| `python -m build` | Wheel and sdist built successfully |
| Wheel installation | Installed into a separate package directory; CLI/report-resource smoke check passed |
| Synthetic CLI run | 200 scenes; expected exit 1; all global metrics within tolerance; turning slice regression caught |
| Public AV2 import | 128 / 128 focal tracks accepted, zero skipped |
| Public AV2 reference comparison | Expected exit 1 for measured CA regressions versus CV |
| Output integrity | SHA-256 hashes verified for every manifest-listed artifact in both examples |
| HTML static checks | Embedded JSON parsed and scene counts checked; JavaScript syntax checked with Node |
| GitHub publishing script | Dry run passed; authenticated publication has not been executed |

The test suite covers analytical metric values and miss-boundary behavior; exact kinematic
predictions; deterministic bootstrap; input-order and translation invariance; history-only slices;
hidden slice regression; insufficient/uncertain evidence; input and prediction contract failures;
configuration errors; output immutability and script-embedding escaping; CLI exit behavior; stable
triage; and labeled/unlabeled AV2 track boundaries.

Tested direct dependencies: NumPy 2.3.5, pandas 2.2.3, PyArrow 23.0.1, pytest 9.2.0,
Ruff 0.17.4, build 1.6.1, setuptools 84.2.1. The local host's preinstalled AnyIO pytest plugin emitted
one deprecation warning; all tests passed. These are tested versions, not a transitive lockfile.

GitHub CI is configured for Python 3.11, 3.12 and 3.13; remote CI has not yet run. Local validation
was on Python 3.12 only. Browser visual/interaction QA was not completed: this environment's browser
does not permit opening workspace files directly. Static HTML/script and artifact checks passed.

Reproduce the numerical runs with the README commands. Do not interpret a successful build or test
suite as proof of vehicle safety, model generalization, fleet-scale performance, or statistical power.
