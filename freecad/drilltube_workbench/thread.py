"""Coarse, FDM-friendly helical thread geometry.

A single-start trapezoidal thread ridge, swept along a helix. Trapezoidal
(rather than a sharp 60-degree V) avoids a knife-thin crest that FDM
printers round off badly. Base/tip width are derived from pitch so the
profile can never overlap between adjacent turns, regardless of what pitch
the caller picks.
"""

import FreeCAD
import Part

BASE_WIDTH_FRACTION = 0.5
TIP_WIDTH_FRACTION = 0.2

# How far a ridge's base should be embedded into the surface it's fused onto, rather than
# sitting exactly tangent to it -- a zero-overlap fuse is an OCC degenerate case that can
# produce an invalid result ("Invalid imbrication of wires") for some sizes.
EMBED_MM = 0.2


def make_thread_ridge(base_radius, pitch, length, thread_height, z0=0.0):
    """A solid helical ridge: the thread, ready to be fused onto an
    external surface or cut out of an internal bore.

    base_radius: radius of the cylindrical surface the thread sits on.
    pitch: axial distance per full turn (mm).
    length: axial length of the threaded section (mm).
    thread_height: radial depth of the thread (mm).
    z0: axial offset of the threaded section's start.
    """
    if base_radius <= 0:
        raise ValueError("base_radius must be > 0")
    if pitch <= 0:
        raise ValueError("pitch must be > 0")
    if length <= 0:
        raise ValueError("length must be > 0")
    if thread_height <= 0:
        raise ValueError("thread_height must be > 0")

    base_width = BASE_WIDTH_FRACTION * pitch
    tip_width = TIP_WIDTH_FRACTION * pitch

    helix = Part.makeHelix(pitch, length, base_radius)
    helix.translate(FreeCAD.Vector(0, 0, z0))

    pts = [
        FreeCAD.Vector(base_radius, -base_width / 2.0, 0),
        FreeCAD.Vector(base_radius, base_width / 2.0, 0),
        FreeCAD.Vector(base_radius + thread_height, tip_width / 2.0, 0),
        FreeCAD.Vector(base_radius + thread_height, -tip_width / 2.0, 0),
        FreeCAD.Vector(base_radius, -base_width / 2.0, 0),
    ]
    profile = Part.makePolygon(pts)
    profile.translate(FreeCAD.Vector(0, 0, z0))

    return Part.Wire(helix).makePipeShell([profile], True, True)
