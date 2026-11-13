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

import math

import FreeCAD
import Part

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
    # Regression case: #29 x12 printed with no visible/printed cap threads and a loose
    # fit on a real printer (Bambu H2S) -- traced to the cap's plain bore being cut at
    # the thread's crest radius instead of its root, making the groove cut a near no-op.
    dict(system=drill_sizes.SYSTEM_NUMBER, label="#29",
         diameter_mm=drill_sizes.resolve_diameter_mm(drill_sizes.SYSTEM_NUMBER, "#29"), count=12,
         category=drill_lengths.CATEGORY_JOBBER),
    # Regression case: bit counts >= 20 fall outside packing.py's hand-tabulated ratios
    # (1..19) and used an asymptotic formula with a spurious factor of 2, producing a
    # bore diameter roughly double what it should have been -- reported as "diameter at
    # 20 bits is significantly larger than at 19". This confirms the full tube+cap
    # pipeline still builds correctly at a count past that boundary, on top of
    # test_packing.py's direct check of the corrected formula itself.
    dict(system=drill_sizes.SYSTEM_NUMBER, label="#4",
         diameter_mm=drill_sizes.resolve_diameter_mm(drill_sizes.SYSTEM_NUMBER, "#4"), count=20,
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
    # The thread's own end tooth legitimately pokes past the nominal top by roughly
    # half its axial width (same as a real screw's first/last partial thread) -- allow
    # a generous margin for that rather than requiring an exact match.
    max_protrusion = 2.5
    if not (0 <= tube_bbox.ZLength - expected_tube_h <= max_protrusion):
        failures.append("{} tube: bbox Z length {:.3f} not within [{:.3f}, {:.3f}] of expected {:.3f}".format(
            name, tube_bbox.ZLength, expected_tube_h, expected_tube_h + max_protrusion, expected_tube_h))

    if tube.BoreDiameter.Value <= 0 or tube.BoreDiameter.Value >= tube.OuterDiameter.Value:
        failures.append("{} tube: bore diameter {:.3f} not sane vs outer {:.3f}".format(
            name, tube.BoreDiameter.Value, tube.OuterDiameter.Value))

    # The cap's plain bore (before the groove is cut) must stop at the thread's ROOT
    # (NeckRadius + ThreadClearance), not its crest -- a bore cut to the crest already
    # removes all the material the groove cut is supposed to carve out, which is exactly
    # the bug behind the #29 x12 regression case above (no real cap threads, loose fit).
    expected_root_r = tube.NeckRadius.Value + cap.ThreadClearance.Value
    actual_root_r = cap.BoreDiameter.Value / 2.0
    if abs(actual_root_r - expected_root_r) > 1e-6:
        failures.append("{} cap: plain-bore radius {:.4f} != expected thread-root radius {:.4f}".format(
            name, actual_root_r, expected_root_r))

    # The groove cut must remove a *substantial* fraction of the root-to-crest shell --
    # not ~0% (the original bug: bore already at the crest, groove cut was a no-op) and
    # not ~100% (would mean no actual thread "fingers" survive to mesh with the tube).
    crest_r = expected_root_r + cap.ThreadHeight.Value
    shell_volume = math.pi * (crest_r ** 2 - actual_root_r ** 2) * cap.ThreadLength.Value
    plain_cup = Part.makeCylinder(cap.OuterDiameter.Value / 2.0, cap.ThreadLength.Value + cap.TopThickness.Value)
    plain_cup = plain_cup.cut(Part.makeCylinder(actual_root_r, cap.ThreadLength.Value))
    # Rebuild the cap's own shape without the label or knurling, to isolate the groove's
    # effect cleanly from those separately-checked features (knurling in particular adds
    # material on top of `plain_cup`'s own baseline, which would otherwise make the groove
    # look like it removed far less than it actually did).
    original_label = cap.SizeLabel
    original_knurl = cap.KnurlEnabled
    cap.SizeLabel = ""
    cap.KnurlEnabled = False
    doc.recompute()
    groove_removed = plain_cup.Volume - cap.Shape.Volume
    cap.SizeLabel = original_label
    cap.KnurlEnabled = original_knurl
    doc.recompute()
    removed_fraction = groove_removed / shell_volume if shell_volume > 0 else 0
    if not (0.15 <= removed_fraction <= 0.9):
        failures.append(
            "{} cap: thread groove removed {:.1f}% of the root-to-crest shell volume "
            "({:.2f} of {:.2f} mm3) -- expected roughly 15-90%, got something that smells "
            "like a no-op cut or a fully-cleared shell".format(
                name, removed_fraction * 100, groove_removed, shell_volume))

    # Knurling must actually add material and stay correctly bounded -- the latter
    # specifically guards against the kind of "looks fine, isValid()==True, but the real
    # geometry ballooned/smeared" bug the helical thread profile had before being rewritten.
    # Use XLength/YLength (extent), not XMin/XMax directly -- cap.Shape.BoundBox reflects
    # the cap's own Placement (it's laid out beside the tube for printing), so absolute
    # coordinates are offset from the origin; the *size* of the bbox is translation-invariant.
    cap_bbox = cap.Shape.BoundBox
    expected_knurled_diameter = cap.OuterDiameter.Value + 2 * cap.KnurlDepth.Value
    max_extent = max(cap_bbox.XLength, cap_bbox.YLength)
    if cap.KnurlEnabled and not (expected_knurled_diameter - 1.0 <= max_extent <= expected_knurled_diameter + 1.0):
        failures.append(
            "{} cap: knurled bbox extent {:.3f} not within 1mm of expected diameter {:.3f} "
            "(KnurlDepth={:.2f}) -- geometry may have ballooned".format(
                name, max_extent, expected_knurled_diameter, cap.KnurlDepth.Value))

    unknurled = doc.addObject("Part::FeaturePython", "DrillTubeCapUnknurled")
    feature.DrillTubeCap(unknurled)
    for prop in ("NeckRadius", "ThreadLength", "ThreadPitch", "ThreadHeight",
                 "ThreadClearance", "CapWallThickness", "TopThickness"):
        setattr(unknurled, prop, getattr(cap, prop).Value)
    unknurled.KnurlEnabled = False
    unknurled.SizeLabel = ""
    doc.recompute()
    original_label2 = cap.SizeLabel
    cap.SizeLabel = ""
    doc.recompute()
    if cap.KnurlEnabled and cap.Shape.Volume <= unknurled.Shape.Volume:
        failures.append("{} cap: knurled volume {:.2f} not greater than unknurled volume {:.2f} "
                         "(knurling had no effect)".format(name, cap.Shape.Volume, unknurled.Shape.Volume))
    cap.SizeLabel = original_label2
    doc.recompute()
    doc.removeObject(unknurled.Name)

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
