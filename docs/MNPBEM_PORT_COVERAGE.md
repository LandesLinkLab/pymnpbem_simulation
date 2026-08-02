# MNPBEM Python Port - Feature Coverage Matrix

This document summarizes the implementation status of major MATLAB MNPBEM
features in the Python port located at `~/workspace/MNPBEM/mnpbem/`.

Survey date: 2026-05-02 (Phase 2 Wave 1 - Task 1)

Status criteria:

- ✅ Available: Fully implemented in the Python port with a clear signature
- ⚠️ Partial: Partially implemented and requires additional work
- ❌ Missing: Target for the M5 porting task

---

## 1. Mirror Symmetry - `comparticlemirror`

| Item | Location | Signature | Status |
|---|---|---|---|
| `ComParticleMirror` class | `mnpbem/geometry/comparticle_mirror.py:107` | `class ComParticleMirror(object)` | ✅ Available |
| `CompStructMirror` helper | `mnpbem/geometry/comparticle_mirror.py:9` | `class CompStructMirror(object)` | ✅ Available |
| BEM mirror solvers | `BEMStatMirror` / `BEMRetMirror` / `BEMLayerMirror` / `BEMStatEigMirror` | `mnpbem/bem/bem_*_mirror.py` | ✅ Available |
| Mirror excitations | `PlaneWaveStatMirror` / `PlaneWaveRetMirror` / `DipoleStatMirror` / `DipoleRetMirror` | `mnpbem/simulation/*_mirror.py` | ✅ Available |
| Mirror Green functions | `CompGreenStatMirror` / `CompGreenRetMirror` | `mnpbem/greenfun/compgreen_*_mirror.py` | ✅ Available |

**EELS + mirror incompatibility** is unsupported, matching MATLAB behavior.

---

## 2. Layered Green Function - `compgreentablayer + tabspace`

| Item | Location | Signature | Status |
|---|---|---|---|
| `CompGreenTabLayer` multi-tab handler | `mnpbem/greenfun/compgreentab_layer.py:208` | `__init__(self, p1, p2, tabs)` | ✅ Available |
| `_MultiGreenTabLayer` internal multi-tab handler | `mnpbem/greenfun/compgreentab_layer.py:12` | `__init__(self, layer, tabs)` | ✅ Available |
| `GreenTabLayer` single-tab handler | `mnpbem/greenfun/greentab_layer.py:30` | `__init__(...)` + `set(enei_arr, **options)` | ✅ Available |
| `GreenRetLayer` reflected Green function | `mnpbem/greenfun/greenret_layer.py` | - | ✅ Available |
| `LayerStructure.tabspace()` | `mnpbem/geometry/layer_structure.py:2190` | `tabspace(self, ...)` | ✅ Available |
| `BEMRetLayer` solver | `mnpbem/bem/bem_ret_layer.py` | - | ✅ Available |
| `BEMStatLayer` solver | `mnpbem/bem/bem_stat_layer.py` | - | ✅ Available |
| `SpectrumRetLayer` / `SpectrumStatLayer` | `mnpbem/spectrum/spectrum_*_layer.py` | - | ✅ Available |

---

## 3. Field Calculation - `meshfield(mindist, nmax)`

| Item | Location | Signature | Status |
|---|---|---|---|
| `MeshField` | `mnpbem/simulation/meshfield.py:18` | `__init__(self, p, x, y, z=None, nmax=None, mindist=None, ...)` + `__call__(self, sig, inout=2, fmm=False, fmm_eps=1e-12)` | ✅ Available |
| FMM multipole acceleration | `mnpbem/simulation/meshfield_fmm.py` | `fmm=True` option | ✅ Available |
| Numba JIT | `mnpbem/simulation/_meshfield_numba.py` | Applied automatically | ✅ Available |

Both `nmax` for chunk-by-chunk processing and `mindist` for surface avoidance
are supported at a level equivalent to MATLAB.

---

## 4. Nonlocal - `nonlocal eps + cover layer + refun`

