# pymnpbem_simulation Regression Acceptance Criteria

Created: 2026-05-02 (Wave 3 M10)  
Target: pymnpbem_simulation v1.0  
Basis: Seven Wave 1 and Wave 2 smoke tests plus `lane_results/baseline_cpu.json`

This document defines the acceptance criteria automatically evaluated by the
regression suite in `tests/regression/`.

---

## 1. Grade Definitions

| Grade | Label | Definition (Maximum Relative Error) | Meaning |
|---|---|---|---|
| machine precision | `machine` | `< 1e-12` | Bit-level agreement within floating-point accumulation limits |
| OK | `OK` | `< 1e-9` | Numerically equivalent |
| good | `good` | `< 1e-6` | Visually equivalent |
| warn | `warn` | `< 1e-3` | Investigation recommended |
| BAD | `BAD` | `>= 1e-3` | Regression failure and release blocker |

The grading logic is implemented by `compute_grade()` in
`tests/regression/runners/compute_grade.py`.

---

## 2. Accuracy Criteria

### 2.1 Regression Grade Distribution

| Metric | Requirement |
|---|---|
| Number of BAD results | **= 0** (required) |
| Machine-precision ratio | `>= 80%` for smoke items limited to analyzers, builders, and imports |
| Total warn results | `<= 1 / N` for CLI smoke tests only |

CLI smoke tests usually receive a `warn` or `good` grade because BEM solver
results can differ by a few ULPs, with relative errors around `1e-7` to
`1e-4`.

Analyzer, builder, and import tests follow deterministic code paths and must
receive the `machine` grade.

### 2.2 Dimer Baseline Accuracy

Wave 1 regression case: 6,336 faces and two wavelengths.

| Metric | Current Measured Value | Requirement |
|---|---:|---|
| Peak `ext_x` at 500 nm | 8744.331 | Relative error `<= 1e-3` against the reference |
| `n_faces` | 6336 | Exact match |

Reference: `dimer_baseline_2wl` in `data/reference_results.json`.

### 2.3 Structure, Excitation, Substrate, Postprocess, and Field Tests

Each module contains fast tests for analyzers and builders and slow tests for
CLI smoke execution.

- Fast tests:
  - Deterministic
  - Must receive the `machine` grade
- Slow tests:
  - Peak values from CLI results must have relative differences `<= 1e-3`
    from the reference
  - Must avoid the `BAD` grade

---

## 3. Performance Criteria

For:

```bash
run_full_regression.py --markers fast
```

the required limits are:

| Metric | Requirement |
|---|---|
| Total wall time for the fast subset | `< 60 s` |
| Total wall time for the slow subset | `< 30 min` on CPU with `n_threads = 4` |

Detailed expectations:

| Test | Expected Wall Time on CPU | Notes |
|---|---:|---|
| `test_structures` with 14 builds | `< 5 s` | fast |
| `test_postprocess` with 5 items | `< 10 s` | fast |
| `test_field` with analyzer and grid | `< 5 s` | fast |
| `test_dispatch` smoke test | `< 1 s` | fast |
| `test_dimer_baseline_2wl` | approximately 5 min | slow |
| `test_dimer_baseline_cpu_pool` | approximately 5 min | slow |
| `test_cube_cli_smoke` | approximately 1 min | slow |
| `test_*_excitation` with 5 types | approximately 2 min each | slow |
| `test_sphere_substrate_smoke` | approximately 3 min | slow |
| `test_field_calculator_dimer` | approximately 3 min | slow |

GPU and multi-node tests are limited to self-hosted runners.

---

## 4. Environment

- Python 3.11
- Conda environment: `mnpbem`
- Main dependencies:
  - numpy
  - scipy
  - h5py
  - pytest
- Optional dependencies:
  - cupy for the `gpu` marker
  - `srun` for the `multinode` marker

---

## 5. Execution

```bash
PYBIN=$HOME/miniconda3/envs/mnpbem/bin/python

# Every commit and pull request
$PYBIN -m pytest tests/regression/ -m fast --tb=short -q

# Nightly
$PYBIN -m pytest tests/regression/ -m slow --tb=short -v

# Weekly, long full-spectrum tests
$PYBIN -m pytest tests/regression/ -m long --tb=short -v

# Integrated runner with grade-distribution reporting
$PYBIN tests/regression/runners/run_full_regression.py \
    --markers "fast or slow" \
    --json artifacts/regression_summary.json
```

Exit codes from `run_full_regression.py`:

- `0`: PASS, with `BAD = 0` and pytest return code `0`
- `1`: FAIL, with `BAD > 0` or a pytest failure

---

## 6. CI Recommendations

For `.github/workflows/regression.yml`:

- `on: pull_request`
  - Run only the `fast` marker
- `on: schedule` nightly
  - Run `fast + slow`
- `on: schedule` weekly
  - Run the full suite, including `long`

If a self-hosted runner with GPU and SLURM support is available, also include
the `gpu` and `multinode` markers.

---

## 7. Known Limitations

- Wave 2 smoke test 5, `dimer_field_1wl`, currently uses
  `PartialFallback` because the CLI grid branch is not connected.
  Another Wave 3 agent, Agent A for the M3 hotfix, is responsible for this.
  The regression suite currently validates only the standalone import and
  analyzer paths.
- The `multinode` marker is skipped automatically when no SLURM environment is
  available.
- The `gpu` marker is skipped automatically when CuPy is unavailable.
