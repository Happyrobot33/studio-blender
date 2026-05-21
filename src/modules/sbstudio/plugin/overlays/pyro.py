from __future__ import annotations

import blf
import bpy
import gpu
import gpu.state
import math

from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy.types import SpaceView3D
from gpu_extras.batch import batch_for_shader
from typing import TYPE_CHECKING, cast
from mathutils import Matrix, Vector

from sbstudio.model.types import Coordinate3D

from .base import ShaderOverlay

if TYPE_CHECKING:
    from sbstudio.plugin.model.pyro_control import PyroControlPanelProperties
    from gpu.types import GPUBatch

__all__ = (
    "PyroOverlay",
    "PyroOverlayMarker",
)

Color = tuple[float, float, float]
"""Type alias for RGB colors in this module."""

PyroOverlayInfo = tuple[Coordinate3D, list[str]]
"""Type specification for a single info block on the overlay. An info block requires 
a single coordinate and a list of text strings (one per line).
"""

PyroOverlayMarker = tuple[Coordinate3D, Color, float, float, float]
"""Type specification for a single marker on the overlay. A marker requires 
a single coordinate, a Color, and yaw/pitch/roll angles in degrees.
"""

DEFAULT_PYRO_OVERLAY_MARKER_COLOR: Color = (0.5, 0.5, 0.5)
DEFAULT_PYRO_OVERLAY_DIRECTION_COLOR: Color = (1.0, 0.0, 0.0)
DEFAULT_PYRO_OVERLAY_YAW_COLOR: Color = (0.0, 1.0, 0.0)
"""Default color for pyro marker overlays."""


