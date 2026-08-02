# Experiment <-> Simulation Analysis - Handoff / Onboarding

This handoff document is designed so that a new session for the experimental
data analysis project can understand, on the first day and from this document
alone, (1) where the existing simulation results are stored, (2) the
`pymnpbem` and `pymnpbem_simulation` projects, and (3) the post-analysis
workflow, including phase-difference analysis.

Detailed supporting information is stored in the auto-memory files referenced
by each section in Section 8.

---

## 0. TL;DR

- **Simulation results**: `~/research/pymnpbem/<family>/<case>/`
  - Each case contains `spectrum.npz`, a `sigma/` surface-charge and
    surface-current cache, and `config.yaml`.
- **Tools**:
  - `pymnpbem`, located at `~/workspace/MNPBEM`, is the GPU BEM core.
  - `pymnpbem_simulation`, located at
    `~/workspace/pymnpbem_simulation`, is the wrapper.
- **Analysis command**:
  `python run_postprocess.py --anal-conf A.py --result <case>/spectrum.npz`
  - `master.py` can run simulation and analysis in one command.
- **Experimental data**:
  `~/scratch/paper_figure_collection/raw/`
  - Contains digitized scattering-spectrum CSV files.
- **Environment**:
  `~/miniconda3/envs/mnpbem/bin/python`
  - Includes MNPBEM and CuPy.

---

## 1. Simulation Result Locations (`~/research/pymnpbem/`)

| Family | Structure | Completed Cases | Size |
|---|---|---:|---:|
| `au_dimer/` | Au dimer, without substrate and with substrate/ITO | 24 | 24 GB |
| `auag_dimer_4nm/` | Au@Ag dimer with a **4 nm Ag shell**, including r0.2/r0.3, gap variation, and 15/30/45 degree rotations | 36 | 53 GB |
| `auagcl_dimer_4nm/` | Au@AgCl dimer with a constant-permittivity shell | 4 | 2.1 GB |
| `monomer/au_r0.2` | Single Au cube | 1 | 0.4 GB |
| `auagagcl_dimer/`, `auagago_dimer/` | Au@Ag@AgCl / Au@Ag@AgO triple-shell structures | **0, incomplete** | - |
| Incomplete: `auag_dimer_1nm` | Au@Ag with a **1 nm shell** | 0, configs only | - |

**Contents of one case directory**, for example
`au_dimer/nosub/au_r0.2_g0.6/`:

- `spectrum.npz`
  - Keys: `wavelength` in nm, `ext`, `sca`, and `abs`.
  - Shape: `(n_wl, n_pol)`.
  - Averaging over the polarization axis gives the unpolarized result.
- `sigma/`
  - Contains wavelength- and polarization-specific files named
    `wl_{nm:07.2f}_p{pol}_d{dir}.npz`, together with `manifest.json`.
  - Stores the **complete BEM solution**:
    - `sig1`, `sig2`: surface charge
    - `h1`, `h2`: surface current
  - Used for recalculation in Section 4.
- `config.yaml`
  - Resolved config actually used for the run.
  - This is the reproducibility reference.
- Additional files may include:
  - `run_metadata.json`
  - `postprocess/`
  - `structure.png`
  - `field.npz`
  - `spectra_eV`

**Loading the spectrum**:

```python
data = np.load(case + '/spectrum.npz')
```

**Loading sigma data**:

```python
from pymnpbem_simulation.sigma_cache import load_sigma

sigma = load_sigma(case, wl_nm, pols, props)
```

**Digitized experimental data** is stored in
`~/scratch/paper_figure_collection/raw/`:

- `digitized_energy_curve.csv`
  - Au monomer
  - Columns: `Energy_eV`, `Intensity_norm`
  - Range: 1.45 to 2.60 eV
- `black_curve_redigitized.csv`
  - Au dimer with substrate, r0.2 and g0.6
  - Columns: `Energy_eV`, `Scattering`
  - Range: 1.39 to 2.66 eV

Both datasets are scattering spectra and should be peak-normalized before
comparison.

---

## 2. `pymnpbem` - Python MNPBEM Port (`~/workspace/MNPBEM`)

- A **boundary element method nanophotonics solver** ported from MATLAB
  MNPBEM to Python with GPU support.
- Solves Maxwell's equations on particle boundaries to obtain surface charge
  `sigma`, then calculates:
  - extinction cross section
  - scattering cross section
  - absorption cross section
  - near fields
- Supports:
  - quasistatic (`stat`)
  - retarded (`ret`)
  - vacuum
  - substrate systems using layered Green functions and Sommerfeld integration
- Provides GPU acceleration through CuPy and supports both:
  - fp32 / complex64
  - fp64 / complex128
- Large meshes can use multi-GPU VRAM sharing.

**Performance warning**:

The distributed VRAM-share initialization path can accidentally retain
complex128 internal matrices even when the config requests fp32. Because an
A6000 has relatively weak fp64 performance, LU can become approximately
13 times slower. The distributed `bem_ret_layer` path therefore needs an
explicit complex64 cast when `LOWPREC` is enabled.

