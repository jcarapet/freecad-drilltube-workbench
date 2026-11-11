"""Run with: freecadcmd tests/verify_in_freecad.py

End-to-end check that freecad.drilltube_workbench.feature actually builds
valid tube and cap shapes inside a running FreeCAD, for a few representative
parameter sets spanning all four sizing systems, plus the small-tube thread
guard.
"""

import os
import sys

# This freecadcmd build does not reliably flush stdout on exit (observed losing all
# buffered print() output whenever the script exited via sys.exit(), with no indication
# of a crash) -- force line buffering so results are visible regardless.
sys.stdout.reconfigure(line_buffering=True)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import FreeCAD

from freecad.drilltube_workbench import drill_lengths, drill_sizes, feature, packing

CASES = [
    dict(system=drill_sizes.SYSTEM_METRIC, label="6 mm", diameter_mm=6.0, count=10,
         category=drill_lengths.CATEGORY_JOBBER),
    dict(system=drill_sizes.SYSTEM_FRACTIONAL, label='1/4"', diameter_mm=0.25 * 25.4, count=7,
         category=drill_lengths.CATEGORY_STUB),
    dict(system=drill_sizes.SYSTEM_NUMBER, label="#30",
         diameter_mm=drill_sizes.resolve_diameter_mm(drill_sizes.SYSTEM_NUMBER, "#30"), count=3,
         category=drill_lengths.CATEGORY_LONG),
    dict(system=drill_sizes.SYSTEM_LETTER, label="Q",
         diameter_mm=drill_sizes.resolve_diameter_mm(drill_sizes.SYSTEM_LETTER, "Q"), count=1,
         category=drill_lengths.CATEGORY_JOBBER),
]

failures = []
doc = FreeCAD.newDocument("DrillTubeVerify")

for case in CASES:
    tube, cap = feature.make_drill_tube(
        doc,
        bit_diameter_mm=case["diameter_mm"],
        bit_count=case["count"],
        size_system=case["system"],
        size_label=case["label"],
        length_category=case["category"],
    )

    name = "{} x{} ({})".format(case["label"], case["count"], case["category"])

    for part_name, obj in (("tube", tube), ("cap", cap)):
        shape = obj.Shape
        if shape.isNull():
            failures.append("{} {}: shape is null".format(name, part_name))
            continue
        if not shape.isValid():
            failures.append("{} {}: shape is not valid".format(name, part_name))
            continue

    tube_bbox = tube.Shape.BoundBox
    expected_tube_h = tube.BottomThickness.Value + tube.Length.Value
    if abs(tube_bbox.ZLength - expected_tube_h) > 1e-2:
        failures.append("{} tube: bbox Z length {:.3f} != expected {:.3f}".format(
            name, tube_bbox.ZLength, expected_tube_h))

    if tube.BoreDiameter.Value <= 0 or tube.BoreDiameter.Value >= tube.OuterDiameter.Value:
        failures.append("{} tube: bore diameter {:.3f} not sane vs outer {:.3f}".format(
            name, tube.BoreDiameter.Value, tube.OuterDiameter.Value))

    # Cap bore must clear the tube's thread crest (NeckRadius + ThreadHeight) by ThreadClearance.
    thread_crest = tube.NeckRadius.Value + tube.ThreadHeight.Value
    expected_cap_bore_r = thread_crest + cap.ThreadClearance.Value
    actual_cap_bore_r = cap.BoreDiameter.Value / 2.0
    if abs(actual_cap_bore_r - expected_cap_bore_r) > 1e-6:
        failures.append("{} cap: bore radius {:.4f} != expected clearance-fit radius {:.4f}".format(
            name, actual_cap_bore_r, expected_cap_bore_r))

    # The engraved label must have actually removed material from the cap.
    cap_label_cleared = cap.SizeLabel == case["label"]
    if not cap_label_cleared:
        failures.append("{} cap: SizeLabel {!r} != expected {!r}".format(
            name, cap.SizeLabel, case["label"]))
    else:
        # Build the same cap without a label to compare volume.
        bare = doc.addObject("Part::FeaturePython", "DrillTubeCapBare")
        feature.DrillTubeCap(bare)
        for prop in ("NeckRadius", "ThreadLength", "ThreadPitch", "ThreadHeight",
                     "ThreadClearance", "CapWallThickness", "TopThickness"):
            setattr(bare, prop, getattr(cap, prop).Value)
        bare.SizeLabel = ""
        doc.recompute()
        if cap.Shape.Volume >= bare.Shape.Volume:
            failures.append("{} cap: labeled volume {:.2f} not less than unlabeled volume {:.2f} "
                             "(engraving cut had no effect)".format(
                                 name, cap.Shape.Volume, bare.Shape.Volume))
        doc.removeObject(bare.Name)

    print("OK  {}: tube bore={:.3f}mm outer={:.3f}mm length={:.3f}mm | "
          "cap bore={:.3f}mm outer={:.3f}mm volume={:.1f}mm3".format(
              name, tube.BoreDiameter.Value, tube.OuterDiameter.Value, tube.Length.Value,
              cap.BoreDiameter.Value, cap.OuterDiameter.Value, cap.Shape.Volume))

# Small-tube guard: ThreadHeight larger than the tube's own radius must fail to recompute
# (execute() raises ValueError, which FreeCAD surfaces as obj.State containing 'Invalid'
# rather than propagating the exception -- confirmed by a standalone probe against this
# FreeCAD build before relying on it here).
guard_tube = doc.addObject("Part::FeaturePython", "GuardTube")
feature.DrillTube(guard_tube)
guard_tube.BitDiameter = 0.3
guard_tube.BitCount = 1
guard_tube.WallThickness = 0.5
guard_tube.ThreadHeight = 5.0  # absurdly large relative to a ~0.65mm-radius tube
doc.recompute()
if guard_tube.isValid():
    failures.append("small-tube guard: expected recompute to fail (Invalid state), got a valid shape")
if guard_tube.NeckRadius.Value > 0 and guard_tube.NeckRadius.Value >= guard_tube.BoreDiameter.Value / 2.0:
    failures.append("small-tube guard: NeckRadius {:.3f} should be <= bore radius {:.3f}, "
                     "guard condition not actually exercised".format(
                         guard_tube.NeckRadius.Value, guard_tube.BoreDiameter.Value / 2.0))

FreeCAD.closeDocument(doc.Name)

if failures:
    print("\nFAILURES:")
    for f in failures:
        print(" - " + f)
    sys.exit(1)

print("\nAll verification cases passed.")
