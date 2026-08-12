from typing import Any, Dict, Tuple

import numpy as np

from .base import StructureBuilder
from ..util import print_info


_MATERIAL_DEFAULTS = {
    'water': 1.33 ** 2,
    'vacuum': 1.0,
    'air': 1.0,
    'glass': 1.5 ** 2}

# Available trisphere vertex counts (same list used by MATLAB trisphere.m)
_TRISPHERE_AVAILABLE = [
    32, 60, 144, 169, 225, 256, 289, 324, 361, 400,
    441, 484, 529, 576, 625, 676, 729, 784, 841, 900,
    961, 1024, 1225, 1444]


def n_from_element_size(diameter: float, element_size: float) -> int:
    """trisphere vertex count whose mean element edge is ~ ``element_size`` nm.

    trisphere(N) triangulates the sphere into about 2N faces over an area of
    pi * d^2. Equating the mean face area to that of an equilateral triangle
    of side s gives

        pi * d^2 / (2 N) = sqrt(3) / 4 * s^2   ->   N = 2 pi d^2 / (sqrt(3) s^2)

    The result is snapped to the nearest available trisphere count. Hitting
    either end of that list is reported, because there the requested element
    size is silently not honoured.
    """
    if element_size <= 0.0:
        raise ValueError(
            '[error] <mesh_density> must be > 0, got <{}>'.format(element_size))

    target = 2.0 * np.pi * diameter ** 2 / (np.sqrt(3.0) * element_size ** 2)
    n = min(_TRISPHERE_AVAILABLE, key = lambda x: abs(x - target))

    if target > _TRISPHERE_AVAILABLE[-1]:
        print_info(
            '[warn] mesh_density={} nm on d={} nm needs ~{} vertices but '
            'trisphere maxes out at {} — element size will be coarser than '
            'requested. (요청 요소 크기보다 성긴 메시가 됩니다.)'.format(
                element_size, diameter, int(round(target)),
                _TRISPHERE_AVAILABLE[-1]))
    elif target < _TRISPHERE_AVAILABLE[0]:
        print_info(
            '[warn] mesh_density={} nm on d={} nm needs only ~{} vertices; '
            'trisphere starts at {} — element size will be finer than '
            'requested. (요청보다 조밀한 메시가 됩니다.)'.format(
                element_size, diameter, int(round(target)),
                _TRISPHERE_AVAILABLE[0]))

    return int(n)


def replicate_inout(epstab: list,
        inout_single: list,
        n_copies: int,
        medium_index: int = 1) -> Tuple[list, list]:
    """Replicate one object's ``(epstab, inout)`` block for N disconnected copies.

    MNPBEM gives every disconnected interior region its own entry in the
    dielectric table, even when the material is identical. Sharing one index
    makes the solver treat the two interiors as a single connected region and
    adds a spurious coupling term through that material — measurable as soon as
    the particles are close (a 30 nm gold sphere dimer in water shifts by 1.0 %
    at a 5 nm gap and 5.5 % at 0.6 nm; it vanishes beyond ~200 nm because the
    metal is lossy).

    Every MNPBEM demo with two identical particles duplicates the entry for
    exactly this reason::

        Demo/planewave/stat/demospecstat8.m:12,26   gold bowtie
        Demo/planewave/stat/demospecstat9.m:14,30   gold spheres
        Demo/eels/ret/demoeelsret9.m:13,29          silver rods

        epstab = { epsconst(1), epstable('gold.dat'), epstable('gold.dat') };
        comparticle( epstab, {p1, p2}, [2, 1; 3, 1], 1, 2, op );

    The medium index is shared (all particles sit in the same embedding
    medium); only interior entries are duplicated.
    """
    epstab_out = list(epstab)
    inout_out = [list(row) for row in inout_single]

    for _ in range(1, int(n_copies)):
        mapping = dict()

        for row in inout_single:
            for idx in row:

                if idx == medium_index or idx in mapping:
                    continue

                epstab_out.append(epstab[idx - 1])
                mapping[idx] = len(epstab_out)

        for row in inout_single:
            inout_out.append([mapping.get(i, i) for i in row])

    return epstab_out, inout_out


