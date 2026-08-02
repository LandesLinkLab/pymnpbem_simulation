# CLI Reference

This document summarizes all options for `run_simulation.py` or
`python -m pymnpbem_simulation.cli`.

## Usage

```bash
python run_simulation.py --config CONFIG_YAML [OPTIONS]
```

## Options

### Required

- `--config PATH`
  Path to the YAML config file.

### Parallel Execution (Three-Axis Model)

- `--n-workers INT`
  Number of concurrent worker processes. Wavelengths are distributed across
  workers. Default: `compute.n_workers` from YAML, or 1.

- `--n-threads INT`
  Number of BLAS, OMP, and Numba threads inside each worker. Used to accelerate
  CPU-intensive operations.

- `--n-gpus-per-worker INT`
  - `0`: CPU only
  - `1`: One GPU per worker, following the Lane D pattern
  - `2+`: VRAM pool using cuSolverMg or Magma, planned as a follow-up to Lane E2

- `--multi-node`
  Enable mpi4py-based multi-node MPI dispatch. Disabled by default.
  Planned for Wave 3.

- `--auto`
  Automatically detect GPU and CPU resources in SLURM or PBS environments and
  generate a compute plan.
  - Detection priority:
    `SLURM_GPUS_ON_NODE`, `SLURM_JOB_GPUS`, `PBS_GPUFILE`,
    `CUDA_VISIBLE_DEVICES`

### Output

- `--output-dir PATH`
  Root output directory. Overrides YAML `output.dir`.

- `--simulation-name STR`
  Simulation name and output folder name. Overrides YAML `output.name`.

### Debugging and Workflow

- `--n-wavelengths INT`
  Number of wavelength subsamples for small regression tests.

- `--reanalyze`
  Skip the simulation and rerun analysis and plotting using the existing
  `spectrum.npz` file.

- `--verbose`
  Enable detailed logging.

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | YAML loading failed |
| 2 | Config validation failed |
| 3 | Multi-node mode is not implemented yet; planned for Wave 3 |
| 4 | Reanalysis failed because `spectrum.npz` was not found |

## Priority

CLI > YAML > `--auto` > defaults (`compute = {1, 1, 0}`)

## Examples

### Quick CPU Regression Test (10 Wavelengths)

```bash
python run_simulation.py \
    --config examples/dimer_baseline.yaml \
    --simulation-name dimer_quick \
    --n-wavelengths 10 \
    --n-workers 1 \
    --n-threads 4
```

### SLURM GPU Auto-Detection

```bash
srun -N1 --gres=gpu:4 python run_simulation.py \
    --config examples/dimer_baseline.yaml \
    --auto
```

### Explicit Multi-GPU Execution

```bash
python run_simulation.py \
    --config examples/dimer_baseline.yaml \
    --n-workers 4 \
    --n-gpus-per-worker 1
```

### Migration

```bash
python -m pymnpbem_simulation.migration.py_to_yaml \
    /path/to/config_str_dimer_g0.6.py \
    /path/to/config_sim_dimer_g0.6.py \
    examples/dimer_g0.6.yaml
```