| Item | Location | Signature | Status |
|---|---|---|---|
| `coverlayer.shift(p1, d, op, ...)` for cover-layer generation | `mnpbem/greenfun/coverlayer.py:25` | `shift(p1, d, op, ...)` | ✅ Available |
| `coverlayer.refine(p, ind)` for `refun` generation | `mnpbem/greenfun/coverlayer.py:159` | `refine(p, ind) -> Callable` | ✅ Available |
| `coverlayer.refineret` / `refinestat` | `mnpbem/greenfun/coverlayer.py:280, 362` | Helper | ✅ Available |
| **`EpsNonlocal` hydrodynamic quantum-model dielectric** | - | - | ❌ Missing |

**Conclusion**: The nonlocal infrastructure, including the cover layer and
`refun`, is fully available, but there is no class equivalent to MATLAB
`epshydrodynamic`, namely `EpsNonlocal`.

**Workaround**: Users can define the hydrodynamic dielectric function directly
with `EpsFun`, following the MATLAB `demospecstat19/20` pattern.

**M5 porting target**: The `EpsNonlocal` class. A single thin wrapper should
be sufficient.

---

## 5. Iterative Solver - `bemiter (BEM*Iter)`

| Item | Location | Signature | Status |
|---|---|---|---|
| `BEMIter` base | `mnpbem/bem/bem_iter.py:11` | `__init__(self, ...)` | ✅ Available |
| `BEMStatIter` | `mnpbem/bem/bem_stat_iter.py:15` | `class BEMStatIter(BEMIter)` | ✅ Available |
| `BEMRetIter` | `mnpbem/bem/bem_ret_iter.py:15` | `class BEMRetIter(BEMIter)` | ✅ Available |
| `BEMRetLayerIter` | `mnpbem/bem/bem_ret_layer_iter.py` | - | ✅ Available |

---

## 6. H2 / ACA Compression - `H-matrix Green`

| Item | Location | Signature | Status |
|---|---|---|---|
| `HMatrix` | `mnpbem/greenfun/hmatrix.py:94` | `__init__(self, ...)` | ✅ Available |
| `ClusterTree` binary clustering | `mnpbem/greenfun/clustertree.py` | - | ✅ Available |
| `ACACompGreenStat` | `mnpbem/greenfun/aca_compgreen_stat.py:11` | `class ACACompGreenStat(object)` | ✅ Available |
| `ACACompGreenRet` | `mnpbem/greenfun/aca_compgreen_ret.py:11` | `class ACACompGreenRet(object)` | ✅ Available |
| `ACACompGreenRetLayer` | `mnpbem/greenfun/aca_compgreen_ret_layer.py` | - | ✅ Available |
| GPU ACA, `aca_block_gpu` | `mnpbem/greenfun/aca_gpu.py:113` | `aca_block_gpu(fun, ...)` | ✅ Available |
| GPU H-matrix | `mnpbem/greenfun/h_matrix_gpu.py` | - | ✅ Available |
| `make_kaware_fadmiss(k)` admissibility helper | `mnpbem/greenfun/hmatrix.py:1118` | - | ✅ Available |

All core components of H2 compression, including clustering, ACA, and
low-rank assembly, are implemented.

---

## 7. Dipole Excitation - `DipoleRet, DipoleStat`

| Item | Location | Signature | Status |
|---|---|---|---|
| `DipoleRet` | `mnpbem/simulation/dipole_ret.py:19` | `__init__(self, pt, dip=None, full=False, medium=1, pinfty=None, **options)` + `__call__(self, p, enei)` | ✅ Available |
| `DipoleStat` | `mnpbem/simulation/dipole_stat.py:20` | - | ✅ Available |
| `DipoleRetMirror` / `DipoleStatMirror` | `mnpbem/simulation/dipole_*_mirror.py` | - | ✅ Available |
| `DipoleRetLayer` / `DipoleStatLayer` | `mnpbem/simulation/dipole_*_layer.py` | - | ✅ Available |
| `dipole_factory.dipole(...)` | `mnpbem/simulation/dipole_factory.py` | - | ✅ Available |

---

