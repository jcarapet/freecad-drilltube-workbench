"""Registers the Drill Tube workbench with the FreeCAD GUI.

Filename and location (lowercase, inside freecad/drilltube_workbench/) are
dictated by FreeCAD's modern addon convention: the Mod-folder scanner
discovers workbenches via package.xml's <classname>, pointed at a package
under freecad/<name>/ containing init_gui.py (GUI mode) and init.py
(console mode) -- a top-level capitalized InitGui.py is not picked up by
this FreeCAD build.
"""

import os

import FreeCADGui

_ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")


class DrillTubeWorkbench(FreeCADGui.Workbench):
    MenuText = "Drill Tube"
    ToolTip = "Generate tubes sized to bundle drill bits"
    Icon = os.path.join(_ICON_DIR, "DrillTubeWorkbench.svg")

    def Initialize(self):
        from . import command  # noqa: F401  (registers the command)

        self.commands = ["CreateDrillTube"]
        self.appendToolbar("Drill Tube", self.commands)
        self.appendMenu("Drill Tube", self.commands)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(DrillTubeWorkbench())