def _resolve_sphere_n(cfg: Dict, diameter: float = None) -> int:
    """Resolve trisphere vertex count from config.

    Priority:
    1. ``nphi`` (legacy): ``n = round(((diameter+1)*pi/nphi)^2 / 2)``
       snapped to nearest available count — mirrors OLD geometry_generator.py.
    2. ``n_verts``: an explicit vertex count, used as given.
    3. ``mesh_density``: the boundary-element size in nm, same meaning as for
       the cube and rod builders, converted via :func:`n_from_element_size`.
    4. Default: 256.

    ``diameter`` overrides ``cfg['diameter']`` so callers that name the size
    differently (core_diameter, per-shell diameters) get the right conversion.
    """
    if diameter is None:
        diameter = float(cfg.get('diameter', 50.0))

    if 'nphi' in cfg:
        nphi = float(cfg['nphi'])
        target = int(round(((diameter + 1) * np.pi / nphi) ** 2 / 2))
        n = min(_TRISPHERE_AVAILABLE,
                key = lambda x: abs(x - target))
        return n

    if 'n_verts' in cfg:
        return int(cfg['n_verts'])

    if 'mesh_density' in cfg:
        return n_from_element_size(float(diameter), float(cfg['mesh_density']))

    return 256


class SphereBuilder(StructureBuilder):

    def build(self) -> Tuple[Any, Any, int]:
        from mnpbem.materials import EpsConst, EpsTable
        from mnpbem.geometry import trisphere, ComParticle

        diameter = float(self.cfg_struct.get('diameter', 50.0))
        n = _resolve_sphere_n(self.cfg_struct, diameter)
        refine = int(self.cfg_struct.get('refine', 2))
        interp = self.cfg_struct.get('interp', 'curv')

        medium_name = self.cfg_materials.get('medium', 'water')
        particle_name = self.cfg_materials.get('particle', 'gold')

        rip = _resolve_rip(self.cfg_struct, self.cfg_materials)
        eps_medium = _build_eps_medium(medium_name, rip)
        eps_particle = _build_eps_particle(particle_name, rip)
        epstab = [eps_medium, eps_particle]

        sphere = trisphere(n, diameter)

        p = ComParticle(epstab, [sphere], [[2, 1]],
                interp = interp, refine = refine)

        nfaces = _count_faces(p)
        print_info('SphereBuilder: diameter={}nm, n={}, nfaces={}'.format(
            diameter, n, nfaces))

        return p, epstab, nfaces


def _build_eps_medium(name: str, custom: Any = None) -> Any:
    from mnpbem.materials import EpsConst, EpsTable

    name_l = name.lower()

    if name_l in _MATERIAL_DEFAULTS:
        return EpsConst(_MATERIAL_DEFAULTS[name_l])

    if name.endswith('.dat'):
        return EpsTable(name)

    # An embedding medium can be any registered material, not just the handful
    # of built-in names: the GUI offers the same material list for environment,
    # substrate and particle, and a config can name a custom dielectric here as
    # readily as on the particle. Without this the name fell through to
    # float(name) and surfaced as "could not convert string to float: 'gold'".
    eps_custom = _eps_from_custom(name, custom)
    if eps_custom is not None:
        return eps_custom

    try:
        return EpsConst(float(name))
    except ValueError:
        raise ValueError(
                '[error] Unsupported <medium> = <{}>! Use a built-in name ({}), '
                'a refractive index, a .dat table, or a material registered in '
                '<materials.refractive_index_paths>.'.format(
                        name, ', '.join(sorted(_MATERIAL_DEFAULTS))))


def _build_eps_particle(name: str, custom: Any = None) -> Any:
    from mnpbem.materials import EpsConst, EpsTable, EpsDrude

    name_l = name.lower()

    if name_l in {'gold', 'au'}:
        return EpsTable('gold.dat')

    if name_l in {'silver', 'ag'}:
        return EpsTable('silver.dat')

    if name.endswith('.dat'):
        return EpsTable(name)

    eps_custom = _eps_from_custom(name, custom)
    if eps_custom is not None:
        return eps_custom

    raise ValueError('[error] Unsupported <particle> = <{}>!'.format(name))