## 8. EELS Excitation - `EELSRet, EELSStat`

| Item | Location | Signature | Status |
|---|---|---|---|
| `EELSBase` | `mnpbem/simulation/eels_base.py` | - | ✅ Available |
| `EELSRet` | `mnpbem/simulation/eels_ret.py:24` | `class EELSRet(EELSBase)` + `__call__` | ✅ Available |
| `EELSStat` | `mnpbem/simulation/eels_stat.py:25` | `class EELSStat(EELSBase)` | ✅ Available |
| `electronbeam(...)` factory | `mnpbem/simulation/electronbeam_factory.py` | - | ✅ Available |

---

## 9. Eigenmode - `bemeig (BEMStat eigenmodes)`

| Item | Location | Signature | Status |
|---|---|---|---|
| `BEMStatEig` | `mnpbem/bem/bem_stat_eig.py:22` | `class BEMStatEig(object)` | ✅ Available |
| `BEMStatEigMirror` | `mnpbem/bem/bem_stat_eig_mirror.py` | - | ✅ Available |
| `plasmonmode(...)` helper | `mnpbem/bem/plasmonmode.py` | Top-level export | ✅ Available |

**Retarded eigenmodes** are also handled in MATLAB MNPBEM through
post-analysis using SVD/QR rather than through a dedicated `BEMRetEig` class.
The Python workflow is likewise planned for the postprocessing stage by
extracting the dense matrix and applying NumPy `eig` or `svd`, equivalent to
the `retarded_eigen.py` logic in `mnpbem_simulation`.

---

## 10. Other Infrastructure

| Item | Location | Status |
|---|---|---|
| `BEMRet` / `BEMStat` dense solvers | `mnpbem/bem/bem_*.py` | ✅ |
| `SpectrumRet` / `SpectrumStat` | `mnpbem/spectrum/spectrum_*.py` | ✅ |
| `PlaneWaveRet` / `PlaneWaveStat` | `mnpbem/simulation/planewave_*.py` | ✅ |
| `tricube` / `trisphere` / `trirod` / `triellipsoid` / `tritorus` | `mnpbem/geometry/particle.py` | ✅ |
| `tripolygon` custom polygon to triangular mesh | `mnpbem/geometry/particle.py:787` | ✅ |
| `particle_from_mat` legacy `.mat` import | `mnpbem/geometry/particle.py:964` | ✅, legacy import only |
| `EpsConst` / `EpsTable` / `EpsDrude` / `EpsFun` | `mnpbem/materials/*.py` | ✅ |
| `multi_gpu.solve_spectrum_multi_gpu` | `mnpbem/utils/multi_gpu.py` | ✅ |
| `mpi_dispatch.solve_spectrum_mpi` | `mnpbem/utils/mpi_dispatch.py` | ✅ |
| `bemoptions` / `getbemoptions` | `mnpbem/misc/options.py` | ✅ |

---

## Summary Checklist

| Category | ✅ | ⚠️ | ❌ |
|---|---:|---:|---:|
| Mirror symmetry | 5 | 0 | 0 |
| Layered Green tabulation | 8 | 0 | 0 |
| Field calculation | 3 | 0 | 0 |
| Nonlocal | 4 | 0 | 1, `EpsNonlocal` |
| Iterative solver | 4 | 0 | 0 |
| H2 / ACA | 7 | 0 | 0 |
| Dipole | 5 | 0 | 0 |
| EELS | 4 | 0 | 0 |
| Eigenmode | 3 | 0 | 0 |
| Other infrastructure | 13 | 0 | 0 |
| **Total** | **56** | **0** | **1** |

**Assessment**: Feature coverage of the Python port is approximately
**98% complete**. The only missing item is a single `EpsNonlocal` class
wrapper, which can be bypassed with `EpsFun`. The M5 porting task is therefore
expected to be very lightweight.

When reconstructing `pymnpbem_simulation`, every ✅ feature in this matrix can
be imported and used directly. When the single ❌ nonlocal option is enabled,
the wrapper can branch to an `EpsFun` implementation.
