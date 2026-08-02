# Migrating `.py` Configs to YAML

This tool automatically converts the two legacy `.py` config files from
`mnpbem_simulation`, `config_str_*.py` and `config_sim_*.py`, into a single
YAML file.

## Usage

```bash
python -m pymnpbem_simulation.migration.py_to_yaml \
    /path/to/config_str_*.py \
    /path/to/config_sim_*.py \
    output.yaml
```

To convert only a `structure` or `simulation` config:

```bash
python -m pymnpbem_simulation.migration.py_to_yaml \
    "" \
    /path/to/config_sim_*.py \
    output.yaml
```

## Key Mapping Table

| Legacy `.py` Key | YAML Section | YAML Key |
|---|---|---|
| `structure` | `structure` | `type` |
| `structure_name`, `simulation_name` | `output` | `name` |
| `simulation_type` | `simulation` | `type` |
| `excitation_type` | `simulation` | `excitation` |
| `wavelength_range` | `simulation` | `wavelength_range`, with automatic expansion into `enei_min`, `enei_max`, and `n_wavelengths` |
| `polarizations` | `simulation` | `polarizations` |
| `propagation_dirs` | `simulation` | `propagation_dirs` |
| `dipole_position` / `dipole_moment` | `simulation` | same key |
| `impact_parameter` / `beam_energy` / `beam_width` | `simulation` | same key |
| `interp` | `simulation` | `interp` |
| `refine` | `structure` | `refine` |
| `relcutoff` | `simulation` | `relcutoff` |
| `waitbar` | `simulation` | `waitbar` |
| `use_parallel` | `compute` | `use_parallel` |
| `num_workers` | `compute` | `n_workers`; `'auto'` becomes `-1`, while `'env'` is preserved |
| `max_comp_threads` | `compute` | `n_threads`; `'auto'` and `'max'` become `-1` |
| `wavelength_chunk_size` | `compute` | `wavelength_chunk_size` |
| `use_mirror_symmetry` | `compute` | `mirror` |
| `use_iterative_solver` | `compute` | `iterative` |
| `use_nonlocality` | `compute` | `nonlocal` |
| `use_h2_compression` | `compute` | `hmode`; `bool` becomes `'aca-gpu'` or `'dense'` |
| `medium` | `materials` | `medium` |
| `materials` as a list | `materials` | `particle_list` |
| `substrate` / `use_substrate` | `materials` | same key |
| `refractive_index_paths` | `materials` | same key |
| `diameter` / `size` / `gap` / `rounding` / `roundings` | `structure` | same key |
| `mesh_density` | `structure` | `mesh_density` |
| `core_size` / `shell_layers` | `structure` | same key |
| `offset` / `tilt_angle` / `tilt_axis` / `rotation_angle` | `structure` | same key |
| `n_spheres` / `shape_file` / `voxel_size` / `voxel_method` | `structure` | same key |
| `output_dir` | `output` | `dir` |
| `output_formats` | `output` | `formats` |
| `save_plots` / `plot_format` / `plot_dpi` | `output` | same key |
| `spectrum_xaxis` | `postprocess` | `spectrum_xaxis` |
| `calculate_cross_sections` / `calculate_fields` | `simulation` | same key |
| `field_region` / `field_mindist` / `field_nmax` / `field_wavelength_idx` | `simulation` | same key |
| `export_field_arrays` / `field_hotspot_count` / `field_hotspot_min_distance` | `simulation` | same key |
| `run_eigenmode_analysis` | `postprocess` | `run_eigenmode_analysis` |
| `eigenmode_n` / `eigenmode_top_k` | `postprocess` | same key |
| `retarded_eigen_wavelength` | `postprocess` | same key |
| `fano_target_wavelengths` / `svd_rank_threshold` | `postprocess` | same key |

## Dropped Keys

The following MATLAB-specific options are not used by the Python wrapper and
are removed during conversion:

