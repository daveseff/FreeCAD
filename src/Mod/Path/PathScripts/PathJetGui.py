# -*- coding: utf-8 -*-
# ***************************************************************************
# *   Copyright (c) 2021 daveseff <dave@solar1.net>                         *
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
import FreeCADGui
import PathGui as PGui # ensure Path/Gui/Resources are loaded
import PathScripts.PathJet as PathJet
import PathScripts.PathGui as PathGui
import PathScripts.PathLog as PathLog
import PathScripts.PathOpGui as PathOpGui

from PySide import QtCore

__title__ = "Path Jet/Plasma/Laser Operation UI."
__author__ = "Dave Seff"
__url__ = "https://www.freecadweb.org"
__doc__ = "UI and Command for Path Jet Cutting Operation."

LOGLEVEL = False

if LOGLEVEL:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.NOTICE, PathLog.thisModule())


class TaskPanelOpPage(PathOpGui.TaskPanelPage):
    '''Controller for the jet operation's page'''

    def registerSignalHandlers(self, obj):
        pass

    def getForm(self):
        '''getForm() ... return UI'''
        return FreeCADGui.PySideUic.loadUi(":/panels/PageOpJetEdit.ui")

    def getFields(self, obj):
        '''setFields(obj) ... update obj's properties with values from the UI'''
        PathLog.track()

        self.updateToolController(obj, self.form.toolController)

    def setFields(self, obj):
        '''setFields(obj) ... update UI with obj properties' values'''
        PathLog.track()

    def getSignalsForUpdate(self, obj):
        '''getSignalsForUpdate(obj) ... return list of signals which cause the receiver to update the model'''
        signals = []

        return signals

Command = PathOpGui.SetupOperation('Jet',
        PathJet.Create,
        TaskPanelOpPage,
        'Path_Jet',
        QtCore.QT_TRANSLATE_NOOP("Path_Jet", "Jet"),
        QtCore.QT_TRANSLATE_NOOP("Path_Jet", "Creates a Path Jet/Plasma/Laser object from a features of a base object"),
        PathJet.SetupProperties)

FreeCAD.Console.PrintLog("Loading PathJetGui... done\n")
