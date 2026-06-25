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

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Coolant")), row, 0)
        form.coolantController = QtWidgets.QComboBox()
        layout.addWidget(form.coolantController, row, 1)
        row += 1

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Cut side")), row, 0)
        form.cutSide = QtWidgets.QComboBox()
        layout.addWidget(form.cutSide, row, 1)
        row += 1

        layout.addWidget(QtWidgets.QLabel(self.pageLabel("Kerf width")), row, 0)
        form.kerfWidth = QtWidgets.QLineEdit()
        layout.addWidget(form.kerfWidth, row, 1)
        row += 1

        form.leadInEnabled = QtWidgets.QCheckBox(self.pageLabel("Enable lead-in"))
        layout.addWidget(form.leadInEnabled, row, 0, 1, 2)
        row += 1

        form.leadOutEnabled = QtWidgets.QCheckBox(self.pageLabel("Enable lead-out"))
        layout.addWidget(form.leadOutEnabled, row, 0, 1, 2)
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
        self.populateCombobox(form, enumTups, [("cutSide", "CutSide")])
        return form

    def pageLabel(self, text):
        return FreeCAD.Qt.translate("CAM_JetProfile", text)

    def getFields(self, obj):
        self.updateToolController(obj, self.form.toolController)
        self.updateCoolant(obj, self.form.coolantController)

        obj.CutSide = str(self.form.cutSide.currentData())
        self.updateKerfWidth(obj)
        obj.LeadInEnabled = self.form.leadInEnabled.isChecked()
        obj.LeadOutEnabled = self.form.leadOutEnabled.isChecked()
        obj.UseStartPoint = self.form.useStartPoint.isChecked()
        obj.LoopCorners = self.form.loopCorners.isChecked()
        self.updateLoopCornerRadius(obj)

    def setFields(self, obj):
        self.setupToolController(obj, self.form.toolController)
        self.setupCoolant(obj, self.form.coolantController)

        self.selectInComboBox(obj.CutSide, self.form.cutSide)
        self.form.kerfWidth.setText(
            FreeCAD.Units.Quantity(obj.KerfWidth.Value, FreeCAD.Units.Length).UserString
        )
        self.form.leadInEnabled.setChecked(obj.LeadInEnabled)
        self.form.leadOutEnabled.setChecked(obj.LeadOutEnabled)
        self.form.useStartPoint.setChecked(obj.UseStartPoint)
        self.form.loopCorners.setChecked(obj.LoopCorners)
        self.form.loopCornerRadius.setText(
            FreeCAD.Units.Quantity(obj.LoopCornerRadius.Value, FreeCAD.Units.Length).UserString
        )

    def updateKerfWidth(self, obj):
        text = self.form.kerfWidth.text().strip()
        if not text:
            return

        try:
            value = FreeCAD.Units.Quantity(text).getValueAs("mm")
        except Exception:
            return

        if obj.KerfWidth.getValueAs("mm") != value:
            obj.KerfWidth = value

    def updateLoopCornerRadius(self, obj):
        text = self.form.loopCornerRadius.text().strip()
        if not text:
            return

        try:
            value = FreeCAD.Units.Quantity(text).getValueAs("mm")
        except Exception:
            return

        if obj.LoopCornerRadius.getValueAs("mm") != value:
            obj.LoopCornerRadius = value

    def getSignalsForUpdate(self, obj):
        del obj
        signals = [
            self.form.toolController.currentIndexChanged,
            self.form.coolantController.currentIndexChanged,
            self.form.cutSide.currentIndexChanged,
            self.form.kerfWidth.editingFinished,
            self.form.loopCornerRadius.editingFinished,
        ]
        if hasattr(self.form.leadInEnabled, "checkStateChanged"):
            signals.append(self.form.leadInEnabled.checkStateChanged)
            signals.append(self.form.leadOutEnabled.checkStateChanged)
            signals.append(self.form.useStartPoint.checkStateChanged)
            signals.append(self.form.loopCorners.checkStateChanged)
        else:
            signals.append(self.form.leadInEnabled.stateChanged)
            signals.append(self.form.leadOutEnabled.stateChanged)
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
