# Feature Parity Audit: mnpbem_simulation (MATLAB) vs pymnpbem_simulation

This document compares the feature coverage of the MATLAB-based
`mnpbem_simulation` wrapper and the pure-Python `pymnpbem_simulation` port.

Status:

- `OK`: An equivalent or better implementation exists in pymnpbem
- `partial`: Only part of the functionality exists and additional work is needed
- `TODO`: Missing and considered a candidate for implementation
- `skip`: MATLAB-only dependency that cannot be ported, or intentionally omitted

Priority:

- `H` (high): Directly affects Au dimer, Au@Ag dimer, aggregate sphere, and rod simulations
- `M` (medium): Frequently used in general plasmonic simulations
- `L` (low): Specialized or MATLAB-specific

## 1. Postprocess - Visualization

| Feature | mnpbem (MATLAB wrapper) | pymnpbem | Status | Priority |
|---|---|---|---|---|
| Spectrum plot per polarization | `visualizer.py:plot_spectrum` | `postprocess/plot.py:plot_spectrum` | OK (Series A) | H |
| Spectrum x-axis energy (eV) toggle | `plot_spectrum` (`xaxis_unit`) | `plot.py:plot_spectrum(xaxis='energy')` | OK (Series A) | H |
| Polarization comparison with ext/sca/abs in three plots | `plot_polarization_comparison` | `plot.py:plot_polarization_comparison` | OK (Series A) | H |
| Unpolarized spectrum using FDTD-style two-polarization averaging | `plot_unpolarized_spectrum` + `SpectrumAnalyzer.calculate` | `spectrum.py:check_unpolarized_conditions` + `calculate_unpolarized_spectrum` | OK (Series A) | H |
| Comparison plot, polarized vs unpolarized | `_plot_spectrum_comparison_with_unpolarized` | `plot.py:plot_polarization_vs_unpolarized` | OK (Series A) | H |
| All-in-one comparison with three subplots | `comparison_all_unpolarized` | `plot_polarization_vs_unpolarized` as the fourth output file | OK (Series A) | M |
| Field plots, enhancement and 2D slice | `plot_fields`, `_plot_field_enhancement` | `plot_field.py:plot_field_2d_slice` | OK | H |
| Field intensity plots with LogNorm and percentile scaling | `_plot_field_intensity` | `plot_field.py:plot_field_intensity_2d` | OK (Series D) | M |
| Field vector plots with 2D quiver | `_plot_field_vectors` | `plot_field.py:plot_field_vectors_2d` | OK (Series D) | M |
| Separate internal and external field plots | `plot_field_separate_internal_external` | Missing | TODO | M |
| Field comparison with all polarizations overlaid | `_plot_field_comparison` | Missing | TODO | M |
| Field overlay with all polarizations on one plot | `_plot_field_overlay` | Missing | TODO | L |
| Unpolarized fields | `plot_unpolarized_fields` | Missing | TODO | M |
| Material boundary on field plots | `_draw_material_boundary` | Missing | TODO | M |
| Surface-charge 3D plot | `_plot_surface_charge_3d` | `plot_surface_charge.py:plot_surface_charge_3d` | OK | - |
| Surface-charge 2D eight-view plot | `_plot_surface_charge_2d_8views` | `plot_surface_charge_2d_8views` | OK | - |
| Surface-charge phase analysis, Re/Im/abs/arg | `plot_surface_charge_phase_analysis` | `plot_surface_charge_phase` | OK | - |
| Hotspots in 3D | Missing, available separately in pyMNPBEM | `plot_hotspots_3d` | OK | - |
| Near-field decay | Missing | `plot_near_field_decay` | OK | - |
| Eigenmode plots as a mode-pattern grid | `_plot_mode_patterns_grid` | `plot_eigenmode.py:plot_mode_patterns` | OK (Series F) | M |
| Eigenvalue spectrum with complex-plane and bar plots | Missing, implemented directly | `plot_eigenmode.py:plot_eigenvalue_spectrum` | OK (Series F) | M |
| Eigenmode magnitude spectra vs wavelength | `_plot_magnitude_spectra` | Missing because wavelength-sweep data are not saved | TODO | L |
| Eigenmode phase spectra vs wavelength | `_plot_phase_spectra` | Missing for the same reason | TODO | L |
| Eigenmode delta-phi comparison | `_plot_delta_phi_comparison` | Missing | TODO | L |
| SVD decay plot | Missing | `plot_eigenmode.py:plot_singular_value_decay` | OK (Series F) | M |
| Multipole bar chart, power per l | Indirect only | `plot.py:plot_multipole_bar` | OK (Series D) | M |
| Multipole character table | `_plot_multipole_character_table` | Missing because character classification has not been ported | TODO | L |
| Fano-fit plot with data, fit, residual, and annotations | `_plot_fano_fit` | `plot.py:plot_fano_fit` | OK (Series D) | M |
| Cross-validation summary | `_plot_cross_validation_summary` | Missing | TODO | L |

