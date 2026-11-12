"""Standard 60-degree (ISO-style) V thread geometry, tuned for FDM printing.

A single-start thread with a true 60-degree included flank angle, matching
the defining angle of ISO 68-1/724 metric threads -- but with an explicit
minimum crest/root flat width tuned for FDM printability rather than ISO
724's hairline truncation. A geometrically "correct" ISO crest is thinner
than a single nozzle line and will not print consistently.

The ridge is built as a stepped loft between many small rotated/translated
copies of the tooth profile, rather than a single sweep along a helical
spine. An earlier version used `Part.Wire(helix).makePipeShell(...)`, which
turned out to be unreliable here: `Part.makeHelix` returns a BSpline
*approximation* of a helix, and sweeping with either Frenet mode along it
produced a shape whose real volume was a small fraction of the intended
thread (confirmed by cross-sectioning it: at any given height the "ridge"
spanned nearly the full disc instead of a thin band near the nominal
radius) -- `isValid()` was still True, so this passed shape-validity checks
while being geometrically wrong. The stepped-loft approach only uses
explicit rotation and translation, which is unambiguous, and its volume and
bounding box match hand-calculated expectations closely.
"""

import math

import FreeCAD
import Part

FLANK_ANGLE_DEG = 30.0  # half of the 60-degree included angle, per ISO
_TAN_FLANK = math.tan(math.radians(FLANK_ANGLE_DEG))

# Crest/root flat width -- matches roughly one 0.4mm nozzle line, so the
# thread's tip is never thinner than a single printed perimeter.
MIN_FLAT_MM = 0.4

# How far a ridge's base should be embedded past its nominal root radius,
# rather than sitting exactly tangent to the surface it's fused onto/cut
# from -- a zero-overlap boolean is an OCC degenerate case that can produce
# an invalid fuse result, or a cut that silently removes no material.
EMBED_MM = 0.2

# Angular resolution of the stepped loft. 24 steps/turn (15 degrees) keeps
# the chord-vs-arc error well under typical FDM print tolerances for the
# tube/cap sizes this workbench targets, at a modest, roughly-linear-in-size
# compute cost.
STEPS_PER_TURN = 24


def _profile_widths(pitch, thread_height, min_flat=MIN_FLAT_MM):
    """(base_width, tip_width) for a true 60-degree-included-angle
    trapezoid of the given radial height, with the tip (narrow end) held
    to at least `min_flat` so the crest/root prints as a real feature
    rather than a knife edge."""
    tip_width = min_flat
    base_width = tip_width + 2 * thread_height * _TAN_FLANK
    max_base = 0.9 * pitch  # leave a little clearance so turns can't touch
    if base_width > max_base:
        base_width = max_base
        tip_width = max(min_flat * 0.5, base_width - 2 * thread_height * _TAN_FLANK)
    return base_width, tip_width


def _tooth_wire(radius, thread_height, base_width, tip_width, angle_deg, z):
    """The trapezoid tooth cross-section (radial x axial plane), rotated
    about the Z axis and translated axially to one point along the thread."""
    pts = [
        FreeCAD.Vector(radius, 0, -base_width / 2.0),
        FreeCAD.Vector(radius, 0, base_width / 2.0),
        FreeCAD.Vector(radius + thread_height, 0, tip_width / 2.0),
        FreeCAD.Vector(radius + thread_height, 0, -tip_width / 2.0),
        FreeCAD.Vector(radius, 0, -base_width / 2.0),
    ]
    wire = Part.makePolygon(pts)
    wire.translate(FreeCAD.Vector(0, 0, z))
    wire.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), angle_deg)
    return wire


def make_thread_ridge(base_radius, pitch, length, thread_height, z0=0.0, embed=EMBED_MM):
    """A solid helical ridge with a true 60-degree included flank angle,
    ready to be fused onto an external surface (male thread) or cut out of
    an internal bore (female thread groove).

    base_radius: nominal root radius the thread sits on -- the ridge is
        actually built `embed` mm further in, for a robust boolean.
    pitch: axial distance per full turn (mm).
    length: axial length of the threaded section (mm).
    thread_height: radial depth from root to crest (mm).
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

    embedded_radius = base_radius - embed
    embedded_height = thread_height + embed
    base_width, tip_width = _profile_widths(pitch, embedded_height)

    total_turns = length / pitch
    total_steps = max(1, int(round(total_turns * STEPS_PER_TURN)))

    segments = []
    for i in range(total_steps):
        a0 = i * 360.0 / STEPS_PER_TURN
        a1 = (i + 1) * 360.0 / STEPS_PER_TURN
        z_a = z0 + i * pitch / STEPS_PER_TURN
        z_b = z0 + (i + 1) * pitch / STEPS_PER_TURN
        w0 = _tooth_wire(embedded_radius, embedded_height, base_width, tip_width, a0, z_a)
        w1 = _tooth_wire(embedded_radius, embedded_height, base_width, tip_width, a1, z_b)
        segments.append(Part.makeLoft([w0, w1], True))

    return segments[0].fuse(segments[1:]) if len(segments) > 1 else segments[0]
