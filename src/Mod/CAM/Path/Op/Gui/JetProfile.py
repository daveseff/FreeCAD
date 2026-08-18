# SPDX-License-Identifier: LGPL-2.1-or-later

# ***************************************************************************
# *   Copyright (c) 2026                                                    *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import FreeCAD
import Path.Op.Gui.Base as PathOpGui
import Path.Op.JetProfile as PathJetProfile

from PySide import QtGui, QtWidgets
from PySide.QtCore import QT_TRANSLATE_NOOP

__title__ = "CAM Jet Profile Operation UI"
__author__ = "OpenAI Codex"
__url__ = "https://www.freecad.org"
__doc__ = "Jet profile operation page controller and command implementation."


class TaskPanelOpPage(PathOpGui.TaskPanelPage):
    """Page controller class for the JetProfile operation."""

    def getForm(self):
        form = QtGui.QWidget()
        layout = QtWidgets.QGridLayout(form)

        row = 0

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Tool controller")), row, 0)
        form.toolController = QtWidgets.QComboBox()
        layout.addWidget(form.toolController, row, 1)
        row += 1

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Cut side")), row, 0)
        form.cutSide = QtWidgets.QComboBox()
        layout.addWidget(form.cutSide, row, 1)
        row += 1

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Direction")), row, 0)
        form.direction = QtWidgets.QComboBox()
        layout.addWidget(form.direction, row, 1)
        row += 1

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Lead-in style")), row, 0)
        form.leadInStyle = QtWidgets.QComboBox()
        layout.addWidget(form.leadInStyle, row, 1)
        row += 1

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Lead-in length")), row, 0)
        form.leadInLength = QtWidgets.QLineEdit()
        layout.addWidget(form.leadInLength, row, 1)
        row += 1

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Lead-out style")), row, 0)
        form.leadOutStyle = QtWidgets.QComboBox()
        layout.addWidget(form.leadOutStyle, row, 1)
        row += 1

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Lead-out length")), row, 0)
        form.leadOutLength = QtWidgets.QLineEdit()
        layout.addWidget(form.leadOutLength, row, 1)
        row += 1

        form.useStartPoint = QtWidgets.QCheckBox(self.pageLabel("Use start point"))
        layout.addWidget(form.useStartPoint, row, 0, 1, 2)
        row += 1

        form.loopCorners = QtWidgets.QCheckBox(self.pageLabel("Loop sharp corners"))
        layout.addWidget(form.loopCorners, row, 0, 1, 2)
        row += 1

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Loop corner radius")), row, 0)
        form.loopCornerRadius = QtWidgets.QLineEdit()
        layout.addWidget(form.loopCornerRadius, row, 1)
        row += 1

        form.scaffoldNote = QtWidgets.QLabel(
            self.pageLabel("Scaffold only: requires a Plasma Torch toolbit and generates placeholder M3/M5 torch control.")
        )
        form.scaffoldNote.setWordWrap(True)
        layout.addWidget(form.scaffoldNote, row, 0, 1, 2)
        row += 1

        layout.setRowStretch(row, 1)

        enumTups = PathJetProfile.ObjectJetProfile.areaOpPropertyEnumerations(dataType="raw")
        self.populateCombobox(
            form,
            enumTups,
            [
                ("cutSide", "CutSide"),
                ("direction", "Direction"),
                ("leadInStyle", "LeadInStyle"),
                ("leadOutStyle", "LeadOutStyle"),
            ],
        )
        return form

    def pageLabel(self, text):
        return FreeCAD.Qt.translate("CAM_JetProfile", text)

    def getFields(self, obj):
        self.updateToolController(obj, self.form.toolController)

        obj.Direction = str(self.form.direction.currentData())
        obj.CutSide = str(self.form.cutSide.currentData())
        obj.LeadInStyle = str(self.form.leadInStyle.currentData())
        obj.LeadOutStyle = str(self.form.leadOutStyle.currentData())
        obj.LeadInEnabled = obj.LeadInStyle != "None"
        obj.LeadOutEnabled = obj.LeadOutStyle != "None"
        self.updateLeadInLength(obj)
        self.updateLeadOutLength(obj)
        obj.UseStartPoint = self.form.useStartPoint.isChecked()
        obj.LoopCorners = self.form.loopCorners.isChecked()
        self.updateLoopCornerRadius(obj)

    def setFields(self, obj):
        self.setupToolController(obj, self.form.toolController)

        self.selectInComboBox(getattr(obj, "Direction", "CW"), self.form.direction)
        self.selectInComboBox(obj.CutSide, self.form.cutSide)
        lead_in_style = getattr(obj, "LeadInStyle", "None")
        lead_out_style = getattr(obj, "LeadOutStyle", "None")
        if lead_in_style == "None" and getattr(obj, "LeadInEnabled", False):
            lead_in_style = "Tangent"
        if lead_out_style == "None" and getattr(obj, "LeadOutEnabled", False):
            lead_out_style = "Tangent"
        self.selectInComboBox(lead_in_style, self.form.leadInStyle)
        self.selectInComboBox(lead_out_style, self.form.leadOutStyle)
        self.form.leadInLength.setText(
            FreeCAD.Units.Quantity(obj.LeadInLength.Value, FreeCAD.Units.Length).UserString
        )
        self.form.leadOutLength.setText(
            FreeCAD.Units.Quantity(obj.LeadOutLength.Value, FreeCAD.Units.Length).UserString
        )
        self.form.useStartPoint.setChecked(obj.UseStartPoint)
        self.form.loopCorners.setChecked(obj.LoopCorners)
        self.form.loopCornerRadius.setText(
            FreeCAD.Units.Quantity(obj.LoopCornerRadius.Value, FreeCAD.Units.Length).UserString
        )

    def updateLeadInLength(self, obj):
        self.updateDistanceField(obj, "LeadInLength", self.form.leadInLength)

    def updateLeadOutLength(self, obj):
        self.updateDistanceField(obj, "LeadOutLength", self.form.leadOutLength)

    def updateLoopCornerRadius(self, obj):
        self.updateDistanceField(obj, "LoopCornerRadius", self.form.loopCornerRadius)

    def updateDistanceField(self, obj, prop_name, widget):
        text = widget.text().strip()
        if not text:
            return

        prop = getattr(obj, prop_name)
        value = self.parseDistanceValue(prop, text)
        if value is None:
            return

        if not FreeCAD.Units.Quantity(prop.Value, FreeCAD.Units.Length) == FreeCAD.Units.Quantity(
            value, FreeCAD.Units.Length
        ):
            setattr(obj, prop_name, value)
        widget.setText(FreeCAD.Units.Quantity(getattr(obj, prop_name).Value, FreeCAD.Units.Length).UserString)

    def parseDistanceValue(self, prop, text):
        try:
            return FreeCAD.Units.Quantity(text).Value
        except Exception:
            pass

        try:
            float(text)
        except ValueError:
            return None

        try:
            unit = prop.getUserPreferred()[2]
            return FreeCAD.Units.Quantity(f"{text} {unit}").Value
        except Exception:
            return None

    def getSignalsForUpdate(self, obj):
        del obj
        signals = [
            self.form.toolController.currentIndexChanged,
            self.form.cutSide.currentIndexChanged,
            self.form.direction.currentIndexChanged,
            self.form.leadInStyle.currentIndexChanged,
            self.form.leadInLength.editingFinished,
            self.form.leadOutStyle.currentIndexChanged,
            self.form.leadOutLength.editingFinished,
            self.form.loopCornerRadius.editingFinished,
        ]
        if hasattr(self.form.useStartPoint, "checkStateChanged"):
            signals.append(self.form.useStartPoint.checkStateChanged)
            signals.append(self.form.loopCorners.checkStateChanged)
        else:
            signals.append(self.form.useStartPoint.stateChanged)
            signals.append(self.form.loopCorners.stateChanged)
        return signals


Command = PathOpGui.SetupOperation(
    "JetProfile",
    PathJetProfile.Create,
    TaskPanelOpPage,
    "CAM_Profile",
    QT_TRANSLATE_NOOP("CAM_JetProfile", "Jet Profile"),
    QT_TRANSLATE_NOOP(
        "CAM_JetProfile",
        "Create a scaffold jet-cutting profile from selected face(s) or edge(s)",
    ),
    PathJetProfile.SetupProperties,
)

FreeCAD.Console.PrintLog("Loading PathJetProfileGui ... done\n")