## 2. Postprocess - Analysis

| Feature | mnpbem | pymnpbem | Status | Priority |
|---|---|---|---|---|
| Peak finder using `scipy.signal.find_peaks` | `SpectrumAnalyzer._find_peaks` | `spectrum.py:find_spectrum_peaks`, per-polarization multi-peak list | OK (Series A) | H |
| FWHM calculation | `_calculate_fwhm` | `spectrum.py:_compute_fwhm` | OK | - |
| Multi-peak detection | `_find_peaks` using prominence | `spectrum.py:find_spectrum_peaks`, sorted by amplitude and prominence | OK (Series A) | M |
| Enhancement factors as pol1/pol2 ratios | `_calculate_enhancement` | `spectrum.py:compute_enhancement_factors`, all pairs | OK (Series A) | M |
| Average and maximum cross sections | `analyze` with `avg_*`, `max_*` | `analyze_spectrum` with `avg_*`, `max_*` | OK (Series A) | M |
| Unpolarized check for orthogonal polarizations | `_check_unpolarized_conditions` | `spectrum.py:check_unpolarized_conditions` | OK (Series A) | H |
| Unpolarized-spectrum calculation | `_calculate_unpolarized_spectrum` | `spectrum.py:calculate_unpolarized_spectrum` | OK (Series A) | H |
| Hotspot finder | `FieldAnalyzer._find_hotspots` | `field_analyzer.py:hotspot_location` | OK | H |
| High-field region analysis with point count, area, and volume by threshold | `_analyze_high_field_regions` | `field_analyzer.py:high_field_regions` | OK (Series C) | M |
| Near-field integration | `calculate_near_field_integration` | Missing because the BEM-aware implementation is complex and was not ported | TODO | L |
| Near-field decay | Missing | `field_analyzer.py:near_field_decay` | OK | - |
| Field statistics, including max, mean, median, and percentiles | `_calculate_statistics` | `field_analyzer.py:field_statistics` | OK (Series C) | M |
| Edge-artifact detection | `edge_filter.py:find_edge_artifacts` | Missing because it depends on near-field integration | TODO | L |
| Geometry cross section | `geometry_cross_section.py:GeometryCrossSection` | Missing because it depends on near-field integration | TODO | L |
| QS eigenmode analysis | `QSEigenAnalyzer` in `eigenmode_analyzer.py` | `postprocess/eigenmode.py:qs_eigenmodes` | OK | - |
| SVD decomposition | `SVDAnalyzer` | `eigenmode.py:svd_decomposition` | OK | - |
| Multipole projection | `MultipoleAnalyzer` | `postprocess/multipole.py` | OK | - |
| Retarded eigenmode | `RetardedEigenAnalyzer` | `eigenmode.py:retarded_eigenmodes` | OK | - |
| Mode comparator for cross-validation | `ModeComparator` | Missing | TODO | L |
| Fano fit | `FanoFitter` | `fano_fit.py:fano_fit` | OK | - |
| Multi-peak Fano fit | Missing | `multi_fano_fit` | OK | - |
| Core-shell separator | `CoreShellSeparator` | `postprocess/core_shell.py:CoreShellSeparator` | OK (Series B) | H (Au@Ag) |

## 3. Simulation Runners

| Feature | mnpbem | pymnpbem | Status | Priority |
|---|---|---|---|---|
| Plane wave + retarded | MATLAB template | `planewave_ret.py` | OK | - |
| Plane wave + quasistatic | MATLAB | `planewave_stat.py` | OK | - |
| Plane wave + retarded + layer substrate | MATLAB | `planewave_ret_layer.py` | OK | - |
| Plane wave + retarded + iterative | MATLAB | `planewave_ret_iter.py` | OK | - |
| Plane wave + quasistatic + iterative | MATLAB | `planewave_stat_iter.py` | OK | - |
| Plane wave + retarded + layer + iterative | MATLAB | `planewave_ret_layer_iter.py` | OK | - |
| Plane wave + retarded + mirror | MATLAB | `planewave_ret_mirror.py` | OK | - |
| Plane wave + quasistatic + layer | MATLAB | Missing | TODO | L |
| Dipole + retarded | MATLAB | `dipole_ret.py` | OK | - |
| Dipole + quasistatic | MATLAB | `dipole_stat.py` | OK | - |
| Dipole + retarded + layer | MATLAB | `dipole_ret_layer.py` | OK | - |
| Dipole + retarded + iterative | MATLAB | Missing | TODO | L |
| Dipole + quasistatic + iterative | MATLAB | Missing | TODO | L |
| EELS + retarded | MATLAB | `eels_ret.py` | OK | - |
| EELS + quasistatic | MATLAB | `eels_stat.py` | OK | - |
| EELS + retarded + layer | MATLAB | `eels_ret_layer.py` | OK | - |
| Nonlocal permittivity | MATLAB | `with_nonlocal` wrapper | partial | M |
| Field-calculation grid | MATLAB | `field_calculator.py` + `grid_builder.py` | OK | - |
| Scattered field on grid (`emesh(sig)`) | MATLAB `@meshfield` | `field_calculator.py` (default) | OK | - |
| Total field on grid (`emesh(sig) + emesh(exc.field(pt))`) | MATLAB demos, `help/bem_ug_efield.m` | `simulation.field_total = true` | OK since 2026-08-12 | - |
| `exc.field()` at ComPoint positions | MATLAB (compoint `inout` is n x 1) | `planewave_ret.py` | fixed 2026-08-12 (was IndexError) | - |

