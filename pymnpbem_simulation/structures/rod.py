from typing import Any, Dict, List, Tuple

import numpy as np

from .base import StructureBuilder
from .sphere import (_build_eps_medium, _build_eps_particle, _count_faces,
        _resolve_materials_list, _resolve_rip)
from ..util import print_info


def _resolve_rod_mesh(cfg: Dict[str, Any], diameter: float, height: float) -> List[int]:
    """Discretisation counts [nphi, ntheta, nz] handed to trirod.

    Two ways to ask for a mesh:

    1. ``nphi`` / ``ntheta`` / ``nz`` -- SPACINGS, not counts, matching the older
       MATLAB-based mnpbem_simulation wrapper
       (sim_utils/geometry_generator.py:_legacy_mesh_to_n_rod)::

           nphi   = max(8, ceil((diameter + 1) * pi / nphi))
           ntheta = max(6, ceil((diameter + 1) / ntheta))
           nz     = max(4, ceil((height - diameter + 1) / nz))

       Smaller values give a finer mesh, which is the opposite of what the
       numbers mean inside trirod. The two wrappers used the same key names for
       opposite conventions, and carrying a config across silently produced the
       wrong mesh: nphi = 3 on a 20 x 60 nm rod means 22 azimuthal divisions
       here but was taken literally as 3 before, giving 12 boundary elements and
       a singular BEM matrix (MATLAB does the same at that mesh).

    2. ``mesh_density`` -- boundary-element size in nm, the same meaning it has
       for the cube and sphere builders.

    To match a MATLAB script that passes trirod counts directly, invert the
    formula: counts [15, 20, 20] on a 20 x 60 nm rod correspond to nphi = 4.4,
    ntheta = 1.05, nz = 2.05.
    """
    if 'nphi' in cfg or 'ntheta' in cfg or 'nz' in cfg:
        nphi_s = float(cfg.get('nphi', 2.0))
        ntheta_s = float(cfg.get('ntheta', 2.0))
        nz_s = float(cfg.get('nz', 2.0))

        for name, val in (('nphi', nphi_s), ('ntheta', ntheta_s), ('nz', nz_s)):
            if val <= 0:
                raise ValueError(
                    '[error] <{}> is a spacing and must be > 0, got <{}>. '
                    'Smaller means finer. '
                    '({} is a spacing, not a division count.)'.format(name, val, name))

        nphi = max(8, int(np.ceil((diameter + 1.0) * np.pi / nphi_s)))
        ntheta = max(6, int(np.ceil((diameter + 1.0) / ntheta_s)))
        nz = max(4, int(np.ceil(max(0.0, height - diameter + 1.0) / nz_s)))
        return [nphi, ntheta, nz]

    element_size = float(cfg.get('mesh_density', 2.0))
    nphi = max(8, int(np.ceil(np.pi * diameter / element_size)))
    ntheta = max(6, int(np.ceil(0.5 * diameter / element_size)))
    nz = max(2, int(np.ceil(max(0.0, height - diameter) / element_size)))
    return [nphi, ntheta, nz]


class RodBuilder(StructureBuilder):

    def build(self) -> Tuple[Any, Any, int]:
        from mnpbem.geometry import trirod, ComParticle

        diameter = float(self.cfg_struct.get('diameter', 10.0))
        height = float(self.cfg_struct.get('height', 50.0))
        refine = int(self.cfg_struct.get('refine', 2))
        interp = self.cfg_struct.get('interp', 'curv')
        horizontal = bool(self.cfg_struct.get('horizontal', True))

        # MATLAB trirod returns quadrilateral faces (with triangles only at the
        # cap poles). Splitting every quad into two triangles is a DIFFERENT
        # discretisation, not a refinement: measured against MATLAB it moves
        # the transverse cross section by ~10% and the longitudinal one by ~3%
        # at [15, 20, 20]. Default to the MATLAB mesh; set <triangles: true>
        # to opt back into the split.
        triangles = bool(self.cfg_struct.get('triangles', False))

        n_mesh = _resolve_rod_mesh(self.cfg_struct, diameter, height)

        medium_name = self.cfg_materials.get('medium', 'water')
        particle_name = self.cfg_materials.get('particle', 'gold')

        rip = _resolve_rip(self.cfg_struct, self.cfg_materials)
        eps_medium = _build_eps_medium(medium_name)
        eps_particle = _build_eps_particle(particle_name, rip)
        epstab = [eps_medium, eps_particle]

        rod = trirod(diameter, height, n_mesh, triangles = triangles)

        if horizontal:
            rod.rot(90, [0, 1, 0])

        p = ComParticle(epstab, [rod], [[2, 1]],
                interp = interp, refine = refine)

        nfaces = _count_faces(p)
        print_info('RodBuilder: diameter={}nm, height={}nm, mesh={}, nfaces={}'.format(
            diameter, height, n_mesh, nfaces))

        return p, epstab, nfaces
