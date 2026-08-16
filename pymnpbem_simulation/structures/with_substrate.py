from typing import Any, Dict, Tuple, Optional

import numpy as np

from .base import StructureBuilder
from ..util import print_info


_SUBSTRATE_PRESETS = {
    'glass': 1.5 ** 2,
    'silica': 1.45 ** 2,
    'silicon': 3.5 ** 2,
    'water': 1.33 ** 2,
    'vacuum': 1.0,
    'air': 1.0}


class WithSubstrateBuilder(StructureBuilder):
    """Wrap an arbitrary base structure on top of a planar dielectric substrate.

    The base structure is built first via the standard registry; its natural
    coordinates are preserved (the particle is never shifted). The substrate
    interface is placed automatically at ``substrate_z = particle_bottom - gap``
    so the particle surface sits exactly ``gap`` nm above the substrate. A
    LayerStructure is constructed using the medium (above) + substrate
    (below), and the substrate eps is appended to ``epstab`` so MNPBEM can
    resolve the layered Green function.

    ``particle_bottom`` is the lowest MESH VERTEX, i.e. the ideal (analytic)
    surface, matching how one would place a particle by hand in MATLAB MNPBEM
    with ``p.shift``. Using the lowest face CENTROID instead would make the
    physical separation mesh-dependent: centroids sit inside a curved surface
    by the chord sag, which grows like the square of the element size
    (0.02 nm at 2 nm elements, 0.22 nm at 6 nm elements for a d = 20 nm rod),
    so ``gap = 1.0`` would mean anything from 0.98 to 0.78 nm. With vertices
    the requested gap is exact and mesh-independent, and ``gap = 0.001``
    reproduces the MATLAB touching convention.

    Returned tuple is ``(p, epstab, nfaces)`` to remain compatible with the
    standard build_structure contract; the LayerStructure is attached on
    the particle as the attribute ``_mnpbem_layer`` so simulation runners
    can pick it up without changing the dispatch signature.

    Example YAML::

        structure:
          type: with_substrate
          base:
            type: sphere
            diameter: 20
            mesh_density: 144
          substrate:
            eps: 2.25            # n=1.5 glass; or 'glass'/'silicon'/...
            gap: 0.001           # nm above substrate (default touching)

        materials:
          medium: vacuum
          particle: gold
    """

    def build(self) -> Tuple[Any, Any, int]:
        from mnpbem.materials import EpsConst, EpsTable
        from mnpbem.geometry import LayerStructure

        from . import build_structure

        cfg_base = self.cfg_struct.get('base', None)

        if cfg_base is None:
            raise ValueError(
                '[error] <structure.base> required for type=with_substrate')

        cfg_sub = self.cfg_struct.get('substrate', dict())

        if 'z_position' in cfg_sub or 'z_shift' in cfg_sub:
            print_info(
                '[warn] WithSubstrate: <z_position>/<z_shift> ignored — only <gap> is '
                'supported (default 0.001 nm = touching). '
                '(<z_position>/<z_shift> 무시됨 — <gap> 만 지원.)')

        gap = float(cfg_sub.get('gap', 0.001))
        eps_sub_spec = cfg_sub.get('eps', 'glass')

        # Build the base particle using the existing registry
        p, epstab_base, nfaces_base = build_structure(cfg_base, self.cfg_materials)

        # Construct the substrate dielectric
        from .sphere import _resolve_rip

        eps_sub = _build_eps_substrate(
                eps_sub_spec, _resolve_rip(self.cfg_struct, self.cfg_materials))

        # Append substrate eps to the table; particle inout assignments stay
        # valid (they reference indices 1, 2 = medium, particle).
        epstab = list(epstab_base) + [eps_sub]
        sub_idx = len(epstab)  # 1-indexed for LayerStructure ind argument

        # Determine medium index in epstab. Convention used by other builders:
        # epstab[0] = medium (index 1), epstab[1] = particle (index 2).
        # LayerStructure.ind uses 1-based MATLAB indexing.
        medium_idx = 1

        # Place the substrate interface so the particle SURFACE sits <gap> nm
        # above it. Particle coordinates are NEVER modified; the substrate
        # plane adapts to the particle's natural geometry.
        try:
            zmin = float(_get_particle_verts(p)[:, 2].min())
        except Exception as e:
            raise RuntimeError(
                '[error] WithSubstrateBuilder: cannot read particle z positions: {}'.format(e))

        try:
            z_centroid = float(_get_particle_pos(p)[:, 2].min())
        except Exception:
            z_centroid = float('nan')

        # Curved-element interpolation puts collocation points on the true
        # surface, so on a fine mesh the lowest centroid can sit *below* the
        # lowest vertex. Referencing the vertices alone then buried a face in
        # the substrate: BEMStatLayer asserts ("p2 must be in upper medium")
        # and the retarded solver quietly treats that face as substrate-side.
        # Reference whichever is lower so every collocation point clears the
        # interface by at least <gap>.
        z_ref = zmin
        if np.isfinite(z_centroid):
            z_ref = min(zmin, z_centroid)

        substrate_z = z_ref - gap

        # Build the LayerStructure: top layer = medium, bottom layer = substrate.
        layer = LayerStructure(epstab, [medium_idx, sub_idx], [substrate_z])

        # ComParticle was built by the base builder with only [medium, particle]
        # in its eps list. Spectrum/far-field code paths reference
        # ``p.eps[layer.ind[-1] - 1]`` to look up the substrate refractive
        # index, so the extended epstab (including substrate) must be visible
        # on the particle. Splice the full table in-place.
        try:
            p.eps = list(epstab)
        except Exception:
            pass

        if hasattr(p, 'pc') and p.pc is not None:
            try:
                p.pc.eps = list(epstab)
            except Exception:
                pass

        # Stash the layer on the particle for the simulation runner to pick up.
        # We use a dedicated attribute name to avoid colliding with mnpbem internals.
        try:
            setattr(p, '_mnpbem_layer', layer)
        except Exception:
            # ComParticle may use slots; fall back to an attribute on pfull.
            if hasattr(p, 'pfull'):
                setattr(p.pfull, '_mnpbem_layer', layer)

        nfaces = _count_faces(p, fallback = nfaces_base)

        print_info(
            'WithSubstrate: base={}, eps={}, gap={} nm, substrate_z={:.4f} nm, nfaces={}'.format(
                cfg_base.get('type'), _eps_repr(eps_sub_spec),
                gap, substrate_z, nfaces))
        print_info(
            'WithSubstrate: surface z={:.4f} (gap reference), lowest centroid z={:.4f} '
            '-> collocation clearance {:.4f} nm'.format(
                zmin, z_centroid, z_centroid - substrate_z))
        print_info(
            'WithSubstrate: layer ind=[{}, {}] (medium, substrate)'.format(
                medium_idx, sub_idx))

        return p, epstab, nfaces


