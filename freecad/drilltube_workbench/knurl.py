"""Straight (axial) knurling ridges for the cap's grip surface.

Unlike the helical thread, these ridges run straight along the cap's axis,
so each one is just a flat profile face extruded linearly along Z and
copied around the circumference by rotation -- no sweep/loft is needed,
and there's no equivalent of the thread's profile-orientation pitfall
(see thread.py) since the profile only needs to be perpendicular to a
purely axial extrusion direction, which a flat XY-plane polygon already is.
"""

import math

import FreeCAD
import Part

# Same FDM-printability floor used for the thread's crest/root -- a ridge
# tip thinner than this won't print as a real, consistent feature.
MIN_FLAT_MM = 0.4

# How far a ridge's base should be embedded past the nominal surface radius,
# rather than sitting exactly tangent to it -- the same OCC zero-overlap
# fuse pitfall as the thread ridge (see thread.EMBED_MM).
EMBED_MM = 0.2


def ridge_count(outer_radius, pitch, minimum=8):
    """How many evenly-spaced ridges fit a given circumference at
    roughly `pitch` spacing, never fewer than `minimum`."""
    if outer_radius <= 0:
        raise ValueError("outer_radius must be > 0")
    if pitch <= 0:
        raise ValueError("pitch must be > 0")
    circumference = 2 * math.pi * outer_radius
    return int(max(minimum, round(circumference / pitch)))


def _ridge_face(outer_radius, depth, base_width, tip_width, embed=EMBED_MM):
    base_r = outer_radius - embed
    tip_r = outer_radius + depth
    pts = [
        FreeCAD.Vector(base_r, -base_width / 2.0, 0),
        FreeCAD.Vector(base_r, base_width / 2.0, 0),
        FreeCAD.Vector(tip_r, tip_width / 2.0, 0),
        FreeCAD.Vector(tip_r, -tip_width / 2.0, 0),
        FreeCAD.Vector(base_r, -base_width / 2.0, 0),
    ]
    return Part.Face(Part.Wire(Part.makePolygon(pts)))


def make_knurl_ridges(outer_radius, height, pitch, depth, z0=0.0, min_count=8):
    """A fused solid: evenly-spaced straight ridges around the
    circumference, each a simple vertical prism (no sweep/loft), ready to
    be fused onto a cylindrical grip surface."""
    if outer_radius <= 0:
        raise ValueError("outer_radius must be > 0")
    if height <= 0:
        raise ValueError("height must be > 0")
    if depth <= 0:
        raise ValueError("depth must be > 0")

    count = ridge_count(outer_radius, pitch, min_count)
    base_width = pitch * 0.5
    tip_width = max(MIN_FLAT_MM, min(base_width * 0.4, base_width * 0.9))

    face = _ridge_face(outer_radius, depth, base_width, tip_width)
    prism = face.extrude(FreeCAD.Vector(0, 0, height))
    prism.translate(FreeCAD.Vector(0, 0, z0))

    ridges = []
    for i in range(count):
        copy = prism.copy()
        copy.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), i * 360.0 / count)
        ridges.append(copy)

    return ridges[0].fuse(ridges[1:]) if len(ridges) > 1 else ridges[0]