---

## 3. `pymnpbem_simulation` - Wrapper (`~/workspace/pymnpbem_simulation`)

A config-driven end-to-end pipeline. For details, see
[README.md](../README.md) and [README.en.md](../README.en.md).

- **Simulation**:

  ```bash
  python run_simulation.py --str-conf S.py --sim-conf M.py
  ```

  Other supported modes:

  ```bash
  python run_simulation.py --config x.yaml
  python run_simulation.py --sweep-conf sweep.yaml
  ```

  The simulation saves `spectrum.npz` and the sigma cache.
  `simulation.save_sigma_cache` is enabled by default.

- **Analysis**:

  ```bash
  python run_postprocess.py \
      --anal-conf A.py \
      --result <case>/spectrum.npz
  ```

  See Section 4.

- **Simulation and analysis in one command**:

  ```bash
  python master.py \
      --str-conf S.py \
      --sim-conf M.py \
      --anal-conf A.py
  ```

- Includes more than 12 structure builders:
  - sphere
  - dimer
  - core-shell
  - custom shell
  - monomer
  - `advanced_dimer_cube`
  - others

- Implemented excitation and solver combinations in the registry:
  - plane wave
  - dipole
  - EELS
  - quasistatic
  - retarded
  - substrate/layer variants

- Polarization is defined by:
  - electric-field vectors in `polarizations`
  - propagation directions in `propagation_dirs`

- For substrate calculations, the core automatically decomposes into
  s/p or TE/TM components.
  - At normal incidence, the two are degenerate.

- Cluster and scheduler support:
  - `slurm_scripts/`
  - `pbs_scripts/`
  - `auto_detect.py`

- YAML and Python config conversion:
  - `migration/`

---

## 4. Post-Analysis

Run post-analysis with:

```bash
python run_postprocess.py --analyzers ...
```

Analyzer hyperparameters can be stored in an `--anal-conf A.py` file.
See `examples/fano_anal.py`.

Available analyzers:

- `spectrum`
  - plots `ext`, `sca`, and `abs`
  - exports CSV, JSON, and NPZ
  - supports eV and nm axes
- `fano`
  - single- or multi-Lorentzian Fano fitting
- `fano-analysis`
  - bright/dark eigenmode analysis
  - multi-Lorentzian analysis
  - based on the full quasistatic eigensystem
- `eigenmode`
  - eigenmode-pattern analysis
- `multipole`
  - multipole decomposition

Relevant modules:

```text
postprocess/
├── spectrum.py
├── fano_fit.py
├── fano_analysis.py
├── mode_phase.py
├── plot_mode_phase.py
├── mode_compare.py
├── eigenmode.py
├── multipole.py
├── plot_surface_charge.py
└── field_analyzer.py
```

### Recalculating Observables from the Sigma Cache Without Re-Solving BEM

Reference script:

```text
~/scratch/spectrum_from_cache.py
```

The `sigma/*.npz` files store the complete BEM solution:

- `sig1`
- `sig2`
- `h1`
- `h2`

Reconstruct the solution as:

```python
sig = CompStruct(
    p,
    wl,
    sig1=sig1,
    sig2=sig2,
    h1=h1,
    h2=h2,
)
```

Then use:

- Free space:

  ```python
  exc = PlaneWaveRet(pol, prop)
  ```

- Substrate:

  ```python
  exc = PlaneWaveRetLayer(pol, prop, layer)
  ```

Recalculate observables with:

```python
extinction = exc.extinction(sig)
scattering = exc.scattering(sig)
```

Validation errors:

- Free space: `7.9e-5`
- Layered substrate: `7.7e-10`

This workflow is useful for recovering spectra from partial or field-only
runs. A Green-function tabulation is not required.

The same sigma cache can also replay near fields through the field-only path
of `FieldCalculator`.

---

## 5. Phase-Difference Analysis for Fano Modes

Auto-memory reference: `project_fano_phase_analysis`

Target case:

```text
au_dimer/sub/au_r0.2_g0.6_sub
```

Target features:

- 1.43 eV
- 1.8 eV

### Convention-Invariant Modal Dipole

Use the convention-invariant modal dipole:

```text
f_m = a_m * d_m
```

where:

- `a_m` is the modal amplitude:

  ```text
  a_m = u_L * sigma
  ```

- `d_m` is the modal dipole:

  ```text
  d_m = sum_f u_R[f] * x_f * A_f
  ```

The phase of an individual eigenvector is arbitrary. The phase factors of
`u_L` and `u_R` cancel in the product, making `f_m` independent of eigenvector
phase convention.

The total longitudinal dipole is:

```text
sum_m f_m
```

### Full Quasistatic Basis

The exact full-basis procedure is:

```python
F = CompGreenStat(p, p).F
```

followed by:

