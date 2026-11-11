"""The 'Create Drill Tube' toolbar/menu command."""

import os

import FreeCAD
import FreeCADGui

from . import feature
from .taskpanel import DrillTubeTaskPanel

_ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")


class CreateDrillTubeCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(_ICON_DIR, "CreateDrillTube.svg"),
            "MenuText": "Create Drill Tube",
            "ToolTip": "Create a tube sized to bundle a set of drill bits",
        }

    def IsActive(self):
        return True

    def Activated(self):
        doc = FreeCAD.ActiveDocument or FreeCAD.newDocument()

        def on_accept(params):
            feature.make_drill_tube(doc, **params)
            FreeCADGui.ActiveDocument.ActiveView.fitAll()

        panel = DrillTubeTaskPanel(doc, on_accept)
        FreeCADGui.Control.showDialog(panel)


FreeCADGui.addCommand("CreateDrillTube", CreateDrillTubeCommand())
