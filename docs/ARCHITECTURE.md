# pymnpbem_simulation - Architecture

## Design Principles

1. **Pipeline-first**: Establish end-to-end operation with the simplest dimer baseline first, then expand functionality.
2. **Remove MATLAB code generation**: Eliminate the former wrapper's `simulation_script.m` synthesis stage, which consisted of 4,034 lines. Call functions from the Python MNPBEM port directly.
3. **Python-native I/O**: Do not use `.mat` files. Use `.npz` for compressed data and `.h5` for large field data. Result analysis loads only `.npz` files.
4. **Three-axis parallelism**: `n_workers × n_threads × n_gpus_per_worker`. Use the same model for CPU and GPU execution.
5. **YAML config**: Use argparse and PyYAML. CLI overrides take precedence over YAML values.

## Module Responsibilities

| Module | Responsibility | Dependencies |
|---|---|---|
| `cli.py` | argparse, calls `env_setup`, calls dispatch, triggers postprocessing | all modules |
| `config.py` | YAML loading, validation, defaults, and snapshot saving | yaml |
| `auto_detect.py` | Detects SLURM, PBS, and `CUDA_VISIBLE_DEVICES`, then creates an `(n_w, n_t, n_g)` plan | os |
| `env_setup.py` | Sets environment variables such as `OMP_NUM_THREADS` and `MNPBEM_GPU`; must run before importing mnpbem | os |
| `util.py` | Seed handling, JSON saving with NFS retry, and tolerance grading | numpy |
| `structures/` | Converts the YAML `structure` section into an MNPBEM `ComParticle` object | mnpbem.geometry, materials |
| `simulation/` | Excitation, BEM solver, and wavelength loop | mnpbem.bem, simulation, spectrum |
| `dispatch/` | Selects the appropriate runner based on `n_workers` and `n_gpus_per_worker` | simulation |
| `io/` | Saves a result dictionary as `.npz` and `.json` | numpy |
| `postprocess/` | Spectrum analysis, including peak and FWHM extraction, and plotting | matplotlib |
| `migration/` | Converts legacy `.py` configs executed with `exec` into YAML | yaml |

## Data Flow

```text
   YAML config + CLI args
            │
            ▼
   load_yaml + merge_overrides + apply_defaults + validate
            │
            ▼
   auto_compute_plan / explicit (n_w, n_t, n_g)
            │
            ▼
   env_setup.setup_env(n_t, n_g)   ← must run before importing mnpbem
            │
            ▼
   build_structure → (ComParticle p, epstab, nfaces)
            │
            ▼
   dispatch_single_node:
     - serial CPU
     - CPU process pool (Wave 2)
     - multi-GPU dispatch (Wave 2, mnpbem.utils.multi_gpu)
     - MPI multi-node (Wave 3, mnpbem.utils.mpi_dispatch)
            │
            ▼
   result = {wavelength, ext, sca, abs, fields?, surface_charge?, ...}
            │
            ▼
   io.save_spectrum (.npz, .json)
   postprocess.analyze_spectrum (peak, FWHM, ...)
   postprocess.plot_spectrum (.png)
            │
            ▼
   {output_dir}/{name}/
       config.yaml
       run_metadata.json
       spectrum.npz
       spectrum.json
       spectrum_analysis.json
       spectrum.png
```

## Wave 1 → Wave 2 → Wave 3 → Wave 4 (M1-M10)

- Wave 1 (current): skeleton + `dimer_cube` `planewave_ret` CPU baseline
- Wave 2 (M2-M6): GPU dispatch, field calculation, 12 structures, dipole + EELS, substrate, and full postprocessing
- Wave 3 (M7, M9): mirror + iterative + nonlocal, and multi-node MPI + PBS
- Wave 4 (M10): regression testing with dimer, 51 sphere/rod cases, and 72 demos

## CONVENTIONS Requirements

- Do not use f-strings; use `.format()`.
- Explicitly declare every class with `(object)`.
- Include spaces on both sides of `=` in function keyword arguments.
- Do not use docstrings.
- Use the match/case pattern, including `case _: raise ValueError`.
- Do not use tensor concatenation with `concat` or `cat`; allocate with `empty` and assign through slices.

## Validation Baseline

Reference result from
`~/scratch/pymnpbem_sanity_test/lane_results/baseline_cpu.json`:

`dimer 47 nm × 2, gap 0.6 nm, e=0.2, 6,336 faces, 100 wavelengths`

- `wall_min`: 60.10 using 1 CPU worker × 4 threads
- Peak `ext_x` at 636.36 nm: 39,344.20
- Relative difference from MATLAB: `2.4e-4`, graded as `good`

The Wave 1 regression test, `tests/test_baseline_dimer.py`, uses a
10-wavelength subsample and should complete in approximately 6 minutes.