```python
scipy.linalg.eig(...)
```

Caches:

```text
~/scratch/_qs_full_eig.npz
~/scratch/_dipole_spec.npz
```

### Critical Pitfall

A fixed eigenbasis calculated at a reference wavelength of approximately
868 nm, or 1.43 eV, is valid only near that wavelength.

Reconstructing the 1.8 eV surface charge using that basis gives:

```text
R^2 = 0.008
```

This means the reconstructed state is nearly orthogonal to the actual state.
Do not perform modal phase analysis far from the reference wavelength using a
fixed eigenbasis.

This mistake previously produced an incorrect phase difference.

### Results

- Both the 1.43 eV and 1.8 eV features are **shallow Fano resonances**.
- Narrow-to-broad amplitude ratio:

  ```text
  approximately 0.3
  ```

- The response does not reach a complete zero.
- Phase difference between the narrow mode and background:

  ```text
  Delta phi approximately pi/2
  ```

  This indicates asymmetry-dominated behavior.

- At the dip minimum:

  ```text
  Delta phi = 0.6 to 0.71 pi
  ```

  This remains below the ideal value of `pi`.

- The basis-independent total dipole phase, `arg(D(omega))`, advances by
  approximately `pi/2` between the two dips.

Reference scripts in `~/scratch/`:

```text
rigorous_phase_qs.py
analyze_dipole.py
fano_fit_global.py
fano_sweep.py
render_true_dips.py
```

---

## 6. Experimental vs Simulation Comparison

Auto-memory reference: `project_exp_sim_validation`

### Monomer Validation

- Experimental peak: 2.182 eV
- Simulated peak: 2.166 eV
- Difference: 16 meV
- Correlation:

  ```text
  r = 0.957
  ```

Conclusion: the methodology and monomer model are valid.

### Dimer with Substrate, g0.6

- The lineshape is reproduced accurately.
- The simulation shows a systematic redshift of 114 to 123 meV.
- Correlation without an energy shift:

  ```text
  r = 0.43
  ```

- Correlation after applying a rigid +114 meV shift:

  ```text
  r = 0.97
  ```

### Likely Cause

All current substrate simulations use an effectively touching geometry:

```text
particle-substrate gap = 0.001 nm
```

This likely overestimates substrate coupling and produces excessive redshift.

The real particle may sit slightly above the substrate, or the effective
substrate permittivity may be lower than 3.88 for ITO.

A substrate-distance sweep is needed for a more physical reproduction.

### Pitfalls

- The apparent peak match for `r0.3 g0.8 sub` corresponds to the upper branch
  of a Fano doublet and is therefore a false match.
- A best-fit geometric gap of `g3.0` is also a degenerate solution and should
  not be interpreted as unique.

Comparison figures:

```text
paper_figure_collection/compare_*.png
```

---

## 7. Paper Figures

Location:

```text
~/scratch/paper_figures/
├── fig1/
├── fig2/
├── fig3/
└── FIGURES_README.md
```

- `fig1`: concept
- `fig2`: validation and performance
- `fig3`: Au dimer examples
  - without substrate
  - with substrate
  - monomer

To avoid storing or reloading heavy sigma data, Figure 3 can be regenerated
from:

```text
plotdata.npz
```

See auto-memory reference `reference_paper_figures` for details.

---

## 8. Related Auto-Memory Files

These are loaded automatically at the beginning of a session within the same
project scope and provide the detailed supporting information.

- `project_exp_sim_validation`
  - experimental vs simulation comparison
  - monomer correlation `r = 0.957`
  - dimer with substrate redshift of approximately 120 meV
- `project_fano_phase_analysis`
  - convention-invariant `f_m` phase-analysis method
  - pitfalls
  - results
- `project_sigma_cache_recompute`
  - recalculating observables and fields from the sigma cache
- `reference_paper_figures`
  - figure scripts
  - data
  - formatting
- `project_auag_dimer_ops`
  - campaign operating parameters and paths
- `project_auag_rotated_campaign`
  - rotated-campaign operating parameters and paths
- `project_auagcl_sim`
  - Au@AgCl simulation operating parameters and paths
- `project_au_dimer_sim_plan`
  - Au dimer simulation planning and operating parameters

---

## 9. How to Use This Document in a New Session

1. At the beginning of a new session, provide this document path:

   ```text
   ~/workspace/pymnpbem_simulation/docs/EXPERIMENT_ANALYSIS_HANDOFF.md
   ```

2. Auto-memory is loaded automatically within the same project scope.
   Mentioning an experimental comparison with Au or Au@Ag dimers should cause
   the Section 8 memories to be referenced.

3. Recommended analysis starting point:

   - Confirm the experimental wavelength range and polarization.
   - Load the corresponding simulation case from `spectrum.npz`.
   - Convert to eV.
   - Peak-normalize the spectra.
   - For a dimer with substrate, account for the approximately
     0.11 to 0.12 eV offset described in Section 6.
