"""Overlay for rendering drone colors based on light effects using GPU shaders."""

from __future__ import annotations

import gpu
from gpu_extras.batch import batch_for_shader
from typing import TYPE_CHECKING

from sbstudio.model.types import Coordinate3D

from .base import ShaderOverlay

if TYPE_CHECKING:
    from gpu.types import GPUBatch

__all__ = ("LightEffectsOverlay",)

Color = tuple[float, float, float, float]
"""Type alias for RGBA colors in this module."""

LightEffectsMarker = tuple[Coordinate3D, Color]
"""Type specification for a single light effect marker: position and RGBA color."""


class LightEffectsOverlay(ShaderOverlay):
    """Overlay that renders drone colors based on light effects using GPU shaders."""

    shader_type = "FLAT_COLOR"

    _markers: list[LightEffectsMarker] | None = None
    _shader_batches: list[GPUBatch] | None = None

    @property
    def markers(self) -> list[LightEffectsMarker] | None:
        return self._markers

    @markers.setter
    def markers(self, value: list[LightEffectsMarker] | None):
        if value is not None:
            self._markers = []
            for point, color in value:
                marker = (
                    tuple(float(c) for c in point),
                    tuple(float(c) for c in color),
                )
                self._markers.append(marker)  # type: ignore
        else:
            self._markers = None

        self._shader_batches = None

    def _create_shader_batches(self) -> list[GPUBatch]:
        """Create shader batches for rendering light effect markers as points."""
        if self._markers is None:
            return []

        assert self._shader is not None

        batches: list[GPUBatch] = []
        points: list[tuple[float, float, float]] = []
        colors: list[tuple[float, float, float, float]] = []

        # Sort markers by z-coordinate in descending order (back to front)
        sorted_markers = sorted(self._markers, key=lambda m: m[0][2], reverse=False)

        for position, color in sorted_markers:
            points.append(tuple(position))
            colors.append(color)

        if points:
            batch = batch_for_shader(
                self._shader,
                "POINTS",
                {"pos": points, "color": colors},
            )
            batches.append(batch)

        return batches

    def draw_3d(self) -> None:
        if self._markers is None:
            return

        assert self._shader is not None

        if self._shader_batches is None:
            self._shader_batches = self._create_shader_batches()

        if self._shader_batches:
            self._shader.bind()
            for batch in self._shader_batches:
                batch.draw(self._shader)

    def dispose(self) -> None:
        """Clean up shader batches when overlay is disabled."""
        self._shader_batches = None