def _build_eps_substrate(spec: Any, custom: Any = None) -> Any:
    from mnpbem.materials import EpsConst, EpsTable

    from .sphere import _eps_from_custom

    # A dielectric function resolved by material_descriptor.py (a user .py
    # material) arrives as a callable and is already what mnpbem wants.
    if callable(spec):
        return spec

    if spec is None or (isinstance(spec, str) and not spec.strip()):
        raise ValueError(
                '[error] No <substrate> material set — give '
                '<materials.substrate.material> a preset name, a refractive '
                'index or a .dat table.')

    if isinstance(spec, (int, float)):
        return EpsConst(float(spec))

    if isinstance(spec, str):
        spec_l = spec.lower()
        if spec_l in _SUBSTRATE_PRESETS:
            return EpsConst(_SUBSTRATE_PRESETS[spec_l])
        if spec.endswith('.dat'):
            return EpsTable(spec)

        # Same reason as the medium builder: the GUI offers one material list
        # for every slot, so a registered material must resolve here too.
        # config._resolve_substrate_eps() handles the constant/table cases but
        # leaves .py-module materials as a bare name.
        eps_custom = _eps_from_custom(spec, custom)
        if eps_custom is not None:
            return eps_custom

        try:
            return EpsConst(float(spec))
        except ValueError:
            raise ValueError(
                '[error] Unsupported <substrate.eps>=<{}>! Use a preset ({}), a '
                'refractive index, a .dat table, or a material registered in '
                '<materials.refractive_index_paths>.'.format(
                        spec, ', '.join(sorted(_SUBSTRATE_PRESETS))))

    raise ValueError(
        '[error] Unsupported <substrate.eps> type: <{}>!'.format(type(spec).__name__))


def _eps_repr(spec: Any) -> str:
    if isinstance(spec, str):
        return spec
    return repr(spec)


def _get_particle_pos(p: Any) -> np.ndarray:
    if hasattr(p, 'pos') and getattr(p, 'pos') is not None:
        return np.asarray(p.pos)
    if hasattr(p, 'pfull') and hasattr(p.pfull, 'pos'):
        return np.asarray(p.pfull.pos)
    raise AttributeError('[error] particle has no <pos> attribute')


def _get_particle_verts(p: Any) -> np.ndarray:
    """Mesh vertices, i.e. points lying on the ideal (analytic) surface.

    ComParticle exposes ``verts``; mirror-symmetric particles keep the full
    mesh on ``pfull``. Falls back to face centroids only if no vertex array
    can be reached, in which case the gap is short by the chord sag.
    """
    for obj in (p, getattr(p, 'pfull', None)):

        if obj is None:
            continue

        verts = getattr(obj, 'verts', None)

        if verts is not None:
            verts = np.asarray(verts)

            if verts.ndim == 2 and verts.shape[1] >= 3 and len(verts) > 0:
                return verts

    parts = getattr(p, 'p', None)

    if isinstance(parts, (list, tuple)) and len(parts) > 0:
        stacked = [np.asarray(part.verts) for part in parts
                if getattr(part, 'verts', None) is not None]

        if len(stacked) > 0:
            return np.vstack(stacked)

    print_info('[warn] WithSubstrate: no vertex array — falling back to face '
            'centroids, so the gap is short by the chord sag. '
            '(정점 배열 없음 — 면 중심 기준으로 대체됨.)')

    return _get_particle_pos(p)


def _count_faces(p: Any, fallback: int = -1) -> int:
    if hasattr(p, 'pfull') and hasattr(p.pfull, 'nfaces'):
        return int(p.pfull.nfaces)
    if hasattr(p, 'nfaces'):
        return int(p.nfaces)
    if hasattr(p, 'pos') and p.pos is not None:
        return int(len(p.pos))
    return int(fallback)
