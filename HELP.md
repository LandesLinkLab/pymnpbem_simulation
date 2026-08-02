# pymnpbem_simulation - User Guide

## CLI Entry Point

```bash
python run_simulation.py [OPTIONS]
```

Or as a module:

```bash
python -m pymnpbem_simulation.cli [OPTIONS]
```

## Required Options

| Option | Description | Default |
|---|---|---|
| `--config PATH` | Path to a YAML config file for a legacy single run | One of the three input modes is required |
| `--str-conf PATH --sim-conf PATH` | Separate structure and simulation `.py` configs for a single run | |
| `--sweep-conf PATH` | YAML config for running multiple cases in parallel with multi-worker fan-out | |

## Parallel Options (Three-Axis Model)

| Option | Description | Default |
|---|---|---|
| `--n-workers INT` | Number of concurrent worker processes, used as the wavelength distribution unit | 1 |
| `--n-threads INT` | Number of BLAS/OMP threads inside each worker | 1 |
| `--n-gpus-per-worker INT` | Number of GPUs assigned to each worker (`0` = CPU, `1` = single GPU, `2+` = VRAM pool) | 0 |
| `--multi-node` | Enable MPI multi-node execution; requires `mpi4py` | False |
| `--auto` | Automatically detect GPU and CPU resources in SLURM/PBS environments | False |

Priority order: CLI > YAML > `--auto` > defaults.

## Other Options

| Option | Description |
|---|---|
| `--output-dir PATH` | Output directory, overriding the YAML value |
| `--simulation-name STR` | Simulation name, used as the output folder name |
| `--n-wavelengths INT` | Number of wavelength subsamples for debugging |
| `--reanalyze` | Skip the simulation and rerun postprocessing only |
| `--verbose` | Enable detailed logging |
| `--help` | Show help |

## YAML Config Structure

```yaml
structure:
  type: dimer_cube              # sphere | cube | rod | dimer_cube | ...
  edge: 47.0                    # nm
  gap: 0.6                      # nm
  n_per_edge: 24                # mesh density
  refine: 3
  e: 0.2                        # rounding fraction for tricube

simulation:
  type: ret                     # ret | stat
  excitation: planewave         # planewave | dipole | eels
  enei_min: 500                 # nm
  enei_max: 1000
  n_wavelengths: 100
  polarizations: [[1,0,0], [0,1,0]]
  propagation_dirs: [[0,0,1], [0,0,1]]
  interp: curv

materials:
  medium: water
  particle: gold

compute:
  n_workers: 4
  n_threads: 1
  n_gpus_per_worker: 0
  multi_node: false
  hmode: dense

output:
  dir: ./results/dimer_baseline
  name: dimer_baseline
  formats: [npz, json, png]
  save_plots: true

postprocess:
  spectrum_xaxis: energy
  run_eigenmode_analysis: false
```

## Automatic Detection Behavior (`--auto`)

- SLURM `--gres=gpu:N` uses `SLURM_GPUS_ON_NODE=N`.
- PBS `-l gpus=N` uses `PBS_GPUFILE`.
- `CUDA_VISIBLE_DEVICES` is used as a fallback.

Heuristics:

- If `G >= 1`: `n_workers=G`, `n_gpus_per_worker=1`, and `n_threads=C//G`.
- If `G == 0`: `n_workers=C` and `n_threads=1`.

## Sweep Mode (`--sweep-conf`)

This mode runs multiple `(str_conf, sim_conf)` pairs in parallel. Each worker
is pinned to its own GPU using `CUDA_VISIBLE_DEVICES` and thread limits. On a
node with four GPUs, four cases can run simultaneously with one GPU per case,
providing up to 4x throughput.

### Format A - Explicit List

```yaml
# sweep.yaml
sim_conf: configs/jk/sim_default.py        # shared sim_conf
str_confs:
  - configs/jk/.../auag_g0.6.py
  - configs/jk/.../auag_g1.0.py
  - configs/jk/.../auag_g2.0.py
  - configs/jk/.../auag_g3.0.py
n_workers: 4                                # match the number of GPUs
gpus_per_worker: 1
output_dir: ./results/sweep_gap
output_subdir_pattern: '{idx:02d}_{name}'   # output folder naming pattern
```

If each case uses a different `sim_conf`:

```yaml
cases:
  - {str_conf: a.py, sim_conf: m1.py, name: foo}
  - {str_conf: b.py, sim_conf: m2.py, name: bar}
```

### Format B - Automatic Parameter Grid Generation

```yaml
base_str_conf: configs/jk/auag_base.py
sim_conf: configs/jk/sim_default.py
overrides:
  gap: [0.6, 1.0, 2.0, 3.0]
n_workers: 4
gpus_per_worker: 1
```

When multiple keys are specified, cases are expanded automatically as a
Cartesian product.

### Execution

```bash
python run_simulation.py --sweep-conf sweep.yaml
```

The CLI options `--n-workers`, `--n-threads`, `--n-gpus-per-worker`, and
`--output-dir` override the corresponding values in the sweep YAML file.

GPU IDs are detected automatically from `CUDA_VISIBLE_DEVICES` or
`nvidia-smi -L` and assigned to workers in round-robin order. They can also be
specified explicitly with `gpu_ids: [0, 1, 2, 3]`.

## Migration: Existing `.py` Config to YAML

```bash
python -m pymnpbem_simulation.migration.py_to_yaml \
    /path/to/config_str.py \
    /path/to/config_sim.py \
    output.yaml
```

For detailed mapping information, see
[docs/CONFIG_MIGRATION.md](./docs/CONFIG_MIGRATION.md).

## Output Structure

```text
{output_dir}/{name}/
├── config.yaml                 # snapshot of the config used
├── spectrum.npz                # ext, sca, abs, wavelength
├── spectrum.json               # peak and FWHM analysis results
├── spectrum.png                # plot
├── fields.npz                  # E_total, E_induced, etc. when calculate_fields=True
├── surface_charge.npz          # surface charge
└── logs/
    └── pipeline.log
```

## Validation Baseline

The results from `examples/dimer_baseline.yaml` should match the following
references at machine-precision level:

- `~/scratch/pymnpbem_sanity_test/lane_results/baseline_cpu.json`
  (60.10 min CPU, 100 wavelengths)
- `~/scratch/pymnpbem_sanity_test/spectra_python_postfix_v4.txt`

Tolerance levels:

- machine: `<1e-12`
- OK: `<1e-9`
- good: `<1e-6`
- warn: `<1e-3`
- BAD: `>=1e-3`
