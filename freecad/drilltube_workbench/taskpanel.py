"""Task panel for entering drill-tube parameters before creation."""

from PySide import QtCore, QtGui

from . import drill_lengths
from . import drill_sizes


class DrillTubeTaskPanel:
    def __init__(self, doc, on_accept):
        self.doc = doc
        self.on_accept = on_accept
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Create Drill Tube")
        self._build_ui()
        self._on_system_changed(self.system_combo.currentText())

    def _build_ui(self):
        layout = QtGui.QFormLayout(self.form)

        self.system_combo = QtGui.QComboBox()
        self.system_combo.addItems(drill_sizes.SYSTEMS)
        self.system_combo.currentTextChanged.connect(self._on_system_changed)
        layout.addRow("Size system", self.system_combo)

        self.size_combo = QtGui.QComboBox()
        layout.addRow("Size", self.size_combo)

        self.custom_diameter = QtGui.QDoubleSpinBox()
        self.custom_diameter.setDecimals(3)
        self.custom_diameter.setRange(0.1, 500.0)
        self.custom_diameter.setSuffix(" mm")
        self.custom_diameter.setValue(6.0)
        layout.addRow("Custom diameter", self.custom_diameter)

        self.bit_count = QtGui.QSpinBox()
        self.bit_count.setRange(1, 500)
        self.bit_count.setValue(1)
        layout.addRow("Number of drill bits", self.bit_count)

        length_box = QtGui.QHBoxLayout()
        self.length_buttons = QtGui.QButtonGroup(self.form)
        for i, category in enumerate(drill_lengths.CATEGORIES):
            btn = QtGui.QRadioButton(category)
            if category == drill_lengths.CATEGORY_JOBBER:
                btn.setChecked(True)
            self.length_buttons.addButton(btn, i)
            length_box.addWidget(btn)
        self.custom_length_btn = QtGui.QRadioButton("Custom")
        self.length_buttons.addButton(self.custom_length_btn, len(drill_lengths.CATEGORIES))
        length_box.addWidget(self.custom_length_btn)
        layout.addRow("Length", length_box)

        self.custom_length = QtGui.QDoubleSpinBox()
        self.custom_length.setDecimals(2)
        self.custom_length.setRange(1.0, 2000.0)
        self.custom_length.setSuffix(" mm")
        self.custom_length.setEnabled(False)
        self.custom_length_btn.toggled.connect(self.custom_length.setEnabled)
        layout.addRow("Custom length value", self.custom_length)

        self.wall_thickness = QtGui.QDoubleSpinBox()
        self.wall_thickness.setDecimals(2)
        self.wall_thickness.setRange(0.1, 50.0)
        self.wall_thickness.setSuffix(" mm")
        self.wall_thickness.setValue(1.5)
        layout.addRow("Wall thickness", self.wall_thickness)

        self.bit_clearance = QtGui.QDoubleSpinBox()
        self.bit_clearance.setDecimals(2)
        self.bit_clearance.setRange(0.0, 10.0)
        self.bit_clearance.setSuffix(" mm")
        self.bit_clearance.setValue(0.3)
        layout.addRow("Bit clearance", self.bit_clearance)

        self.bottom_thickness = QtGui.QDoubleSpinBox()
        self.bottom_thickness.setDecimals(2)
        self.bottom_thickness.setRange(0.1, 50.0)
        self.bottom_thickness.setSuffix(" mm")
        self.bottom_thickness.setValue(2.0)
        layout.addRow("Bottom thickness", self.bottom_thickness)

        self.thread_length = QtGui.QDoubleSpinBox()
        self.thread_length.setDecimals(1)
        self.thread_length.setRange(3.0, 100.0)
        self.thread_length.setSuffix(" mm")
        self.thread_length.setValue(10.0)
        layout.addRow("Thread length", self.thread_length)

        self.thread_pitch = QtGui.QDoubleSpinBox()
        self.thread_pitch.setDecimals(1)
        self.thread_pitch.setRange(1.0, 10.0)
        self.thread_pitch.setSuffix(" mm")
        self.thread_pitch.setValue(3.0)
        layout.addRow("Thread pitch", self.thread_pitch)

        self.thread_height = QtGui.QDoubleSpinBox()
        self.thread_height.setDecimals(2)
        self.thread_height.setRange(0.2, 5.0)
        self.thread_height.setSuffix(" mm")
        self.thread_height.setValue(1.0)
        layout.addRow("Thread height (radial depth)", self.thread_height)

        self.thread_clearance = QtGui.QDoubleSpinBox()
        self.thread_clearance.setDecimals(2)
        self.thread_clearance.setRange(0.05, 2.0)
        self.thread_clearance.setSuffix(" mm")
        self.thread_clearance.setValue(0.3)
        layout.addRow("Thread fit clearance", self.thread_clearance)

        self.cap_wall_thickness = QtGui.QDoubleSpinBox()
        self.cap_wall_thickness.setDecimals(2)
        self.cap_wall_thickness.setRange(0.1, 50.0)
        self.cap_wall_thickness.setSuffix(" mm")
        self.cap_wall_thickness.setValue(2.0)
        layout.addRow("Cap wall thickness", self.cap_wall_thickness)

        self.cap_top_thickness = QtGui.QDoubleSpinBox()
        self.cap_top_thickness.setDecimals(2)
        self.cap_top_thickness.setRange(0.1, 50.0)
        self.cap_top_thickness.setSuffix(" mm")
        self.cap_top_thickness.setValue(3.0)
        layout.addRow("Cap top thickness", self.cap_top_thickness)

        self.knurl_enabled = QtGui.QCheckBox("Add knurling to cap")
        self.knurl_enabled.setChecked(True)
        layout.addRow("", self.knurl_enabled)

        self.knurl_pitch = QtGui.QDoubleSpinBox()
        self.knurl_pitch.setDecimals(2)
        self.knurl_pitch.setRange(1.0, 10.0)
        self.knurl_pitch.setSuffix(" mm")
        self.knurl_pitch.setValue(2.5)
        self.knurl_enabled.toggled.connect(self.knurl_pitch.setEnabled)
        layout.addRow("Knurl pitch", self.knurl_pitch)

        self.knurl_depth = QtGui.QDoubleSpinBox()
        self.knurl_depth.setDecimals(2)
        self.knurl_depth.setRange(0.1, 2.0)
        self.knurl_depth.setSuffix(" mm")
        self.knurl_depth.setValue(0.5)
        self.knurl_enabled.toggled.connect(self.knurl_depth.setEnabled)
        layout.addRow("Knurl depth", self.knurl_depth)

        self.preview_label = QtGui.QLabel()
        layout.addRow("Preview", self.preview_label)

        self.system_combo.currentTextChanged.connect(self._update_preview)
        self.size_combo.currentTextChanged.connect(self._update_preview)
        self.custom_diameter.valueChanged.connect(self._update_preview)
        self.bit_count.valueChanged.connect(self._update_preview)
        self.wall_thickness.valueChanged.connect(self._update_preview)
        self.bit_clearance.valueChanged.connect(self._update_preview)
        self.length_buttons.buttonToggled.connect(self._update_preview)
        self.custom_length.valueChanged.connect(self._update_preview)

    def _on_system_changed(self, system):
        self.size_combo.clear()
        is_custom = system == drill_sizes.SYSTEM_CUSTOM
        self.size_combo.setVisible(not is_custom)
        self.custom_diameter.setVisible(is_custom)
        if system == drill_sizes.SYSTEM_METRIC:
            for mm in [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7,
                       7.5, 8, 8.5, 9, 9.5, 10, 11, 12, 13, 14, 15, 16, 18, 20]:
                self.size_combo.addItem("{} mm".format(mm), mm)
        elif system == drill_sizes.SYSTEM_FRACTIONAL:
            for label, inches in drill_sizes.fractional_sizes_in():
                self.size_combo.addItem(label, label)
        elif system == drill_sizes.SYSTEM_NUMBER:
            for label in sorted(drill_sizes.NUMBER_GAUGE_SIZES_IN,
                                 key=lambda s: int(s[1:])):
                self.size_combo.addItem(label, label)
        elif system == drill_sizes.SYSTEM_LETTER:
            for label in sorted(drill_sizes.LETTER_GAUGE_SIZES_IN):
                self.size_combo.addItem(label, label)
        self._update_preview()

    def _selected_diameter_mm(self):
        system = self.system_combo.currentText()
        if system == drill_sizes.SYSTEM_CUSTOM:
            return drill_sizes.resolve_diameter_mm(system, self.custom_diameter.value())
        return drill_sizes.resolve_diameter_mm(system, self.size_combo.currentData())

    def _selected_size_label(self):
        system = self.system_combo.currentText()
        if system == drill_sizes.SYSTEM_CUSTOM:
            return "{:.3f} mm (custom)".format(self.custom_diameter.value())
        return self.size_combo.currentText()

    def _selected_length_category(self):
        checked = self.length_buttons.checkedButton()
        return checked.text() if checked else drill_lengths.CATEGORY_JOBBER

    def _update_preview(self, *args):
        try:
            diameter = self._selected_diameter_mm()
        except (KeyError, TypeError, ValueError):
            self.preview_label.setText("Select a size")
            return

        from . import packing
        bore = packing.bore_diameter(diameter, self.bit_count.value(), self.bit_clearance.value())
        outer = bore + 2 * self.wall_thickness.value()

        category = self._selected_length_category()
        if category == "Custom":
            length = self.custom_length.value()
        else:
            length = drill_lengths.length_for(diameter, category)

        self.preview_label.setText(
            "Bit {:.3f} mm x{} -> bore {:.2f} mm, outer {:.2f} mm, length {:.1f} mm".format(
                diameter, self.bit_count.value(), bore, outer, length))

    def get_parameters(self):
        diameter = self._selected_diameter_mm()
        category = self._selected_length_category()
        length = self.custom_length.value() if category == "Custom" else None
        return dict(
            bit_diameter_mm=diameter,
            bit_count=self.bit_count.value(),
            size_system=self.system_combo.currentText(),
            size_label=self._selected_size_label(),
            length_category=category,
            wall_thickness_mm=self.wall_thickness.value(),
            bit_clearance_mm=self.bit_clearance.value(),
            length_mm=length,
            bottom_thickness_mm=self.bottom_thickness.value(),
            thread_length_mm=self.thread_length.value(),
            thread_pitch_mm=self.thread_pitch.value(),
            thread_height_mm=self.thread_height.value(),
            thread_clearance_mm=self.thread_clearance.value(),
            cap_wall_thickness_mm=self.cap_wall_thickness.value(),
            cap_top_thickness_mm=self.cap_top_thickness.value(),
            knurl_enabled=self.knurl_enabled.isChecked(),
            knurl_pitch_mm=self.knurl_pitch.value(),
            knurl_depth_mm=self.knurl_depth.value(),
        )

    def accept(self):
        self.on_accept(self.get_parameters())
        import FreeCADGui
        FreeCADGui.Control.closeDialog()
        return True

    def reject(self):
        import FreeCADGui
        FreeCADGui.Control.closeDialog()
        return True