- `mnpbem_path`
- `matlab_executable`
- `matlab_options`

## Unmapped Keys

Keys that do not appear in the table above are preserved under the YAML
`extras:` section. This retains information so users can review it after
reconstruction.

## Conversion Example

Legacy `config_str_au_r0.2_g0.6.py`:

```python
args = {}
args['structure'] = 'advanced_dimer_cube'
args['core_size'] = 47
args['shell_layers'] = []
args['roundings'] = [0.2]
args['mesh_density'] = 2
args['gap'] = 0.6
args['materials'] = ['gold']
args['medium'] = 'water'
args['refractive_index_paths'] = {'agcl': {'type': 'constant', 'epsilon': 2.02}}
args['use_substrate'] = False
```

Legacy `config_sim_au_r0.2_g0.6.py`:

```python
import os

args = {}
args['use_parallel'] = True
args['num_workers'] = 4
args['max_comp_threads'] = 1
args['wavelength_chunk_size'] = 10
args['simulation_name'] = 'au_r0.2_g0.6'
args['simulation_type'] = 'ret'
args['interp'] = 'curv'
args['excitation_type'] = 'planewave'
args['polarizations'] = [[1, 0, 0], [0, 1, 0]]
args['propagation_dirs'] = [[0, 0, 1], [0, 0, 1]]
args['wavelength_range'] = [500, 1000, 100]
args['refine'] = 3
args['use_mirror_symmetry'] = False
args['use_iterative_solver'] = True
args['use_nonlocality'] = False
args['output_dir'] = os.path.join(os.path.expanduser('~'), 'research', 'mnpbem', 'dimer')
args['output_formats'] = ['txt', 'csv', 'json']
args['save_plots'] = True
args['run_eigenmode_analysis'] = True
```

Converted YAML:

```yaml
output:
  name: au_r0.2_g0.6
  dir: ~/research/mnpbem/dimer
  formats: [txt, csv, json]
  save_plots: true
structure:
  type: advanced_dimer_cube
  core_size: 47
  shell_layers: []
  roundings: [0.2]
  mesh_density: 2
  gap: 0.6
  refine: 3
materials:
  particle_list: [gold]
  medium: water
  refractive_index_paths:
    agcl: {type: constant, epsilon: 2.02}
  use_substrate: false
compute:
  use_parallel: true
  n_workers: 4
  n_threads: 1
  wavelength_chunk_size: 10
  mirror: false
  iterative: true
  nonlocal: false
simulation:
  type: ret
  interp: curv
  excitation: planewave
  polarizations: [[1, 0, 0], [0, 1, 0]]
  propagation_dirs: [[0, 0, 1], [0, 0, 1]]
  wavelength_range: [500, 1000, 100]
  enei_min: 500
  enei_max: 1000
  n_wavelengths: 100
postprocess:
  run_eigenmode_analysis: true
```

## Follow-Up Steps for Manual Review

After automatic conversion, users should review the following items:

1. **`compute.n_gpus_per_worker`**: Automatic conversion sets this value to
   `0`, meaning CPU execution. Set it explicitly when using GPUs.
2. **`structure.type`**: Wave 1 supports only `dimer_cube` and `sphere`.
   Additional types such as `advanced_dimer_cube` are added in Wave 2 (M4).
3. **`materials.particle`**: Wave 1 handles only a single particle.
   Multi-shell structures using `shell_layers` are supported in Wave 2.
4. **`output.formats`**: Adding `npz` is recommended for Python-native output.

## Conflicts

- Both `structure_name` and `simulation_name` map to `output.name`.
  The migration code updates `args_str` first and then `args_sim` inside
  `merge_args()`, so the simulation value takes precedence.

- Legacy `args['materials']` is a list, while YAML may use a single
  `materials.medium` or `materials.particle` value.
  The list is preserved as `materials.particle_list` and is intended for
  multi-particle handling in Wave 2.
