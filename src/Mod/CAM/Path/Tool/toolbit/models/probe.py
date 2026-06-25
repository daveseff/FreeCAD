# SPDX-License-Identifier: LGPL-2.1-or-later

# ***************************************************************************
# *   Copyright (c) 2025 Samuel Abels <knipknap@gmail.com>                  *
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
import Path.Base.Util as PathUtil
from typing import Optional, Mapping
from ...camassets import cam_assets
from ...shape import ToolBitShapeProbe
from .base import ToolBit


class ToolBitProbe(ToolBit):
    SHAPE_CLASS = ToolBitShapeProbe
    _PLASMA_PARAMETERS = {
        "KerfWidth": (
            "App::PropertyLength",
            FreeCAD.Qt.translate("ToolBit", "Width of the plasma cut kerf"),
            "1.500 mm",
        ),
        "PierceDelay": (
            "App::PropertyFloat",
            FreeCAD.Qt.translate("ToolBit", "Seconds to dwell after torch ignition before motion"),
            0.5,
        ),
        "PierceHeight": (
            "App::PropertyLength",
            FreeCAD.Qt.translate("ToolBit", "Initial torch height for piercing"),
            "3.000 mm",
        ),
        "PlungeRate": (
            "App::PropertySpeed",
            FreeCAD.Qt.translate("ToolBit", "Feed rate used to move from pierce height to cut height"),
            "300.000 mm/min",
        ),
        "CutHeight": (
            "App::PropertyLength",
            FreeCAD.Qt.translate("ToolBit", "Torch height while cutting"),
            "1.500 mm",
        ),
        "EndPause": (
            "App::PropertyFloat",
            FreeCAD.Qt.translate("ToolBit", "Seconds to dwell after torch off at the end of the cut"),
            0.0,
        ),
    }
    _LEGACY_PROBE_PARAMETERS = ("Diameter", "Length", "ShaftDiameter")

    def __init__(
        self, shape: ToolBitShapeProbe, id: str | None = None, attrs: Optional[Mapping] = None
    ):
        Path.Log.track(f"ToolBitProbe __init__ called with shape: {shape}, id: {id}")
        super().__init__(shape, id=id, attrs=attrs)
        self.obj.SpindleDirection = "None"
        self.obj.setEditorMode("SpindleDirection", 2)
        self._update_subtype_properties()

    def _update_tool_properties(self):
        super()._update_tool_properties()
        if getattr(self, "_shape_type", None):
            self._update_subtype_properties()

    def _update_subtype_properties(self):
        if self.get_subtype() != "plasma":
            return

        plasma_icon = cam_assets.get_or_none("toolbitshapesvg://plasma.svg")
        if plasma_icon:
            self._tool_bit_shape.icon = plasma_icon

        self.obj.SpindleDirection = "None"
        self.obj.setEditorMode("SpindleDirection", 2)

        for name in self._LEGACY_PROBE_PARAMETERS:
            if hasattr(self.obj, name):
                self.obj.setEditorMode(name, 2)
            self._tool_bit_shape._params.pop(name, None)

        for name, (prop_type, docstring, default_value) in self._PLASMA_PARAMETERS.items():
            if not hasattr(self.obj, name):
                self.obj.addProperty(prop_type, name, "Shape", docstring)

            self._tool_bit_shape._param_types[name] = prop_type
            value = self._tool_bit_shape.get_parameters().get(name, default_value)
            self._tool_bit_shape.set_parameter(name, value)
            if getattr(self.obj, name) != value:
                PathUtil.setProperty(self.obj, name, value)
            self.obj.setEditorMode(name, 0)

    def _get_props(self, group=None):
        props = super()._get_props(group)
        if self.get_subtype() != "plasma":
            return props

        hidden = {"Material", "SpindleDirection", *self._LEGACY_PROBE_PARAMETERS}
        return [prop for prop in props if prop not in hidden]

    @property
    def summary(self) -> str:
        if self.get_subtype() == "plasma":
            kerf_width = self.get_property_str("KerfWidth", "?", precision=3)
            cut_height = self.get_property_str("CutHeight", "?", precision=3)
            return FreeCAD.Qt.translate(
                "CAM", f"Plasma torch, {kerf_width} kerf, {cut_height} cut height"
            )

        diameter = self.get_property_str("Diameter", "?", precision=3)
        length = self.get_property_str("Length", "?", precision=3)
        shaft_diameter = self.get_property_str("ShaftDiameter", "?", precision=3)

        return FreeCAD.Qt.translate(
            "CAM", f"{diameter} probe, {length} length, {shaft_diameter} shaft"
        )

    def can_rotate(self) -> bool:
        return False

    # Connor: Add getters and setters for Diameter and Length
    def get_diameter(self) -> FreeCAD.Units.Quantity:
        """
        Get the diameter of the rotary tool bit from the shape.
        """
        return self.obj.Diameter

    def set_diameter(self, diameter: FreeCAD.Units.Quantity):
        """
        Set the diameter of the rotary tool bit on the shape.
        """
        if not isinstance(diameter, FreeCAD.Units.Quantity):
            raise ValueError("Diameter must be a FreeCAD Units.Quantity")
        self.obj.Diameter = diameter

    def get_length(self) -> FreeCAD.Units.Quantity:
        """
        Get the length of the rotary tool bit from the shape.
        """
        return self.obj.Length

    def set_length(self, length: FreeCAD.Units.Quantity):
        """
        Set the length of the rotary tool bit on the shape.
        """
        if not isinstance(length, FreeCAD.Units.Quantity):
            raise ValueError("Length must be a FreeCAD Units.Quantity")
        self.obj.Length = length
