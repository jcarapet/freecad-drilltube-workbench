"""Part::FeaturePython objects for a drill-bit bundling tube and its cap.

The tube is a closed-bottom hollow cylinder with a threaded neck at the
top: an outer body fused to a reduced-diameter neck, bore cut through
(starting above the solid bottom), with a helical thread ridge fused onto
the neck (see thread.py). The bore diameter is sized to bundle BitCount
bits of BitDiameter packed together (see packing.py); Length is the usable
internal bore depth, driven by the Stub/Jobber/Long lookup in
drill_lengths.py unless LengthCategory is "Custom".

The cap is a separate object: a cup with a matching thread groove cut into
its bore, and the bit's SizeLabel engraved into its top face (see
text_label.py). Tube and cap are never joined inside FreeCAD -- they are
two solids meant to be sliced and printed separately, then screwed together
after printing.
"""

import os

import FreeCAD
import Part

from . import drill_lengths
from . import drill_sizes
from . import packing
from . import text_label
from . import thread

LENGTH_CATEGORIES = drill_lengths.CATEGORIES + ["Custom"]

# ~3 perimeters at a common 0.4mm FDM nozzle. Below this we only warn --
# the user's explicit number is still honored.
FDM_MIN_WALL_MM = 1.2

_ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")


def _warn_if_thin(label, value_mm):
    if value_mm < FDM_MIN_WALL_MM:
        FreeCAD.Console.PrintWarning(
            "DrillTube: {} is {:.2f} mm, below the ~{:.1f} mm recommended minimum "
            "for reliable FDM printing (3 perimeters at a 0.4 mm nozzle).\n".format(
                label, value_mm, FDM_MIN_WALL_MM))


class DrillTube:
    def __init__(self, obj):
        obj.Proxy = self
        self._add_properties(obj)

    def _add_properties(self, obj):
        obj.addProperty("App::PropertyLength", "BitDiameter", "DrillTube",
                         "Diameter of a single drill bit").BitDiameter = 6.0
        obj.addProperty("App::PropertyInteger", "BitCount", "DrillTube",
                         "Number of bits bundled in this tube").BitCount = 1
        obj.addProperty("App::PropertyEnumeration", "SizeSystem", "DrillTube",
                         "Sizing system used to pick BitDiameter")
        obj.SizeSystem = drill_sizes.SYSTEMS
        obj.SizeSystem = drill_sizes.SYSTEM_METRIC
        obj.addProperty("App::PropertyString", "SizeLabel", "DrillTube",
                         "Informational label of the selected bit size, e.g. '#30' or '1/4\"'")
        obj.SizeLabel = ""
        obj.addProperty("App::PropertyEnumeration", "LengthCategory", "DrillTube",
                         "Stub / Jobber / Long, or Custom to set Length manually")
        obj.LengthCategory = LENGTH_CATEGORIES
        obj.LengthCategory = drill_lengths.CATEGORY_JOBBER
        obj.addProperty("App::PropertyLength", "Length", "DrillTube",
                         "Usable internal bore depth. Auto-set from LengthCategory unless Custom.")
        obj.Length = drill_lengths.length_for(6.0, drill_lengths.CATEGORY_JOBBER)
        obj.addProperty("App::PropertyLength", "WallThickness", "DrillTube",
                         "Wall thickness around the bundled bits").WallThickness = 1.5
        obj.addProperty("App::PropertyLength", "BitClearance", "DrillTube",
                         "Extra radial slack per bit inside the bore").BitClearance = 0.3
        obj.addProperty("App::PropertyLength", "BottomThickness", "DrillTube",
                         "Solid base thickness below the bore").BottomThickness = 2.0
        obj.addProperty("App::PropertyLength", "ThreadLength", "DrillTube",
                         "Axial length of the threaded neck at the top").ThreadLength = 10.0
        obj.addProperty("App::PropertyLength", "ThreadPitch", "DrillTube",
                         "Thread pitch (axial distance per turn)").ThreadPitch = 3.0
        obj.addProperty("App::PropertyLength", "ThreadHeight", "DrillTube",
                         "Radial depth of the thread").ThreadHeight = 1.0
        obj.addProperty("App::PropertyLength", "BoreDiameter", "DrillTube",
                         "Computed inner bore diameter")
        obj.setEditorMode("BoreDiameter", 1)  # read-only
        obj.addProperty("App::PropertyLength", "OuterDiameter", "DrillTube",
                         "Computed outer tube diameter")
        obj.setEditorMode("OuterDiameter", 1)  # read-only
        obj.addProperty("App::PropertyLength", "NeckRadius", "DrillTube",
                         "Computed radius of the threaded neck (crest flush with OuterDiameter)")
        obj.setEditorMode("NeckRadius", 1)  # read-only
        self._recompute_derived(obj)

    def onDocumentRestored(self, obj):
        self._add_properties_if_missing(obj)

    def _add_properties_if_missing(self, obj):
        if not hasattr(obj, "NeckRadius"):
            self._add_properties(obj)

    def _recompute_derived(self, obj):
        bore = packing.bore_diameter(obj.BitDiameter.Value, max(1, obj.BitCount), obj.BitClearance.Value)
        obj.BoreDiameter = bore
        outer = bore + 2 * obj.WallThickness.Value
        obj.OuterDiameter = outer
        obj.NeckRadius = outer / 2.0 - obj.ThreadHeight.Value

    def onChanged(self, obj, prop):
        if prop in ("BitDiameter", "BitCount", "BitClearance", "WallThickness", "ThreadHeight"):
            if hasattr(obj, "NeckRadius"):
                self._recompute_derived(obj)
        if prop in ("BitDiameter", "LengthCategory") and hasattr(obj, "Length"):
            if obj.LengthCategory != "Custom":
                obj.Length = drill_lengths.length_for(obj.BitDiameter.Value, obj.LengthCategory)

    def execute(self, obj):
        if obj.BitCount < 1:
            raise ValueError("BitCount must be >= 1")
        length = obj.Length.Value
        if length <= 0:
            raise ValueError("Length must be > 0")

        outer_r = obj.OuterDiameter.Value / 2.0
        bore_r = obj.BoreDiameter.Value / 2.0
        bottom = obj.BottomThickness.Value
        thread_length = obj.ThreadLength.Value
        thread_height = obj.ThreadHeight.Value
        neck_r = obj.NeckRadius.Value

        if neck_r <= 0 or neck_r < bore_r:
            raise ValueError(
                "ThreadHeight ({:.2f} mm) is too large for this tube's wall "
                "(OuterDiameter {:.2f} mm, BoreDiameter {:.2f} mm): the threaded neck "
                "would be thinner than the bore, or disappear entirely. Reduce ThreadHeight "
                "or increase WallThickness.".format(thread_height, obj.OuterDiameter.Value, obj.BoreDiameter.Value))

        _warn_if_thin("WallThickness", obj.WallThickness.Value)
        _warn_if_thin("BottomThickness", bottom)

        overall_h = bottom + length
        body_h = overall_h - thread_length

        body = Part.makeCylinder(outer_r, body_h)
        neck = Part.makeCylinder(neck_r, thread_length)
        neck.translate(FreeCAD.Vector(0, 0, body_h))
        blank = body.fuse(neck)

        bore = Part.makeCylinder(bore_r, length)
        bore.translate(FreeCAD.Vector(0, 0, bottom))
        cut = blank.cut(bore)

        # Embed the ridge's base slightly into the neck rather than leaving it exactly
        # tangent to the neck's surface: fusing two shapes that only touch (zero volumetric
        # overlap) is an OCC degenerate case that produces an invalid "wire imbrication" for
        # some tube sizes. Growing thread_height by the same amount keeps the crest flush
        # with OuterDiameter as designed.
        ridge = thread.make_thread_ridge(neck_r - thread.EMBED_MM, obj.ThreadPitch.Value, thread_length,
                                          thread_height + thread.EMBED_MM, z0=body_h)
        obj.Shape = cut.fuse(ridge)