class PyroOverlay(ShaderOverlay):
    """Overlay that marks pyro drones in the 3D view."""

    shader_type = "FLAT_COLOR"

    _info_blocks: list[PyroOverlayInfo] | None = None
    _markers: list[PyroOverlayMarker] | None = None
    _shader_batches: list[GPUBatch] | None = None

    @property
    def info_blocks(self) -> list[PyroOverlayInfo] | None:
        return self._info_blocks

    @info_blocks.setter
    def info_blocks(self, value: list[PyroOverlayInfo] | None):
        if value is not None:
            self._info_blocks = []
            for point, lines in value:
                info_block = (
                    tuple(float(c) for c in point),
                    lines,
                )
                self._info_blocks.append(info_block)  # type: ignore

        else:
            self._info_blocks = None

        # self._shader_batches = None

    @property
    def markers(self) -> list[PyroOverlayMarker] | None:
        return self._markers

    @markers.setter
    def markers(self, value: list[PyroOverlayMarker] | None):
        if value is not None:
            self._markers = []
            for point, color, yaw, pitch, roll in value:
                marker = (
                    tuple(float(c) for c in point),
                    tuple(float(c) for c in color),
                    float(yaw),
                    float(pitch),
                    float(roll),
                )
                self._markers.append(marker)  # type: ignore

        else:
            self._markers = None

        self._shader_batches = None

    def draw_2d(self) -> None:
        context = bpy.context
        skybrush = getattr(context.scene, "skybrush", None)
        pyro_control: PyroControlPanelProperties | None = getattr(
            skybrush, "pyro_control", None
        )
        if (
            not pyro_control
            or self._info_blocks is None
            or pyro_control.visualization != "INFO"
        ):
            return

        space_data = context.space_data
        if space_data.type != "VIEW_3D":
            return

        space_data = cast(SpaceView3D, space_data)
        if not hasattr(space_data, "overlay") or not bool(
            getattr(space_data.overlay, "show_overlays", False)
        ):
            return

        font_id = 0
        ui_scale = self.get_ui_scale()
        region = context.region
        region_3d = context.region_data
        font_size = int(11 * ui_scale)
        line_height = font_size + 2

        if bpy.app.version >= (4, 0, 0):
            # DPI argument was removed in Blender 4.0
            blf.size(font_id, font_size)
        else:
            blf.size(font_id, font_size, 72)
        blf.enable(font_id, blf.SHADOW)
        blf.color(font_id, 1, 1, 1, 1)

        for info_block in self._info_blocks:
            num_lines = len(info_block[1])
            x, y = location_3d_to_region_2d(region, region_3d, info_block[0])
            y += (num_lines - 3 / 2) * font_size / 2
            for line in info_block[1]:
                blf.position(font_id, x, y, 0)
                blf.draw(font_id, line)
                y -= line_height

    def draw_3d(self) -> None:
        gpu.state.blend_set("ALPHA")

        skybrush = getattr(bpy.context.scene, "skybrush", None)
        pyro_control: PyroControlPanelProperties | None = getattr(
            skybrush, "pyro_control", None
        )
        if not pyro_control or pyro_control.visualization not in ["MARKERS", "INFO"]:
            return

        if self._markers is not None:
            assert self._shader is not None

            if self._shader_batches is None:
                self._shader_batches = self._create_shader_batches()

            if self._shader_batches:
                self._shader.bind()
                gpu.state.point_size_set(30)
                for batch in self._shader_batches:
                    batch.draw(self._shader)

    def dispose(self) -> None:
        super().dispose()
        self._shader_batches = None

    def _create_shader_batches(self) -> list[GPUBatch]:
        assert self._shader is not None

        points: list[Coordinate3D] = []
        colors: list[tuple[float, ...]] = []

        # Define fixed colors for arrows
        firing_color = (1.0, 0.0, 0.0)  # Red for firing direction
        roll_color = (1.0, 1.0, 1.0)    # White for roll representation

        # For each marker, draw two arrows: one for firing direction, one for roll
        for marker_data in self._markers or ():
            point, color, yaw, pitch, roll = marker_data
            x, y, z = point
            
            # Convert angles from degrees to radians
            yaw_rad = math.radians(yaw)
            pitch_rad = math.radians(pitch)
            roll_rad = math.radians(roll)
            
            # Arrow 1: Firing direction (forward direction) - RED
            # Yaw and pitch determine firing direction
            shaft_length = 2.5
            arrow1_forward = Vector((0, 0, shaft_length))
            arrow1_head_size = 0.5
            arrow1_head_point = Vector((0, 0, shaft_length))
            arrow1_head_left = Vector((0.25, 0, shaft_length - arrow1_head_size))
            arrow1_head_right = Vector((-0.25, 0, shaft_length - arrow1_head_size))
            
            # Apply yaw and pitch only for firing direction (no roll)
            # Using same order as original: pitch (Y) -> yaw (Z, negated)
            rot_pitch = Matrix.Rotation(pitch_rad, 4, 'Y')
            rot_yaw = Matrix.Rotation(-yaw_rad, 4, 'Z')
            rot_matrix_firing = rot_yaw @ rot_pitch
            
            # Apply rotation
            arrow1_forward = rot_matrix_firing @ arrow1_forward
            arrow1_head_point = rot_matrix_firing @ arrow1_head_point
            arrow1_head_left = rot_matrix_firing @ arrow1_head_left
            arrow1_head_right = rot_matrix_firing @ arrow1_head_right
            
            # Arrow 1 shaft
            points.append(tuple(point))
            points.append(tuple(Vector(point) + arrow1_forward))
            colors.append(firing_color)
            colors.append(firing_color)
            
            # Arrow 1 head
            arrow1_back = Vector(point) + arrow1_forward * (1 - arrow1_head_size / shaft_length)
            points.append(tuple(arrow1_back))
            points.append(tuple(Vector(point) + arrow1_head_left))
            colors.append(firing_color)
            colors.append(firing_color)
            
            points.append(tuple(arrow1_back))
            points.append(tuple(Vector(point) + arrow1_head_right))
            colors.append(firing_color)
            colors.append(firing_color)
            
            points.append(tuple(Vector(point) + arrow1_head_left))
            points.append(tuple(Vector(point) + arrow1_head_right))
            colors.append(firing_color)
            colors.append(firing_color)
            
            # Arrow 2: Roll direction (shows Z-axis rotation) - WHITE
            arrow2_forward = Vector((shaft_length, 0, 0))  # Start pointing along X-axis
            arrow2_head_size = 0.5
            arrow2_head_point = Vector((shaft_length, 0, 0))
            arrow2_head_left = Vector((shaft_length - arrow2_head_size, 0.25, 0))
            arrow2_head_right = Vector((shaft_length - arrow2_head_size, -0.25, 0))
            
            # Apply rotations in the same order as the original code:
            # roll (Z) -> pitch (Y) -> yaw (Z, negated)
            rot_roll = Matrix.Rotation(roll_rad, 4, 'Z')
            rot_pitch = Matrix.Rotation(pitch_rad, 4, 'Y')
            rot_yaw = Matrix.Rotation(-yaw_rad, 4, 'Z')
            rot_matrix_roll = rot_yaw @ rot_pitch @ rot_roll
            
            arrow2_forward = rot_matrix_roll @ arrow2_forward
            arrow2_head_point = rot_matrix_roll @ arrow2_head_point
            arrow2_head_left = rot_matrix_roll @ arrow2_head_left
            arrow2_head_right = rot_matrix_roll @ arrow2_head_right
            
            # Arrow 2 shaft
            points.append(tuple(point))
            points.append(tuple(Vector(point) + arrow2_forward))
            colors.append(roll_color)
            colors.append(roll_color)
            
            # Arrow 2 head
            arrow2_back = Vector(point) + arrow2_forward * (1 - arrow2_head_size / shaft_length)
            points.append(tuple(arrow2_back))
            points.append(tuple(Vector(point) + arrow2_head_left))
            colors.append(roll_color)
            colors.append(roll_color)
            
            points.append(tuple(arrow2_back))
            points.append(tuple(Vector(point) + arrow2_head_right))
            colors.append(roll_color)
            colors.append(roll_color)
            
            points.append(tuple(Vector(point) + arrow2_head_left))
            points.append(tuple(Vector(point) + arrow2_head_right))
            colors.append(roll_color)
            colors.append(roll_color)

        # Construct the shader batch to draw the arrows
        batches: list[GPUBatch] = [
            batch_for_shader(self._shader, "LINES", {"pos": points, "color": colors}),
        ]

        return batches
