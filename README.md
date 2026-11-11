# Drill Tube Workbench

A FreeCAD workbench that generates a closed-bottom tube with a screw-on cap,
sized to bundle a chosen number of same-size drill bits together in
cross-section — like the plastic sleeve a multi-pack of bits comes in, but
with a reusable threaded lid instead of a snap-shut cap. Pick a drill size,
how many bits go in the tube, and a standard length class (Stub / Jobber /
Long); the workbench works out the bore diameter, outer diameter, tube
length, and a matching cap with the bit size engraved on top — and both
parts are designed to actually print on an FDM printer (see
[FDM printing notes](#fdm-printing-notes) below).

Each "Create Drill Tube" click produces **two separate solids** — a tube and
a cap — grouped together in the tree view but laid out side by side in 3D
space. They are never joined inside FreeCAD: they're two parts meant to be
exported as separate STLs, printed separately, and screwed together after
printing.

## How it decides the geometry

- **Bore diameter**: the smallest circle that can fit N bits of the chosen
  diameter packed together (plus a bit of slack), using the standard
  "circle packing in a circle" ratios (`freecad/drilltube_workbench/packing.py`). More
  bits → a proportionally wider bore, not a linear one — 7 bits only need
  3x the diameter of 1 bit, not 7x.
- **Outer diameter**: bore diameter + 2x wall thickness.
- **Length**: the *usable internal bore depth* — looked up from the bit
  diameter and the Stub/Jobber/Long class you pick
  (`freecad/drilltube_workbench/drill_lengths.py` / `freecad/drilltube_workbench/drill_lengths.json`).
  The tube's actual printed height is `Length + BottomThickness`, since the
  bottom is solid (see below) — the bit's full length still fits in the
  cavity either way.
- **Thread**: a single-start, coarse trapezoidal thread (see
  [FDM printing notes](#fdm-printing-notes)) on a reduced-diameter "neck" at
  the top of the tube, flush with the tube's outer diameter at the thread
  crest. The cap has a matching thread groove cut into its bore, offset
  radially by `ThreadClearance` for a printable fit, plus the bit size
  engraved into its top face.

### Important caveat on the length table

The jobber/stub/long lengths this workbench ships with are **representative
calibration points for 3D modeling and clearance checks — not an exact
reproduction of any manufacturer's catalog.** Standard tables vary slightly
between sources, and getting every value precise from memory isn't something
to take on faith for a manufacturing decision. If exact lengths matter:

- Edit `freecad/drilltube_workbench/drill_lengths.json` with your supplier's real
  numbers (it's a simple diameter-mm → length-mm table, plus the stub/long
  ratios applied on top of jobber length), or
- After creating a tube, just type the correct value into its `Length`
  property in the Data tab (switch `LengthCategory` to `Custom` first so it
  stops being overwritten automatically).

The number-gauge (#1–#80) and letter-gauge (A–Z) *diameters* in
`freecad/drilltube_workbench/drill_sizes.py` are the standard, universally published
wire-gauge drill chart values — still worth double-checking against a
caliper or your own chart before cutting metal, as general good practice.

## FDM printing notes

**Thread design.** The tube/cap thread is a coarse, single-start trapezoidal
profile (pitch 3 mm by default, `ThreadLength`/`ThreadPitch`/`ThreadHeight`
properties on the tube) rather than a fine ISO metric thread — fine threads
are notoriously unreliable straight off an FDM printer. `ThreadClearance`
(on the cap, default 0.3 mm radial) is the knob to loosen or tighten the fit:
how tight a given clearance prints depends on your printer, nozzle, and
filament, so **print one small test tube+cap pair first** and adjust
`ThreadClearance` before generating a whole batch.

**Print orientation.**
- The tube prints **closed-bottom-down**: the solid base sits flat on the
  bed, no supports needed.
- The cap prints **opening-down, engraved top face up**. This keeps the
  labeled face away from the build plate (bed contact ruins fine engraved
  detail) without hurting the thread's printability — flipping which face
  touches the bed doesn't change the thread helix's own overhang
  characteristics, only which surface gets the bed's finish.

**Minimum wall thickness.** `WallThickness`, `BottomThickness`,
`CapWallThickness`, and `TopThickness` default to values at or above ~1.2 mm
(3 perimeters at a common 0.4 mm nozzle). The workbench will print a
*warning* to FreeCAD's Report View if you set one thinner than that — it
won't block you, since thin walls might be fine for your printer/use case,
but it's worth noticing.

**Very small tubes.** If `ThreadHeight` ends up larger than the tube's own
wall (common if you shrink `WallThickness` a lot for a single tiny bit),
the threaded neck has nowhere to go and the tube will fail to recompute with
a clear error telling you to reduce `ThreadHeight` or increase
`WallThickness`.

## Installation

1. Locate your FreeCAD `Mod` folder. **FreeCAD 1.0+ uses a version-specific
   path** — check this one first, since an older unversioned `Mod/` folder
   may also exist from a previous install and won't actually be scanned:
   - macOS: `~/Library/Application Support/FreeCAD/v1-1/Mod/` (adjust
     `v1-1` to match your installed version, e.g. `v1-0`)
   - Linux: `~/.local/share/FreeCAD/v1-1/Mod/`
   - Windows: `%APPDATA%\FreeCAD\v1-1\Mod\`

   If none of those exist, fall back to the plain `Mod/` folder (no version
   segment) at the same location — older FreeCAD versions use that instead.
2. **Copy** (not symlink — FreeCAD's addon scanner does not follow symlinked
   Mod subfolders, confirmed on FreeCAD 1.1) this entire
   `freecad-drilltube-workbench` folder into that `Mod` directory. If you
   edit the source afterward, re-copy it to pick up the changes.
3. Restart FreeCAD (a full quit, not just closing the document window —
   workbenches are only discovered at startup). The **Drill Tube** workbench
   will appear in the workbench dropdown.

If it still doesn't appear, check `freecad/drilltube_workbench/` exists
inside the installed copy with lowercase `init_gui.py` and `init.py` files —
FreeCAD 1.0+'s addon scanner looks for that structure (driven by
`package.xml`'s `<classname>`/`<subdirectory>`), not a top-level capitalized
`InitGui.py`.

Alternatively, publish this folder as a git repository and add it in
FreeCAD's Addon Manager via *Developer tools → Custom repository*.

Before publishing/distributing, fill in your own details in `package.xml`
(`<maintainer>`, `<license>`, `<url>`).

## Usage

1. Switch the workbench dropdown (top toolbar) to **Drill Tube**.
2. Click the **Create Drill Tube** toolbar button.
3. In the dialog:
   - **Size system**: Metric, Fractional, Number, Letter, or Custom.
   - **Size**: pick a value from the dropdown (or enter a custom mm diameter
     if you chose Custom).
   - **Number of drill bits**: how many bits this tube bundles.
   - **Length**: Stub / Jobber / Long, or Custom to type your own length.
   - **Wall thickness** / **Bit clearance**: tune how tight the bit bundle
     fit is.
   - **Bottom thickness**: solid base thickness below the bore.
   - **Thread length / pitch / height / fit clearance**: the screw thread
     geometry shared between the tube and cap — see
     [FDM printing notes](#fdm-printing-notes) for sane defaults.
   - **Cap wall thickness / top thickness**: the cap's skirt wall and the
     solid disc on top that carries the engraved label.
   - The **Preview** line updates live with the resulting bore/outer
     diameter and length.
4. Click **OK** to create the tube and its matching cap (grouped together
   in the tree view, laid out side by side in 3D space, ready to export as
   two separate STLs).
5. After creation, you can still tweak any of these as properties in the
   **Data** tab (select the tube or cap in the tree view) and the geometry
   recomputes — e.g. nudge `BitClearance`, loosen `ThreadClearance` on the
   cap if a test print fits too tight, or switch the tube's `LengthCategory`
   to `Custom` and set an exact `Length`. Note the tube and cap don't stay
   automatically in sync after creation — if you change the tube's thread
   geometry afterward, update the matching properties on the cap too.

## Running the tests

The sizing/length/packing math is pure Python and can be tested without
FreeCAD:

```
python3 tests/test_packing.py
python3 tests/test_drill_sizes.py
python3 tests/test_drill_lengths.py
```

An end-to-end check that actually builds geometry inside FreeCAD (headless):

```
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd tests/verify_in_freecad.py
```

(adjust the `freecadcmd` path for your platform/install).