class DrillTubeCap:
    def __init__(self, obj):
        obj.Proxy = self
        self._add_properties(obj)

    def _add_properties(self, obj):
        obj.addProperty("App::PropertyLength", "NeckRadius", "DrillTubeCap",
                         "Radius of the tube's threaded neck this cap fits over").NeckRadius = 10.0
        obj.addProperty("App::PropertyLength", "ThreadLength", "DrillTubeCap",
                         "Axial length of the threaded engagement").ThreadLength = 10.0
        obj.addProperty("App::PropertyLength", "ThreadPitch", "DrillTubeCap",
                         "Thread pitch (must match the tube)").ThreadPitch = 3.0
        obj.addProperty("App::PropertyLength", "ThreadHeight", "DrillTubeCap",
                         "Radial depth of the thread (must match the tube)").ThreadHeight = 1.0
        obj.addProperty("App::PropertyLength", "ThreadClearance", "DrillTubeCap",
                         "Radial slack between the cap's thread groove and the tube's thread ridge"
                         ).ThreadClearance = 0.3
        obj.addProperty("App::PropertyLength", "CapWallThickness", "DrillTubeCap",
                         "Wall thickness of the cap's side skirt").CapWallThickness = 2.0
        obj.addProperty("App::PropertyLength", "TopThickness", "DrillTubeCap",
                         "Thickness of the solid top disc").TopThickness = 3.0
        obj.addProperty("App::PropertyString", "SizeLabel", "DrillTubeCap",
                         "Text engraved on the cap's top face").SizeLabel = ""
        obj.addProperty("App::PropertyString", "FontFile", "DrillTubeCap",
                         "TrueType font used to engrave SizeLabel")
        obj.FontFile = text_label.find_default_font()
        obj.addProperty("App::PropertyLength", "LabelDepth", "DrillTubeCap",
                         "How deep the label is engraved").LabelDepth = 0.6
        obj.addProperty("App::PropertyLength", "BoreDiameter", "DrillTubeCap",
                         "Computed inner bore diameter (clears the tube's thread crest)")
        obj.setEditorMode("BoreDiameter", 1)  # read-only
        obj.addProperty("App::PropertyLength", "OuterDiameter", "DrillTubeCap",
                         "Computed outer cap diameter")
        obj.setEditorMode("OuterDiameter", 1)  # read-only
        self._recompute_derived(obj)

    def onDocumentRestored(self, obj):
        if not hasattr(obj, "OuterDiameter"):
            self._add_properties(obj)

    def _recompute_derived(self, obj):
        bore = 2 * (obj.NeckRadius.Value + obj.ThreadHeight.Value + obj.ThreadClearance.Value)
        obj.BoreDiameter = bore
        obj.OuterDiameter = bore + 2 * obj.CapWallThickness.Value

    def onChanged(self, obj, prop):
        if prop in ("NeckRadius", "ThreadHeight", "ThreadClearance", "CapWallThickness"):
            if hasattr(obj, "OuterDiameter"):
                self._recompute_derived(obj)

    def execute(self, obj):
        thread_length = obj.ThreadLength.Value
        top = obj.TopThickness.Value
        if thread_length <= 0 or top <= 0:
            raise ValueError("ThreadLength and TopThickness must be > 0")

        cap_bore_r = obj.BoreDiameter.Value / 2.0
        cap_outer_r = obj.OuterDiameter.Value / 2.0

        _warn_if_thin("CapWallThickness", obj.CapWallThickness.Value)
        _warn_if_thin("TopThickness", top)

        cap_h = thread_length + top
        blank = Part.makeCylinder(cap_outer_r, cap_h)
        bore = Part.makeCylinder(cap_bore_r, thread_length)
        body = blank.cut(bore)

        groove = thread.make_thread_ridge(obj.NeckRadius.Value + obj.ThreadClearance.Value,
                                           obj.ThreadPitch.Value, thread_length,
                                           obj.ThreadHeight.Value, z0=0.0)
        shape = body.cut(groove)

        if obj.SizeLabel:
            max_width = cap_outer_r * 2 * 0.8
            cut_solid = text_label.make_engraved_cut(
                obj.SizeLabel, obj.FontFile, max_width, obj.LabelDepth.Value)
            cut_solid.translate(FreeCAD.Vector(0, 0, cap_h))
            shape = shape.cut(cut_solid)

        obj.Shape = shape


