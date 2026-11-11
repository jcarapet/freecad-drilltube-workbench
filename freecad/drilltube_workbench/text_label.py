"""Engraved size-label text for the cap's top face.

Builds glyph outlines via the document-free Part.makeWireString, then
assembles each character's wire(s) into a proper face -- handling glyphs
with an enclosed hole (0, 6, 8, 9, #, Q, ...) by detecting which wire is
the outer boundary and which are holes via bounding-box containment, not
a single sampled point: a centered hole's bounding box sits asymmetrically
inside the outer wire's box, but the outer wire's own bbox-center can
itself fall inside a *centered* hole (e.g. Q, 0, #), which makes a
single-point "is this wire's center inside that face" test see mutual
containment and misclassify both wires. Bounding-box containment avoids
that because the outer wire's box is never contained within its own
(smaller) hole's box, only the reverse.

This also sidesteps Draft.make_shapestring, which needs its own FreeCAD
document: calling it from inside another object's execute() -- even via a
throwaway scratch document -- was observed to corrupt this FreeCAD build's
stdout buffering and ultimately produce invalid shapes for some glyph
combinations. Staying document-free avoids both problems.
"""

import os

import FreeCAD
import Part

_FALLBACK_FONTS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:\\Windows\\Fonts\\arial.ttf",
]

_REFERENCE_SIZE = 5.0


def find_default_font():
    bundled = os.path.join(FreeCAD.getHomePath(), "fonts", "DejaVuSans.ttf")
    candidates = [bundled] + _FALLBACK_FONTS
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise RuntimeError(
        "No usable font found for engraving (checked: {}). "
        "Set the cap's FontFile property to a .ttf file manually.".format(candidates))


def _bbox_contains(outer_bbox, inner_bbox, tol=1e-6):
    return (outer_bbox.XMin - tol <= inner_bbox.XMin and inner_bbox.XMax <= outer_bbox.XMax + tol and
            outer_bbox.YMin - tol <= inner_bbox.YMin and inner_bbox.YMax <= outer_bbox.YMax + tol)


def _glyph_group_to_faces(wires):
    """One character's wires -> one face per disjoint outline, each with
    its enclosed holes (if any) correctly subtracted."""
    wires = [w for w in wires if w.Vertexes]
    if not wires:
        return []  # e.g. a space character

    areas = [Part.Face(w).Area for w in wires]
    bboxes = [w.BoundBox for w in wires]
    n = len(wires)

    # parent[i] = index of the smallest wire that both strictly encloses
    # wire i's bounding box and has a larger area (its direct container).
    parent = [None] * n
    for i in range(n):
        best_j, best_area = None, None
        for j in range(n):
            if i == j:
                continue
            if areas[j] > areas[i] and _bbox_contains(bboxes[j], bboxes[i]):
                if best_area is None or areas[j] < best_area:
                    best_j, best_area = j, areas[j]
        parent[i] = best_j

    faces = []
    for t in (i for i in range(n) if parent[i] is None):
        holes = [wires[i] for i in range(n) if parent[i] == t]
        faces.append(Part.Face([wires[t]] + holes) if holes else Part.Face(wires[t]))
    return faces


def _text_shape(text, font_file, size):
    font_dir, font_name = os.path.split(font_file)
    font_dir = font_dir + os.sep  # makeWireString concatenates dir+file with no separator
    groups = Part.makeWireString(text, font_dir, font_name, size, 0.0)

    faces = []
    for wires in groups:
        faces.extend(_glyph_group_to_faces(wires))
    if not faces:
        raise ValueError("Label text produced no visible geometry: {!r}".format(text))

    return Part.Compound(faces)


def make_engraved_cut(text, font_file, max_width, depth, size_range=(2.0, 8.0)):
    """A solid to subtract from a top face: `text`, centered, scaled to fit
    within `max_width`, extruded downward by `depth` from z=0."""
    min_size, max_size = size_range

    reference = _text_shape(text, font_file, _REFERENCE_SIZE)
    ref_width = reference.BoundBox.XLength

    fitted_size = max_width / ref_width * _REFERENCE_SIZE
    fitted_size = max(min_size, min(max_size, fitted_size))

    shape = reference if fitted_size == _REFERENCE_SIZE else _text_shape(text, font_file, fitted_size)
    bbox = shape.BoundBox
    cx = (bbox.XMin + bbox.XMax) / 2.0
    cy = (bbox.YMin + bbox.YMax) / 2.0
    shape.translate(FreeCAD.Vector(-cx, -cy, -depth))

    return shape.extrude(FreeCAD.Vector(0, 0, depth + 0.05))
