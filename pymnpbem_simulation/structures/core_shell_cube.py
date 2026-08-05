from typing import Any, Dict, Optional, Tuple

import numpy as np

from .adaptive_cube_mesh import build_adaptive_cube
from .advanced_monomer_cube import (_resolve_n_per_edge,
        _resolve_roundings)
from .base import StructureBuilder
from .sphere import (_build_eps_medium, _build_eps_particle, _count_faces,
        _resolve_materials_list, _resolve_rip)
from .core_shell_sphere import (_normalize_shells, _build_inout_table,
        _resolve_core_name)
from .cube import _resolve_face_densities, _resolve_edge_profile_kwargs
from ..util import print_info


class CoreShellCubeBuilder(StructureBuilder):
    """Multi-shell core_shell cube builder (1+ shells).

    YAML config (single-shell, legacy)::

        structure:
          type: core_shell_cube
          core_size: 30
          shell_thickness: 5
          n_per_edge: 16

    YAML config (N shells, v1.5+)::

        structure:
          type: core_shell_cube
          core_size: 30
          n_per_edge: 16
          shells:
            - thickness: 3.0
              material: silver
            - thickness: 2.0
              material: silica
    """

    def build(self) -> Tuple[Any, Any, int]:
        from mnpbem.geometry import tricube, ComParticle

        core_size = float(self.cfg_struct.get('core_size', 30.0))

        cum_size_outer = core_size
        shells_raw = self.cfg_struct.get('shells', None)
        if shells_raw:
            for sh in shells_raw:
                cum_size_outer = cum_size_outer + 2.0 * float(sh['thickness'])
        elif 'shell_thickness' in self.cfg_struct:
            cum_size_outer = cum_size_outer + 2.0 * float(self.cfg_struct['shell_thickness'])

        n_per_edge = _resolve_n_per_edge(self.cfg_struct, 1,
                edge_override = cum_size_outer)[0]
        e = float(self.cfg_struct.get('e', self.cfg_struct.get('rounding', 0.25)))
        refine = int(self.cfg_struct.get('refine', 2))
        interp = self.cfg_struct.get('interp', 'curv')

        shells = _normalize_shells(self.cfg_struct, self.cfg_materials,
                default_n = n_per_edge)

        if len(shells) == 0:
            raise ValueError(
                '[error] CoreShellCubeBuilder: no shells specified '
                '(set <shell_thickness> or <shells>)')

        medium_name = self.cfg_materials.get('medium', 'water')
        core_name = _resolve_core_name(self.cfg_struct, self.cfg_materials)

        rip = _resolve_rip(self.cfg_struct, self.cfg_materials)
        eps_medium = _build_eps_medium(medium_name)
        eps_core = _build_eps_particle(core_name, rip)

        epstab = [eps_medium, eps_core]
        for sh in shells:
            epstab.append(_build_eps_particle(sh['material'], rip))

        face_densities = _resolve_face_densities(self.cfg_struct)
        edge_profile_kw = _resolve_edge_profile_kwargs(self.cfg_struct)
        use_adaptive = face_densities is not None or edge_profile_kw is not None

        # Cumulative outer edge of every layer, inner -> outer.
        sizes = [core_size]
        for sh in shells:
            sizes.append(sizes[-1] + 2.0 * float(sh['thickness']))

        n_layers = len(sizes)

        # Per-layer mesh: <mesh_density> is an element size, so each layer must
        # be divided against ITS OWN edge. Sizing every layer off the outermost
        # cube (the previous behaviour) over-meshed the core — for core 30 /
        # outer 40 at mesh_density 2.5 the core came out with 1350 faces
        # instead of 726, a 1.86x excess. advanced_monomer_cube already does
        # the per-layer conversion; this matches it.
        n_per_edges = []
        for size in sizes:
            n_per_edges.append(
                    _resolve_n_per_edge(self.cfg_struct, 1, edge_override = size)[0])

        # Per-layer rounding, honouring <roundings> like the advanced builders.
        # Previously only the single <rounding>/<e> was applied to every layer.
        roundings = _resolve_roundings(self.cfg_struct, n_layers) \
                if 'roundings' in self.cfg_struct else [e] * n_layers

        particles = []
        for i, (size, n_edge, rnd) in enumerate(zip(sizes, n_per_edges, roundings)):

            # An explicit per-shell <n> still wins over the density conversion.
            if i > 0 and shells[i - 1].get('n_explicit', False):
                n_edge = int(shells[i - 1]['n'])

            if use_adaptive:
                particles.append(build_adaptive_cube(
                    size = size, n_default = n_edge,
                    face_densities = face_densities, e = rnd,
                    edge_profile_kwargs = edge_profile_kw, interp = interp))
            else:
                particles.append(tricube(n_edge, size, e = rnd))

        inout = _build_inout_table(len(shells))

        p = ComParticle(epstab, particles, inout,
                interp = interp, refine = refine)

        nfaces = _count_faces(p)
        print_info(
            'CoreShellCubeBuilder: core={}nm, n_shells={}, nfaces={}'.format(
                core_size, len(shells), nfaces))

        return p, epstab, nfaces
