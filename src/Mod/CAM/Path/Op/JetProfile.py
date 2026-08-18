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
import math
import Path
import Path.Geom
import Path.Op.Area as PathAreaOp
import Path.Op.Base as PathOp
import Path.Op.Util as PathOpUtil
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

    def opFeatures(self, obj):
        del obj
        return (
            PathOp.FeatureTool
            | PathOp.FeatureHeights
            | PathOp.FeatureStartPoint
            | PathOp.FeatureBaseFaces
            | PathOp.FeatureBaseEdges
        )

    def areaOpFeatures(self, obj):
        return PathOp.FeatureBaseFaces | PathOp.FeatureBaseEdges

    def initAreaOp(self, obj):
        self.propertiesReady = False
        self.initAreaOpProperties(obj)
        if hasattr(obj, "KerfWidth"):
            obj.setEditorMode("KerfWidth", 2)

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
                "Direction",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "The direction that the jet path should go around closed contours.",
                ),
            ),
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
                    "Compatibility flag for lead-in generation.",
                ),
            ),
            (
                "App::PropertyBool",
                "LeadOutEnabled",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Compatibility flag for lead-out generation.",
                ),
            ),
            (
                "App::PropertyEnumeration",
                "LeadInStyle",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Lead-in style for closed jet contours.",
                ),
            ),
            (
                "App::PropertyDistance",
                "LeadInLength",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Lead-in length for the selected style.",
                ),
            ),
            (
                "App::PropertyEnumeration",
                "LeadOutStyle",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Lead-out style for closed jet contours.",
                ),
            ),
            (
                "App::PropertyDistance",
                "LeadOutLength",
                "Jet",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Lead-out length for the selected style.",
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
            "Direction": [
                (translate("PathJetProfile", "CW"), "CW"),
                (translate("PathJetProfile", "CCW"), "CCW"),
            ],
            "CutSide": [
                (translate("PathJetProfile", "Outside"), "Outside"),
                (translate("PathJetProfile", "Inside"), "Inside"),
                (translate("PathJetProfile", "On Line"), "OnLine"),
            ],
            "LeadInStyle": [
                (translate("PathJetProfile", "None"), "None"),
                (translate("PathJetProfile", "Arc"), "Arc"),
                (translate("PathJetProfile", "Tangent"), "Tangent"),
                (translate("PathJetProfile", "Perpendicular"), "Perpendicular"),
            ],
            "LeadOutStyle": [
                (translate("PathJetProfile", "None"), "None"),
                (translate("PathJetProfile", "Arc"), "Arc"),
                (translate("PathJetProfile", "Tangent"), "Tangent"),
                (translate("PathJetProfile", "Perpendicular"), "Perpendicular"),
            ],
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
        if hasattr(obj, "KerfWidth"):
            obj.setEditorMode("KerfWidth", 2)

    def areaOpSetDefaultValues(self, obj, job):
        obj.Direction = "CW"
        obj.CutSide = "OnLine"
        obj.KerfWidth = "1.0 mm"
        obj.LeadInEnabled = False
        obj.LeadOutEnabled = False
        obj.LeadInStyle = "None"
        obj.LeadInLength = "2.5 mm"
        obj.LeadOutStyle = "None"
        obj.LeadOutLength = "2.5 mm"
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

    def _offsetShape(self, shape, obj):
        kerf_width = self._kerfWidth(obj)
        if obj.CutSide == "OnLine" or kerf_width <= 0:
            return shape

        if not getattr(shape, "isClosed", lambda: False)():
            Path.Log.warning(
                translate(
                    "PathJetProfile",
                    "JetProfile kerf compensation currently requires closed contours; using on-line path.",
                )
            )
            return shape

        approx = PathOpUtil.approximateWire(shape, 0.01)
        try:
            base_face = Part.Face(approx)
        except Part.OCCError:
            Path.Log.warning(
                translate(
                    "PathJetProfile",
                    "JetProfile could not build a planar face for kerf compensation; using on-line path.",
                )
            )
            return shape

        half_kerf = kerf_width / 2.0
        requested_inside = obj.CutSide == "Inside"
        candidates = []

        for offset in (half_kerf, -half_kerf):
            try:
                offset_shape = approx.makeOffset2D(offset)
            except Part.OCCError:
                continue

            wires = list(getattr(offset_shape, "Wires", []))
            if not wires and hasattr(offset_shape, "Edges") and offset_shape.Edges:
                try:
                    wires = [Part.Wire(Part.__sortEdges__(offset_shape.Edges))]
                except Part.OCCError:
                    wires = []

            for wire in wires:
                if not wire.Edges:
                    continue
                candidate = PathOpUtil.orientWire(wire, None)
                point = candidate.Edges[0].firstVertex().Point
                is_inside = base_face.isInside(point, FreeCAD.Base.Precision.confusion(), True)
                candidates.append((is_inside, candidate))

        for is_inside, candidate in candidates:
            if is_inside == requested_inside:
                return candidate

        Path.Log.warning(
            translate(
                "PathJetProfile",
                "JetProfile could not resolve the requested kerf compensation side; using on-line path.",
            )
        )
        return shape

    def _signedAreaXY(self, edges):
        points = []
        for edge in edges:
            if not points:
                points.append(edge.firstVertex().Point)
            points.append(edge.lastVertex().Point)

        if len(points) < 3:
            return 0.0
        if points[0].distanceToPoint(points[-1]) > FreeCAD.Base.Precision.confusion():
            points.append(points[0])

        area = 0.0
        for p0, p1 in zip(points, points[1:]):
            area += p0.x * p1.y - p1.x * p0.y
        return area * 0.5

    def _orderedEdges(self, shape, startPoint=None, direction=None):
        wire = PathOpUtil.orientWire(shape, None) if hasattr(shape, "Edges") else shape
        edges = list(wire.Edges) if hasattr(wire, "Edges") else [wire]
        if not edges:
            return []

        if getattr(wire, "isClosed", lambda: False)() and direction in ("CW", "CCW"):
            signed_area = self._signedAreaXY(edges)
            if (direction == "CW" and signed_area > 0) or (direction == "CCW" and signed_area < 0):
                edges = [Path.Geom.flipEdge(edge) for edge in reversed(edges)]

        if startPoint is None:
            return edges

        if getattr(wire, "isClosed", lambda: False)():
            start_index = min(
                range(len(edges)),
                key=lambda idx: edges[idx].firstVertex().Point.distanceToPoint(startPoint),
            )
            return edges[start_index:] + edges[:start_index]

        start = edges[0].firstVertex().Point
        end = edges[-1].lastVertex().Point
        if end.distanceToPoint(startPoint) < start.distanceToPoint(startPoint):
            return [Path.Geom.flipEdge(edge) for edge in reversed(edges)]
        return edges

    def _commandsForEdges(self, edges):
        commands = []
        for edge in edges:
            edge_commands = []
            source_edges = [edge]
            if isinstance(edge.Curve, Part.Circle) and edge.isClosed():
                mid = edge.FirstParameter + (edge.LastParameter - edge.FirstParameter) * 0.5
                source_edges = [
                    Part.Edge(Part.ArcOfCircle(edge.Curve, edge.FirstParameter, mid)),
                    Part.Edge(Part.ArcOfCircle(edge.Curve, mid, edge.LastParameter)),
                ]

            for source_edge in source_edges:
                edge_commands.extend(
                    Path.Geom.cmdsForEdge(
                        source_edge,
                        approximation=True,
                        hSpeed=self.horizFeed,
                        vSpeed=self.vertFeed,
                        tol=0.01,
                    )
                )

            for cmd in edge_commands:
                params = dict(cmd.Parameters)
                params.pop("Z", None)
                params.pop("K", None)
                commands.append(Path.Command(cmd.Name, params))
        return commands

    def _cutHeight(self, obj):
        tool_controller = getattr(obj, "ToolController", None)
        tool = getattr(tool_controller, "Tool", None)
        cut_height = tool.CutHeight.Value if tool and hasattr(tool, "CutHeight") else 0.0
        job = self.getJob(obj)
        if job and getattr(job, "Stock", None):
            reference_z = job.Stock.Shape.BoundBox.ZMax
        elif hasattr(obj, "Base") and obj.Base:
            reference_z = max(base.Shape.BoundBox.ZMax for base, _subs in obj.Base)
        else:
            reference_z = 0.0
        return reference_z - cut_height

    def _kerfWidth(self, obj):
        tool_controller = getattr(obj, "ToolController", None)
        tool = getattr(tool_controller, "Tool", None)
        if tool and hasattr(tool, "KerfWidth"):
            return tool.KerfWidth.Value
        return obj.KerfWidth.Value if hasattr(obj, "KerfWidth") else 0.0

    def _normalized(self, vector, fallback):
        result = FreeCAD.Vector(vector.x, vector.y, vector.z)
        if result.Length == 0:
            return FreeCAD.Vector(fallback.x, fallback.y, fallback.z)
        result.normalize()
        return result

    def _edgeTangent(self, edge, at_start=True):
        first = edge.FirstParameter
        last = edge.LastParameter
        if at_start:
            t0 = first + (last - first) * 0.01
            t1 = first + (last - first) * 0.05
        else:
            t0 = last - (last - first) * 0.05
            t1 = last - (last - first) * 0.01
        p0 = edge.valueAt(t0)
        p1 = edge.valueAt(t1)
        vec = p1.sub(p0)
        if vec.Length == 0:
            return FreeCAD.Vector(1, 0, 0)
        vec.normalize()
        return vec

    def _scrapNormal(self, wire, point, tangent, cut_side):
        left = self._normalized(FreeCAD.Vector(-tangent.y, tangent.x, 0), FreeCAD.Vector(0, 1, 0))
        right = -left
        try:
            face = Part.Face(PathOpUtil.orientWire(wire, None))
        except Part.OCCError:
            return left

        probe = max(0.1, min(1.0, getattr(wire.BoundBox, "DiagonalLength", 1.0) * 0.001))
        left_inside = face.isInside(point + left * probe, FreeCAD.Base.Precision.confusion(), True)
        right_inside = face.isInside(
            point + right * probe, FreeCAD.Base.Precision.confusion(), True
        )
        want_inside = cut_side == "Inside"
        if left_inside == want_inside and right_inside != want_inside:
            return left
        if right_inside == want_inside and left_inside != want_inside:
            return right
        return right if cut_side == "Outside" else left

    def _arcEdge(self, start, mid, end):
        return Part.Edge(Part.Arc(start, mid, end))

    def _leadInGeometry(self, wire, entry_edge, entry_point, obj):
        style = getattr(obj, "LeadInStyle", "None")
        if style == "None" and getattr(obj, "LeadInEnabled", False):
            style = "Tangent"
        length = obj.LeadInLength.Value if hasattr(obj, "LeadInLength") else 0.0
        if style == "None" or length <= 0 or not getattr(wire, "isClosed", lambda: False)():
            return entry_point, []

        tangent = self._edgeTangent(entry_edge, at_start=True)
        normal = self._scrapNormal(wire, entry_point, tangent, obj.CutSide)

        if style == "Perpendicular":
            start = entry_point + normal * length
            return start, [Path.Command("G1", {"X": entry_point.x, "Y": entry_point.y, "F": self.horizFeed})]

        if style == "Tangent":
            start = entry_point - tangent * length
            return start, [Path.Command("G1", {"X": entry_point.x, "Y": entry_point.y, "F": self.horizFeed})]

        if style == "Arc":
            start = entry_point - tangent * length + normal * length
            center = entry_point + normal * length
            mid = center + self._normalized(-(tangent + normal), FreeCAD.Vector(-1, -1, 0)) * length
            cmds = self._commandsForEdges([self._arcEdge(start, mid, entry_point)])
            return start, cmds

        return entry_point, []

    def _leadOutGeometry(self, wire, exit_edge, exit_point, obj):
        style = getattr(obj, "LeadOutStyle", "None")
        if style == "None" and getattr(obj, "LeadOutEnabled", False):
            style = "Tangent"
        length = obj.LeadOutLength.Value if hasattr(obj, "LeadOutLength") else 0.0
        if style == "None" or length <= 0 or not getattr(wire, "isClosed", lambda: False)():
            return []

        tangent = self._edgeTangent(exit_edge, at_start=False)
        normal = self._scrapNormal(wire, exit_point, tangent, obj.CutSide)

        if style == "Perpendicular":
            end = exit_point + normal * length
            return [Path.Command("G1", {"X": end.x, "Y": end.y, "F": self.horizFeed})]

        if style == "Tangent":
            end = exit_point + tangent * length
            return [Path.Command("G1", {"X": end.x, "Y": end.y, "F": self.horizFeed})]

        if style == "Arc":
            end = exit_point + tangent * length + normal * length
            center = exit_point + normal * length
            mid = center + self._normalized(tangent - normal, FreeCAD.Vector(1, -1, 0)) * length
            return self._commandsForEdges([self._arcEdge(exit_point, mid, end)])

        return []

    def _plasmaFallbackFeed(self, obj):
        tool_controller = getattr(obj, "ToolController", None)
        tool = getattr(tool_controller, "Tool", None)
        if tool and hasattr(tool, "PlungeRate"):
            return tool.PlungeRate.Value
        return 0.0

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
            fallback_feed = self._plasmaFallbackFeed(obj)
            if fallback_feed > 0:
                self.horizFeed = fallback_feed
                if self.vertFeed <= 0:
                    self.vertFeed = fallback_feed
                Path.Log.warning(
                    translate(
                        "PathJetProfile",
                        "JetProfile is using the plasma toolbit PlungeRate as a temporary cut feed fallback.",
                    )
                )

        if self.horizFeed <= 0:
            Path.Log.error(
                translate(
                    "PathJetProfile",
                    "JetProfile plasma cutting requires a positive horizontal feed rate.",
                )
            )
            return []

        target_z = self._cutHeight(obj)
        shapes = self._collectShapes(obj)

        self.commandlist.append(Path.Command("(JetProfile scaffold path)"))
        self.commandlist.append(
            Path.Command(
                "(TODO: refine kerf compensation for open contours and more complex geometry)"
            )
        )
        self.commandlist.append(
            Path.Command(
                "(TODO: add plasma/laser/waterjet-specific post and pierce behavior integration)"
            )
        )
        self.commandlist.append(Path.Command("(JetProfile uses a single pass at tool CutHeight)"))
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
            working_shape = self._offsetShape(shape, obj)
            edges = self._orderedEdges(working_shape, startPoint, getattr(obj, "Direction", "CW"))
            if not edges:
                continue

            entry = edges[0].firstVertex().Point
            contour_commands = self._commandsForEdges(edges)
            lead_in_start, lead_in_commands = self._leadInGeometry(working_shape, edges[0], entry, obj)
            lead_out_commands = self._leadOutGeometry(working_shape, edges[-1], edges[-1].lastVertex().Point, obj)
            self.commandlist.append(Path.Command("G0", {"Z": obj.SafeHeight.Value, "F": self.vertRapid}))
            self.commandlist.append(
                Path.Command("G0", {"X": lead_in_start.x, "Y": lead_in_start.y, "F": self.horizRapid})
            )
            # TODO: Replace simple torch commands with process-aware plasma behavior.
            # TODO: Generate sharp-corner looping geometry when LoopCorners is enabled.
            self.commandlist.append(Path.Command("G1", {"Z": target_z, "F": self.vertFeed}))
            self.commandlist.append(Path.Command("M3"))
            self.commandlist.extend(lead_in_commands)
            self.commandlist.extend(contour_commands)
            self.commandlist.extend(lead_out_commands)
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
