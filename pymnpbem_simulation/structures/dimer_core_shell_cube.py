from typing import Any, Dict, Tuple

import numpy as np

from .advanced_monomer_cube import _resolve_n_per_edge
from .base import StructureBuilder
from .core_shell_sphere import (_resolve_core_name, _normalize_shells,
        _build_inout_table)
from .sphere import (_build_eps_medium, _build_eps_particle, _count_faces,
        _resolve_materials_list, _resolve_rip, replicate_inout)
from ..util import print_info


class DimerCoreShellCubeBuilder(StructureBuilder):

    def build(self) -> Tuple[Any, Any, int]:
        from mnpbem.geometry import tricube, ComParticle

        core_size = float(self.cfg_struct.get('core_size', 30.0))
        gap = float(self.cfg_struct.get('gap', 5.0))

        # N shells via `shells: [{thickness, material}, ...]`, or the legacy
        # single `shell_thickness`. Previously only `shell_thickness` was read,
        # so a multi-shell config silently produced one 5 nm default shell.
        shells = _normalize_shells(self.cfg_struct, self.cfg_materials,
                default_n = 0)

        if len(shells) == 0:
            raise ValueError(
                '[error] DimerCoreShellCubeBuilder: no shells specified '
                '(set <shell_thickness> or <shells>)')

        # Cumulative outer size of every layer, inner -> outer.
        sizes = [core_size]
        for sh in shells:
            sizes.append(sizes[-1] + 2.0 * float(sh['thickness']))

        outer_size = sizes[-1]
        n_per_edge = _resolve_n_per_edge(self.cfg_struct, 1,
                edge_override = outer_size)[0]
        e = float(self.cfg_struct.get('e', self.cfg_struct.get('rounding', 0.25)))
        refine = int(self.cfg_struct.get('refine', 2))
        interp = self.cfg_struct.get('interp', 'curv')

        shift = (outer_size + gap) / 2.0

        medium_name = self.cfg_materials.get('medium', 'water')
        core_name = _resolve_core_name(self.cfg_struct, self.cfg_materials)

        rip = _resolve_rip(self.cfg_struct, self.cfg_materials)
        eps_medium = _build_eps_medium(medium_name)
        epstab = [eps_medium, _build_eps_particle(core_name, rip)]

        for sh in shells:
            epstab.append(_build_eps_particle(sh['material'], rip))

        particles = []
        for sign in (-1.0, +1.0):
            for size in sizes:
                cube = tricube(n_per_edge, size, e = e)
                cube.shift([sign * shift, 0.0, 0.0])
                particles.append(cube)

        single_inout = _build_inout_table(len(shells))
        epstab, inout = replicate_inout(epstab, single_inout, 2)

        p = ComParticle(epstab, particles, inout,
                interp = interp, refine = refine)

        nfaces = _count_faces(p)
        print_info(
            'DimerCoreShellCubeBuilder: core={}nm, n_shells={}, outer={}nm, '
            'gap={}nm, nfaces={}'.format(
                core_size, len(shells), outer_size, gap, nfaces))

        return p, epstab, nfaces