class ViewProviderDrillTube:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return os.path.join(_ICON_DIR, "CreateDrillTube.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class ViewProviderDrillTubeCap(ViewProviderDrillTube):
    pass


def make_drill_tube(doc, bit_diameter_mm, bit_count, size_system=drill_sizes.SYSTEM_METRIC,
                     size_label="", length_category=drill_lengths.CATEGORY_JOBBER,
                     wall_thickness_mm=1.5, bit_clearance_mm=0.3, length_mm=None,
                     bottom_thickness_mm=2.0, thread_length_mm=10.0, thread_pitch_mm=3.0,
                     thread_height_mm=1.0, thread_clearance_mm=0.3, cap_wall_thickness_mm=2.0,
                     cap_top_thickness_mm=3.0):
    """Create and recompute a DrillTube + matching DrillTubeCap, grouped together."""
    tube = doc.addObject("Part::FeaturePython", "DrillTube")
    DrillTube(tube)
    if tube.ViewObject is not None:
        ViewProviderDrillTube(tube.ViewObject)

    tube.SizeSystem = size_system
    tube.SizeLabel = size_label
    tube.BitDiameter = bit_diameter_mm
    tube.BitCount = bit_count
    tube.WallThickness = wall_thickness_mm
    tube.BitClearance = bit_clearance_mm
    tube.BottomThickness = bottom_thickness_mm
    tube.ThreadLength = thread_length_mm
    tube.ThreadPitch = thread_pitch_mm
    tube.ThreadHeight = thread_height_mm
    tube.LengthCategory = length_category
    if length_category == "Custom" and length_mm is not None:
        tube.Length = length_mm
    else:
        tube.Length = drill_lengths.length_for(bit_diameter_mm, length_category)

    doc.recompute()

    cap = doc.addObject("Part::FeaturePython", "DrillTubeCap")
    DrillTubeCap(cap)
    if cap.ViewObject is not None:
        ViewProviderDrillTubeCap(cap.ViewObject)

    cap.NeckRadius = tube.NeckRadius.Value
    cap.ThreadLength = thread_length_mm
    cap.ThreadPitch = thread_pitch_mm
    cap.ThreadHeight = thread_height_mm
    cap.ThreadClearance = thread_clearance_mm
    cap.CapWallThickness = cap_wall_thickness_mm
    cap.TopThickness = cap_top_thickness_mm
    cap.SizeLabel = size_label

    doc.recompute()

    cap.Placement = FreeCAD.Placement(FreeCAD.Vector(tube.OuterDiameter.Value * 2.5, 0, 0),
                                       FreeCAD.Rotation())

    group = doc.addObject("App::DocumentObjectGroup", "DrillTube_Group")
    group.addObject(tube)
    group.addObject(cap)

    doc.recompute()
    return tube, cap