## 4. Structures (Geometry Builders)

| Feature | mnpbem | pymnpbem | Status | Priority |
|---|---|---|---|---|
| Sphere | MATLAB `trisphere` | `sphere.py` | OK | - |
| Cube | MATLAB `tricube` | `cube.py` | OK | - |
| Rod | MATLAB `trirod` | `rod.py` | OK | - |
| Ellipsoid | MATLAB `triellipsoid` | `ellipsoid.py` | OK | - |
| Triangle | MATLAB `tritriangle` | `triangle.py` | OK | - |
| Dimer, sphere/cube | MATLAB | `dimer_sphere.py` + `dimer_cube.py` | OK | - |
| Core-shell sphere | MATLAB | `core_shell_sphere.py` | OK | - |
| Core-shell cube | MATLAB | `core_shell_cube.py` | OK | - |
| Core-shell rod | MATLAB | `core_shell_rod.py` | OK | - |
| Core-shell cube dimer, Au@Ag dimer | MATLAB | `dimer_core_shell_cube.py` | OK | - |
| Advanced monomer cube | MATLAB | `advanced_monomer_cube.py` | OK | - |
| Advanced dimer cube | MATLAB | `advanced_dimer_cube.py` | OK | - |
| Connected dimer cube | MATLAB | `connected_dimer_cube.py` | OK | - |
| Sphere cluster, aggregate | MATLAB | `sphere_cluster.py` | OK | - |
| Import from shape, `.mat` / `.stl` | MATLAB geometry generator | `from_shape.py` | OK | - |
| With substrate | MATLAB | `with_substrate.py` | OK | - |
| With mirror symmetry | MATLAB | `with_mirror.py` | OK | - |
| With nonlocal correction | MATLAB | `with_nonlocal.py` | OK | - |
| Cylindrical rod as a separate builder | MATLAB | Cylinder shape supported in `rod.py` | OK | - |

## 5. Materials

| Feature | mnpbem | pymnpbem | Status | Priority |
|---|---|---|---|---|
| Drude / Lorentz / `EpsConst` | MATLAB | Direct call to mnpbem core | OK | - |
| Table-based permittivity, including Johnson & Christy | `RefractiveIndexLoader` | Direct call to mnpbem core | OK | - |
| AgCl and dielectric coatings | MATLAB | mnpbem core | OK | - |
| Nonlocal hydrodynamic Drude | `NonlocalGenerator` | `nonlocal_eps.py:make_hydrodynamic_drude_eps` | OK | - |
| Automatic material classification, metal/dielectric | `material_manager:_is_metal` | Missing | TODO | L |

## 6. CLI / Dispatch / Orchestration

| Feature | mnpbem | pymnpbem | Status | Priority |
|---|---|---|---|---|
| Single-node dispatch | MATLAB | `dispatch/single_node.py` | OK | - |
| Multiple GPUs per worker | MATLAB | `dispatch/multi_gpu.py` | OK | - |
| Multi-node MPI | MATLAB | `dispatch/mpi_node.py` | OK | - |
| Sweep launcher with four workers pinned per GPU | Missing | Sweep launcher | OK | - |
| `--reanalyze`, postprocess only | `run_postprocess.py` | `cli.py --reanalyze` | OK | - |
| `--auto` compute plan | MATLAB | `cli.py --auto` | OK | - |
| `--verbose` | MATLAB | `cli.py --verbose` | OK | - |
| `--n-wavelengths` subsampling | Missing | `cli.py` | OK | - |
| SLURM scripts | MATLAB | `slurm_scripts/` | OK | - |
| PBS scripts | MATLAB | `pbs_scripts/` | OK | - |
| Config snapshot saving | MATLAB | `cli.py:save_yaml` | OK | - |
| Run metadata saving | MATLAB | `save_run_metadata` | OK | - |
| Python-config to YAML migration | MATLAB `.py` format | `migration/py_to_yaml.py` | OK | - |

