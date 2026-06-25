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
import Path
import Path.Op.Area as PathAreaOp
import Path.Op.Base as PathOp
from PySide.QtCore import QT_TRANSLATE_NOOP

from lazy_loader.lazy_loader import LazyLoader

Part = LazyLoader("Part", globals(), "Part")

translate = FreeCAD.Qt.translate

__title__ = "CAM Jet Profile Operation"
__author__ = "OpenAI Codex"
__url__ = "https://www.freecad.org"
__doc__ = "Create a scaffold jet-cutting profile operation."

if False:
    Path.Log.setLevel(Path.Log.Level.DEBUG, Path.Log.thisModule())
    Path.Log.trackModule(Path.Log.thisModule())
else:
    Path.Log.setLevel(Path.Log.Level.INFO, Path.Log.thisModule())


class ObjectJetProfile(PathAreaOp.ObjectOp):
    """Proxy object for a minimal jet profile scaffold."""

    def areaOpFeatures(self, obj):
        return PathOp.FeatureBaseFaces | PathOp.FeatureBaseEdges

    def initAreaOp(self, obj):
        self.propertiesReady = False
        self.initAreaOpProperties(obj)

    def initAreaOpProperties(self, obj, warn=False):
        self.addNewProps = []

        for propertytype, propertyname, grp, tooltip in self.areaOpProperties():
            if not hasattr(obj, propertyname):
                obj.addProperty(propertytype, propertyname, grp, tooltip)
                self.addNewProps.append(propertyname)

        if self.addNewProps:
            enums = self.areaOpPropertyEnumerations()
            for name, values in enums:
                if name in self.addNewProps:
                    setattr(obj, name, values)
            if warn:
                message = 'New property added to "{}": {}. Check its default value.\n'.format(
                    obj.Label, self.addNewProps
                )
                FreeCAD.Console.PrintWarning(message)

        self.propertiesReady = True

    def areaOpProperties(self):
        return [
            (
                "App::PropertyEnumeration",
                "CutSide",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Requested jet cut side relative to the selected geometry.",
                ),
            ),
            (
                "App::PropertyDistance",
                "KerfWidth",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Jet kerf width used for future offset calculations.",
                ),
            ),
            (
                "App::PropertyBool",
                "LeadInEnabled",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Enable future lead-in generation for jet entry.",
                ),
            ),
            (
                "App::PropertyBool",
                "LeadOutEnabled",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Enable future lead-out generation for jet exit.",
                ),
            ),
            (
                "App::PropertyBool",
                "LoopCorners",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Enable looping moves around sharp corners for plasma cutting.",
                ),
            ),
            (
                "App::PropertyDistance",
                "LoopCornerRadius",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Requested radius for future sharp-corner looping moves.",
                ),
            ),
        ]

    @classmethod
    def areaOpPropertyEnumerations(cls, dataType="data"):
        enums = {
            "CutSide": [
                (translate("PathJetProfile", "Outside"), "Outside"),
                (translate("PathJetProfile", "Inside"), "Inside"),
                (translate("PathJetProfile", "On Line"), "OnLine"),
            ]
        }

        if dataType == "raw":
            return enums

        data = []
        idx = 0 if dataType == "translated" else 1
        for name in enums:
            data.append((name, [value[idx] for value in enums[name]]))
        return data

    def areaOpOnDocumentRestored(self, obj):
        self.initAreaOpProperties(obj, warn=True)

    def areaOpSetDefaultValues(self, obj, job):
        obj.CutSide = "OnLine"
        obj.KerfWidth = "1.0 mm"
        obj.LeadInEnabled = False
        obj.LeadOutEnabled = False
        obj.LoopCorners = False
        obj.LoopCornerRadius = "1.5 mm"

    def _toolSubtype(self, tool):
        if hasattr(tool, "Proxy") and hasattr(tool.Proxy, "get_subtype"):
            subtype = tool.Proxy.get_subtype()
            if subtype:
                return subtype.lower()
        if hasattr(tool, "ShapeType") and tool.ShapeType:
            return str(tool.ShapeType).lower()
        return ""

    def isToolSupported(self, obj, tool):
        del obj
        subtype = self._toolSubtype(tool)
        shape_type = str(getattr(tool, "ShapeType", "")).lower()
        return subtype == "plasma" or shape_type == "plasma"

    def _collectShapes(self, obj):
        shapes = []
        if not hasattr(obj, "Base") or not obj.Base:
            return shapes

        for base, subNames in obj.Base:
            if not subNames:
                Path.Log.warning(
                    translate(
                        "PathJetProfile",
                        "JetProfile scaffold currently expects selected faces or edges."
                    )
                )
                continue

            edges = []
            for sub in subNames:
                try:
                    element = base.Shape.getElement(sub)
                except Part.OCCError as exc:
                    Path.Log.error(exc)
                    continue

                if sub.startswith("Face"):
                    shapes.append((element.OuterWire.copy(), False, sub))
                elif sub.startswith("Edge"):
                    edges.append(element.copy())

            if edges:
                try:
                    wire = Part.Wire(Part.__sortEdges__(edges))
                    shapes.append((wire, False, "Edges"))
                except Part.OCCError:
                    for edge in edges:
                        shapes.append((edge, False, "Edge"))

        return shapes

    def _wirePoints(self, shape):
        points = []
        edges = shape.Edges if hasattr(shape, "Edges") else [shape]

        for index, edge in enumerate(edges):
            count = max(2, int(edge.Length / 2.0) + 1)
            discretized = edge.discretize(Number=count)
            if index:
                discretized = discretized[1:]
            points.extend(discretized)

        if getattr(shape, "isClosed", lambda: False)() and points:
            if points[0].distanceToPoint(points[-1]) > FreeCAD.Base.Precision.confusion():
                points.append(points[0])

        return points

    def opExecute(self, obj):
        if self._toolSubtype(self.tool) != "plasma":
            Path.Log.error(
                translate(
                    "PathJetProfile",
                    "JetProfile currently supports the Plasma Torch toolbit subtype only.",
                )
            )
            return []

        if self.horizFeed <= 0:
            Path.Log.error(
                translate(
                    "PathJetProfile",
                    "JetProfile plasma cutting requires a positive horizontal feed rate.",
                )
            )
            return []

        self.depthparams = self._customDepthParams(obj, obj.StartDepth.Value, obj.FinalDepth.Value)
        shapes = self._collectShapes(obj)

        self.commandlist.append(Path.Command("(JetProfile scaffold path)"))
        self.commandlist.append(
            Path.Command(
                "(TODO: apply true kerf offset from CutSide and KerfWidth before cutting)"
            )
        )
        self.commandlist.append(
            Path.Command("(TODO: generate lead-in and lead-out geometry when enabled)")
        )
        self.commandlist.append(
            Path.Command(
                "(TODO: add plasma/laser/waterjet-specific post and pierce behavior integration)"
            )
        )
        self.commandlist.append(Path.Command("(Torch control: M03 on, M05 off)"))
        if obj.LoopCorners:
            loop_radius = FreeCAD.Units.Quantity(
                obj.LoopCornerRadius.Value, FreeCAD.Units.Length
            ).UserString
            self.commandlist.append(
                Path.Command("(TODO: loop sharp corners using radius {})".format(loop_radius))
            )

        if not shapes:
            self.commandlist.append(
                Path.Command("(JetProfile: no supported base geometry selected for scaffold)")
            )
            return []

        startPoint = obj.StartPoint if getattr(obj, "UseStartPoint", False) else None

        for shape, isHole, label in shapes:
            del isHole, label
            points = self._wirePoints(shape)
            if not points:
                continue

            orderedPoints = points
            if startPoint is not None:
                if getattr(shape, "isClosed", lambda: False)():
                    startIndex = min(
                        range(len(points)),
                        key=lambda idx: points[idx].distanceToPoint(startPoint),
                    )
                    loopPoints = points[:-1] if len(points) > 1 and points[0] == points[-1] else points
                    orderedPoints = loopPoints[startIndex:] + loopPoints[:startIndex]
                    orderedPoints.append(orderedPoints[0])
                else:
                    # TODO: Replace this endpoint-only choice with proper open-contour entry logic.
                    if points[-1].distanceToPoint(startPoint) < points[0].distanceToPoint(startPoint):
                        orderedPoints = list(reversed(points))

            entry = orderedPoints[0]
            self.commandlist.append(Path.Command("G0", {"Z": obj.SafeHeight.Value, "F": self.vertRapid}))
            self.commandlist.append(
                Path.Command("G0", {"X": entry.x, "Y": entry.y, "F": self.horizRapid})
            )

            for depth in self.depthparams:
                # TODO: Apply CutSide/KerfWidth offset before these moves.
                # TODO: Inject lead-in/out geometry around the contour entry and exit.
                # TODO: Replace simple torch commands with process-aware plasma behavior.
                # TODO: Generate sharp-corner looping geometry when LoopCorners is enabled.
                self.commandlist.append(Path.Command("G1", {"Z": depth, "F": self.vertFeed}))
                self.commandlist.append(Path.Command("M3"))
                for point in orderedPoints[1:]:
                    self.commandlist.append(
                        Path.Command("G1", {"X": point.x, "Y": point.y, "F": self.horizFeed})
                    )
                self.commandlist.append(Path.Command("M5"))
                self.commandlist.append(
                    Path.Command("G0", {"Z": obj.SafeHeight.Value, "F": self.vertRapid})
                )

        return []


def SetupProperties():
    setup = PathAreaOp.SetupProperties()
    setup.extend([item[1] for item in ObjectJetProfile.areaOpProperties(False)])
    return setup


def Create(name, obj=None, parentJob=None):
    """Create(name) ... create and return a JetProfile operation."""
    if obj is None:
        obj = FreeCAD.ActiveDocument.addObject("Path::FeaturePython", name)
    obj.Proxy = ObjectJetProfile(obj, name, parentJob)
    return obj
