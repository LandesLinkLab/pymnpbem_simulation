from typing import Any, Dict, Tuple

import numpy as np

from .base import StructureBuilder
from .sphere import (_build_eps_medium, _build_eps_particle, _count_faces,
        _resolve_materials_list, _resolve_rip, _resolve_sphere_n)
from ..util import print_info


class EllipsoidBuilder(StructureBuilder):
    """Ellipsoid from an anisotropically scaled reference sphere.

    ``axes`` are SEMI-axes [a, b, c] in nm, so the particle spans 2a x 2b x 2c.
    (Note this differs from the sphere and cube builders, whose ``diameter`` /
    ``size`` are full extents — the semi-axis convention is what the recipe
    book documents for this builder, so it is kept.)

    Implementation note: MNPBEM has no ellipsoid generator, and the engine's
    ``triellipsoid`` builds a Fibonacci point set and returns a Particle
    without ``verts2``. Without midpoint vertices ``interp='curv'`` silently
    degrades to flat elements — measured on axes [10, 15, 20] with 508 faces,
    the surface area came out 1.27 % low and the volume 2.29 % low, and passing
    the particle through ``ComParticle(interp='curv')`` changed nothing (bit
    identical), confirming curv was a no-op.

    Scaling a ``trisphere`` instead keeps ``verts2`` (``Particle.scale``
    transforms it too), so curved elements survive: the same 508-face case then
    lands within 0.056 % of the analytic Thomsen area — about 23x better.
    """

    def build(self) -> Tuple[Any, Any, int]:
        from mnpbem.geometry import trisphere, ComParticle

        axes = self.cfg_struct.get('axes', [10.0, 15.0, 20.0])
        axes = [float(v) for v in axes]
        assert len(axes) == 3, '[error] <axes> must be [a, b, c]'

        # mesh_density is an element size in nm; size it off the mean diameter
        # so the conversion matches the sphere builders.
        mean_diameter = 2.0 * float(np.mean(axes))
        n_verts = _resolve_sphere_n(self.cfg_struct, mean_diameter)
        refine = int(self.cfg_struct.get('refine', 2))
        interp = self.cfg_struct.get('interp', 'curv')

        medium_name = self.cfg_materials.get('medium', 'water')
        particle_name = self.cfg_materials.get('particle', 'gold')

        rip = _resolve_rip(self.cfg_struct, self.cfg_materials)
        eps_medium = _build_eps_medium(medium_name, rip)
        eps_particle = _build_eps_particle(particle_name, rip)
        epstab = [eps_medium, eps_particle]

        # Unit-diameter reference sphere, then scale to the requested semi-axes.
        ell = trisphere(n_verts, 2.0)
        ell.scale(axes)

        p = ComParticle(epstab, [ell], [[2, 1]],
                interp = interp, refine = refine)

        nfaces = _count_faces(p)
        print_info('EllipsoidBuilder: semi-axes={}, n_verts={}, nfaces={}'.format(
            axes, n_verts, nfaces))

        return p, epstab, nfaces