## 7. Output Formats

| Feature | mnpbem | pymnpbem | Status | Priority |
|---|---|---|---|---|
| `.npz` spectrum | Missing | `io/writer.py` | OK | - |
| `.json` spectrum analysis | `data_exporter` JSON | postprocess JSON | OK | - |
| `.csv` spectrum | `data_exporter` CSV | `postprocess/export.py` | OK | - |
| `.txt` spectrum with header, per-polarization, and combined output | `data_exporter._save_txt` | `export.py:export_spectrum_txt` | OK (Series C) | M |
| `.txt` field data per polarization/wavelength | `DataExporter._export_single_field` | Missing because there has been no user request | TODO | L |
| `.png` plot | MATLAB + visualizer | `plot.py` and related modules | OK | - |
| `.pdf` plot | visualizer with `plot_format=['png','pdf']` | `plot_spectrum` and related functions support `plot_format` | OK (Series A) | M |
| `.h5` export | Missing | `export.py:export_h5` | OK | - |
| `.mat` export | MATLAB native | Missing | skip | - |
| `.eps` / `.svg` | Visualizer option | Missing | TODO | L |

## 8. Postprocess-Specific Analyses Already Implemented

| Feature | mnpbem | pymnpbem | Status | Priority |
|---|---|---|---|---|
| QS eigenmodes using the boundary-integral method | `eigenmode_analyzer.QSEigenAnalyzer` | `postprocess.eigenmode` | OK | - |
| Retarded eigenmodes | `retarded_eigen.RetardedEigenAnalyzer` | `postprocess.eigenmode.retarded_eigenmodes` | OK | - |
| SVD rank determination | `SVDAnalyzer.determine_rank` | Missing in pymnpbem | TODO | L |
| Mode classification, dipole/quadrupole/etc. | `MultipoleAnalyzer.classify` | Missing | TODO | M |
| Mode comparator for cross-validation | `ModeComparator` | Missing | TODO | L |

---

# Priority Summary

## High Priority: Essential and Directly Relevant to User Cases, Series A/B/C

- **Series A, visualization**:
  - Spectrum energy-axis support
  - Polarization comparison
  - Unpolarized spectrum
  - Comparison plots
- **Series B, analysis**:
  - Multi-peak detection
  - Enhancement factors
  - Unpolarized-condition checks
- **Series C, Au@Ag**:
  - Core-shell separator with core/shell masks and cutaway plots

## Medium Priority: Frequently Used in General Plasmonic Simulations, Series D/E/F

- **Series D, visualization**:
  - Field intensity
  - Field comparison
  - Mode-pattern grids
  - Multipole character table
  - Fano-fit plot
- **Series E, output**:
  - Text spectrum and field exporters
  - PDF plots
- **Series F, analysis**:
  - High-field region analysis
  - Near-field integration
  - Geometry cross section
  - Fano-fit plot
  - Improvements to multi-peak detection

## Low Priority: Series G

- `planewave_stat_layer` runner
- Iterative dipole variants
- Mode comparator
- SVD rank determination
- Mode classification
- EPS / SVG plots

---

# Series Execution Plan

| Series | Target | Description | Files |
|---|---|---|---|
| A1 | `postprocess/plot.py` | Add `xaxis='energy'` support for spectra | `plot.py` |
| A2 | `postprocess/plot.py` | Add polarization-comparison plots | `plot.py` |
| A3 | `postprocess/spectrum.py` | Add unpolarized calculation and checks | `spectrum.py` + new module |
| A4 | `postprocess/plot.py` | Add unpolarized and comparison plots | `plot.py` |
| B1 | `postprocess/spectrum.py` | Add multi-peak detection using SciPy `find_peaks` | `spectrum.py` |
| B2 | `postprocess/spectrum.py` | Add enhancement factors, averages, and maxima | `spectrum.py` |
| C1 | `postprocess/core_shell.py` | Port `CoreShellSeparator` for cubes and rods | New module |
| D1 | `postprocess/plot_field.py` | Add missing field-intensity and comparison plots | `plot_field.py` |
| D2 | `postprocess/plot_eigenmode.py` | Add mode patterns, magnitude spectra, and phase spectra | New module |
| D3 | `postprocess/plot.py` | Add multipole-character bar charts and Fano-fit plots | `plot.py` |
| E1 | `postprocess/export.py` | Add text spectrum and field exporters | `export.py` |
| F1 | `postprocess/field_analyzer.py` | Add high-field region analysis | `field_analyzer.py` |
| F2 | `postprocess/geometry_cross_section.py` | Add geometry cross-section utilities | New module |
