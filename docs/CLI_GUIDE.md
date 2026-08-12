# CLI Guide - `--str-conf` / `--sim-conf` Pattern

This document explains the new CLI usage for `pymnpbem_simulation` and its
relationship to the legacy YAML CLI. The new pattern follows the same
interface style as `mnpbem_simulation`, the former MATLAB wrapper, by
separating the structure definition and simulation definition into two
`.py` config files.

## 1. Two Modes

### Mode A - New Pattern (Recommended, Compatible with mnpbem_simulation)

```bash
python run_simulation.py \
    --str-conf path/to/<name>_str.py \
    --sim-conf path/to/<name>_sim.py \
    --verbose
```

- `--str-conf <path.py>`: Structure definition, including `structure_type`,
  dimensions, materials, mesh density, and related parameters.
- `--sim-conf <path.py>`: Simulation, compute, and output definitions,
  including `simulation_type`, `wavelength_range`, `polarizations`,
  `compute = {n_workers, n_threads, n_gpus_per_worker, ...}`,
  `output = {dir, name}`, and related parameters.
- `--verbose`: Dumps the loaded `str_conf`, `sim_conf`, and merged config
  as JSON.

### Mode B - Legacy YAML (Backward Compatibility)

```bash
python run_simulation.py --config path/to/cfg.yaml
```

Existing jk-config YAML files such as `auag_r0.2_g0.6.yaml` continue to work
without modification. The `--config` option is required only when the new
mode is not used.

## 2. `.py` Config Format

Each `.py` config file must define exactly one dictionary named
**`args = {...}`**. The file is loaded with `exec()`. Loading fails if
`args` is missing or is not a dictionary.

### `str_conf` Example (`examples/auag_dimer_str.py`)

```python
args = {
    'structure': 'advanced_dimer_cube',
    'core_size': 47,
    'shell_layers': [4],
    'roundings': [0.2, 0.2],
    'mesh_density': 2,
    'gap': 0.6,
    'offset': [0, 0, 0],
    'tilt_angle': 0,
    'tilt_axis': [1, 0, 0],
    'rotation_angle': 0,
    'refine': 3,
    'materials': ['gold', 'silver'],
    'medium': 'water',
    'use_substrate': False,
    'refractive_index_paths': {
        'agcl': {'type': 'constant', 'epsilon': 2.02}}}
```

### `sim_conf` Example (`examples/auag_dimer_sim.py`)

```python
args = {
    'simulation_type': 'ret',
    'excitation_type': 'planewave',
    'wavelength_range': [300, 1000, 140],
    'polarizations': [[1, 0, 0], [0, 1, 0]],
    'propagation_dirs': [[0, 0, 1], [0, 0, 1]],
    'interp': 'curv',
    'relcutoff': 3,
    'calculate_cross_sections': True,
    'calculate_fields': False,
    # Field runs return the scattered field by default, matching MATLAB
    # @meshfield: emesh(sig) is the surface-charge field, so it decays to zero
    # far from the particle instead of to |E0|^2. Set True for the total field
    # the MATLAB near-field demos plot, i.e. emesh(sig) + emesh(exc.field(...)).
    # The result dict and field.json record which one was produced under
    # 'field_kind'.
    'field_total': False,

    'compute': {
        'use_parallel': True,
        'n_workers': 5,
        'n_threads': 1,
        'wavelength_chunk_size': 10,
        'iterative': True,
        'n_gpus_per_worker': 0,
        'multi_node': False,
        'hmode': 'dense'},

    'output': {
        'dir': './results',
        'name': 'auag_r0.2_g0.6',
        'formats': ['json', 'npz', 'png'],
        'save_plots': True}}
```

## 3. CLI Override Priority

```text
CLI flag > sim_conf nested compute/output > default
```

Common overrides:

| Flag | Effect |
|---|---|
| `--n-workers N` | Overrides `compute.n_workers` |
| `--n-threads N` | Overrides `compute.n_threads` |
| `--n-gpus-per-worker N` | Overrides `compute.n_gpus_per_worker` |
| `--vram-share-backend X` | Selects `cusolvermg`, `magma`, or `nccl`; relevant only when `n_gpus_per_worker > 1` |
| `--multi-node` | Sets `compute.multi_node = True` |
| `--auto` | Automatically detects the compute plan from the SLURM/PBS environment |
| `--simulation-name X` | Overrides `output.name`, which determines the run folder |
| `--output-dir DIR` | Overrides `output.dir` |
| `--n-wavelengths N` | Subsamples wavelengths for debugging |
| `--reanalyze` | Skips the simulation and reruns postprocessing only |
| `--verbose` | Prints `str_conf`, `sim_conf`, and the merged config |

## 4. Conversion Tools

### Legacy `.py` Configs in the mnpbem_simulation Format to YAML

```bash
python -m pymnpbem_simulation.migration.py_to_yaml \
    legacy_str.py legacy_sim.py output.yaml
```

### YAML to a `--str-conf` / `--sim-conf` `.py` Pair

```bash
python -m pymnpbem_simulation.migration.yaml_to_str_sim \
    input.yaml out_str.py out_sim.py
```

This tool can split existing jk-config YAML files back into `.py` files for
use with the new CLI pattern.

## 5. Execution Examples

### Recommended v1.5.2 Setting (Four-GPU VRAM Share)

The `compute` block in `auag_dimer_sim.py`:

```python
'compute': {
    'n_workers': 1,
    'n_threads': 4,
    'n_gpus_per_worker': 4,
    'vram_share_backend': 'cusolvermg',
    'iterative': True}
```

Or override from the CLI:

```bash
python run_simulation.py \
    --str-conf examples/auag_dimer_str.py \
    --sim-conf examples/auag_dimer_sim.py \
    --n-workers 1 --n-threads 4 \
    --n-gpus-per-worker 4 \
    --vram-share-backend cusolvermg \
    --verbose
```

### Multi-Node SLURM

```bash
srun python run_simulation.py \
    --str-conf my_str.py --sim-conf my_sim.py \
    --multi-node --auto
```

### Quick Debugging (Three Wavelengths Only)

```bash
python run_simulation.py \
    --str-conf examples/sphere_str.py \
    --sim-conf examples/sphere_sim.py \
    --n-wavelengths 3 --simulation-name sphere_smoke
```

## 6. Key Mapping Summary

The mapping from flat keys in the `.py` config files to sections in the
internal config dictionary is defined in
`pymnpbem_simulation.migration.py_to_yaml._KEY_TO_SECTION`.

Important mappings:

| `.py` Flat Key | Internal Config Section |
|---|---|
| `structure` | `structure.type` |
| `core_size`, `gap`, ... | `structure.<...>` |
| `materials` | `materials.particle_list` |
| `medium` | `materials.medium` |
| `simulation_type` | `simulation.type` |
| `excitation_type` | `simulation.excitation` |
| `wavelength_range` | `simulation.wavelength_range` |
| `polarizations` | `simulation.polarizations` |
| `num_workers` | `compute.n_workers` |
| `output_dir` | `output.dir` |
| `simulation_name` | `output.name` |

Nested dictionaries such as `compute = {...}` and `output = {...}` may also
be written directly inside `sim_conf.py`. These nested values take priority.
Both the flat format from `mnpbem_simulation` and the newer nested format are
supported.
