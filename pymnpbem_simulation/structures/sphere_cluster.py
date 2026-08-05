from typing import Any, Dict, List, Tuple

import numpy as np

from .base import StructureBuilder
from .sphere import (_build_eps_medium, _build_eps_particle, _count_faces,
        _resolve_materials_list, _resolve_rip, n_from_element_size,
        replicate_inout)
from ..util import print_info


def _cluster_positions(n_spheres: int, spacing: float) -> List[Tuple[float, float]]:
    """Close-packed layouts, centred on the cluster's centroid.

    N >= 4 is a central sphere plus the first N-1 vertices of a hexagon around
    it, so every outer sphere touches the centre. (The recipe book used to call
    N=4 a "2x2 grid" and N=6 "3 bottom, 3 top"; neither matched what is built,
    and a square would leave the diagonal pairs apart. The text now describes
    the hexagonal packing.)

    Positions are shifted so the centroid sits at the origin. They previously
    were not — an N=4 cluster of 30 nm spheres had its centre of mass at
    (+7.5, +12.9) nm, which silently offsets the structure from any field grid,
    dipole position or substrate reference built around the origin.
    """
    dy_60 = spacing * np.sqrt(3.0) / 2.0

    hex_positions = []
    for i in range(6):
        angle = i * 60.0 * np.pi / 180.0
        x = spacing * np.cos(angle)
        y = spacing * np.sin(angle)
        hex_positions.append((x, y))

    table = {
        1: [(0.0, 0.0)],
        2: [(-spacing / 2.0, 0.0),
            (+spacing / 2.0, 0.0)],
        3: [(-spacing / 2.0, 0.0),
            (+spacing / 2.0, 0.0),
            (0.0, dy_60)],
        4: [(0.0, 0.0)] + hex_positions[0:3],
        5: [(0.0, 0.0)] + hex_positions[0:4],
        6: [(0.0, 0.0)] + hex_positions[0:5],
        7: [(0.0, 0.0)] + hex_positions[0:6]}

    if n_spheres not in table:
        raise ValueError('[error] <n_spheres> must be 1-7, got <{}>'.format(n_spheres))

    pos = table[n_spheres]
    cx = sum(p[0] for p in pos) / len(pos)
    cy = sum(p[1] for p in pos) / len(pos)

    return [(x - cx, y - cy) for x, y in pos]


class SphereClusterBuilder(StructureBuilder):

    def build(self) -> Tuple[Any, Any, int]:
        from mnpbem.geometry import trisphere, ComParticle

        n_spheres = int(self.cfg_struct.get('n_spheres', 1))
        diameter = float(self.cfg_struct.get('diameter', 50.0))
        # Surface-to-surface gap. A NEGATIVE gap overlaps the spheres: the
        # closed surfaces genuinely intersect (at gap = -0.1 nm on d = 30 nm,
        # 54 of 31808 quadrature points of one sphere fall inside its
        # neighbour), which leaves the inside/outside assignment of the shared
        # volume contradictory and the BEM problem ill-posed. gap = 0 touches
        # without intersecting, so that is the default.
        gap = float(self.cfg_struct.get('gap', 0.0))

        if gap < 0.0:
            print_info(
                '[warn] sphere_cluster gap={} < 0 overlaps the spheres; the '
                'closed surfaces intersect and the BEM inside/outside '
                'assignment is undefined. Use gap=0 for contact. '
                '(구가 실제로 겹칩니다 — 접촉은 gap=0 을 쓰세요.)'.format(gap))
        # <mesh_density> is a boundary-element size in nm, as for cube/rod.
        if 'n_verts' in self.cfg_struct:
            n_verts = int(self.cfg_struct['n_verts'])
        elif 'mesh_density' in self.cfg_struct:
            n_verts = n_from_element_size(
                    diameter, float(self.cfg_struct['mesh_density']))
        else:
            n_verts = 144
        refine = int(self.cfg_struct.get('refine', 2))
        interp = self.cfg_struct.get('interp', 'curv')

        spacing = diameter + gap

        positions = _cluster_positions(n_spheres, spacing)

        medium_name = self.cfg_materials.get('medium', 'water')
        particle_name = self.cfg_materials.get('particle', 'gold')

        rip = _resolve_rip(self.cfg_struct, self.cfg_materials)
        eps_medium = _build_eps_medium(medium_name)
        eps_particle = _build_eps_particle(particle_name, rip)
        epstab = [eps_medium, eps_particle]

        particles = []
        for x, y in positions:
            sph = trisphere(n_verts, diameter)
            sph.shift([x, y, 0.0])
            particles.append(sph)

        epstab, inout = replicate_inout(epstab, [[2, 1]], len(particles))

        p = ComParticle(epstab, particles, inout,
                interp = interp, refine = refine)

        nfaces = _count_faces(p)
        print_info('SphereClusterBuilder: n_spheres={}, diameter={}nm, gap={}nm, nfaces={}'.format(
            n_spheres, diameter, gap, nfaces))

        return p, epstab, nfaces