def _eps_from_custom(name: str, custom: Any = None) -> Any:
    """Resolve <name> against refractive_index_paths, or None if absent.

    Shared by the medium and particle builders so a material registered once is
    usable wherever a material name is accepted.
    """
    from mnpbem.materials import EpsConst, EpsTable

    if not isinstance(custom, dict) or not custom:
        return None

    name_l = name.lower()

    # custom material from refractive_index_paths (e.g. agcl, ito).
    # Supports both descriptor dicts and runtime-resolved values:
    #   {'agcl': {'type': 'constant', 'epsilon': 2.02}} -> EpsConst(2.02)
    #   {'foo':  {'type': 'table', 'file': 'foo.dat'}}  -> EpsTable('foo.dat')
    #   {'foo': 'foo.dat'}                               -> EpsTable('foo.dat')
    #   {'foo': 2.02}                                    -> EpsConst(2.02)
    #   {'foo': <callable>}                              -> <callable>
    cmap = {str(k).lower(): v for k, v in custom.items()}
    if name_l not in cmap:
        return None

    m = cmap[name_l]

    # Runtime value resolved by material_descriptor.py.
    if callable(m):
        return m

    if isinstance(m, (int, float)):
        return EpsConst(float(m))

    if isinstance(m, str):
        if m.endswith('.dat'):
            return EpsTable(m)
        try:
            return EpsConst(float(m))
        except ValueError:
            return EpsTable(m)

    if isinstance(m, dict):
        mtype = str(m.get('type', 'constant')).lower()
        if mtype == 'constant':
            if 'epsilon' not in m:
                raise ValueError('[error] Missing <epsilon> for custom '
                                 'material <{}>!'.format(name))
            return EpsConst(float(m['epsilon']))

        if mtype == 'table':
            path = m.get('path', m.get('file', name))
            return EpsTable(str(path))

        if mtype == 'python_module':
            # If resolver is bypassed, allow direct callable injection.
            fn = m.get('callable', None)
            if callable(fn):
                return fn
            raise ValueError('[error] Unsupported unresolved '
                             '<python_module> descriptor for material '
                             '<{}>; run descriptor resolver first!'.format(name))

        # Legacy path-like dicts without explicit type.
        if 'path' in m or 'file' in m:
            return EpsTable(str(m.get('path', m.get('file'))))

    raise ValueError('[error] Unsupported custom material spec for '
                     '<{}>: <{}>!'.format(name, type(m).__name__))


def _resolve_materials_list(cfg_struct: Any, cfg_materials: Any) -> list:
    """Per-layer materials list, tolerating both config layouts.

    Direct .py configs carry the list under ``structure.materials``; the yaml
    migration (py_to_yaml) routes it to ``materials.particle_list``. Read the
    structure section first, then fall back to the materials section so CLI
    runs (migrated) and direct builder calls resolve to the same materials.
    """
    mats = (cfg_struct or {}).get('materials')
    if not mats:
        mats = (cfg_materials or {}).get('particle_list')
    return list(mats) if mats else []


def _resolve_rip(cfg_struct: Any, cfg_materials: Any) -> Any:
    """``refractive_index_paths`` from either config section (custom eps).

    Same rationale as :func:`_resolve_materials_list` — the migration routes
    ``refractive_index_paths`` into the materials section, so a builder reading
    only ``cfg_struct`` would silently lose custom dielectrics under the CLI.
    """
    return ((cfg_struct or {}).get('refractive_index_paths')
            or (cfg_materials or {}).get('refractive_index_paths')
            or None)


def _count_faces(p: Any) -> int:
    if hasattr(p, 'pfull'):
        return int(p.pfull.nfaces)

    if hasattr(p, 'nfaces'):
        return int(p.nfaces)

    if hasattr(p, 'pos'):
        return int(len(p.pos))

    return -1
