"""Background task that is invoked after every frame change and draws
markers on drones when their pyro effect is active.
"""

from __future__ import annotations
import math
import numpy as np

import bpy

from contextlib import contextmanager
from typing import Iterator, TYPE_CHECKING

from sbstudio.plugin.constants import Collections
from sbstudio.plugin.overlays.pyro import (
    DEFAULT_PYRO_OVERLAY_MARKER_COLOR,
    DEFAULT_PYRO_OVERLAY_DIRECTION_COLOR,
    DEFAULT_PYRO_OVERLAY_YAW_COLOR,
    PyroOverlayInfo,
    PyroOverlayMarker,
)
from sbstudio.plugin.utils.evaluator import get_position_of_object
from sbstudio.plugin.utils.pyro_markers import get_pyro_markers_of_object

# from sbstudio.plugin.utils import debounced

from .base import Task

if TYPE_CHECKING:
    from bpy.types import Scene

_suspension_counter = 0
"""Suspension counter. Pyro marker overlay is suspended if this counter is positive."""

def rotatearoundaxis(pos, axis, angle) -> tuple[float, float, float]:
    """Rotate position pos around axis by angle (in radians)"""
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(angle / 2.0)
    b, c, d = -axis * math.sin(angle / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = (
        b * c,
        a * d,
        a * c,
        a * b,
        b * d,
        c * d,
    )
    rotation_matrix = np.array(
        [
            [aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
            [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
            [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc],
        ]
    )
    rotated_pos = np.dot(rotation_matrix, np.asarray(pos))
    return (rotated_pos[0], rotated_pos[1], rotated_pos[2])

# @debounced(delay=0.1)
def run_update_pyro_overlay_markers(scene: Scene, depsgraph) -> None:
    global _suspension_counter
    if _suspension_counter > 0:
        return

    pyro_control = scene.skybrush.pyro_control

    if pyro_control.visualization in ["MARKERS", "INFO"]:
        drones = Collections.find_drones(create=False)
    else:
        drones = None

    if not drones:
        pyro_control.clear_pyro_overlay_markers()
        return

    # Get position of drones from the current frame that have
    # active pyro effect at the moment
    frame = scene.frame_current
    fps = scene.render.fps
    overlay_markers: list[PyroOverlayMarker] = []
    overlay_info_blocks: list[PyroOverlayInfo] = []
    for drone in drones.objects:
        markers = get_pyro_markers_of_object(drone)
        if markers is None:
            continue

        #print markers
        print(frame, markers)
        if frame not in markers.markers:
            continue

        position = get_position_of_object(drone)
        # TODO: change color with pyro channel
        color = DEFAULT_PYRO_OVERLAY_MARKER_COLOR
        overlay_markers.append((position, color))
        #add a SECOND marker showing the direction of the pyro
        marker = markers.markers[frame]

        directionposition = (0, 0, 1) #default is up
        yawindicatorposition = (0, 1, 0) #a point to indicate yaw direction
        #convert pitch yaw roll to radians
        pitch = math.radians(marker.pitch)
        yaw = math.radians(marker.yaw)
        roll = math.radians(marker.roll)

        #rotate around z axis by roll
        directionposition = rotatearoundaxis(directionposition, (0, 0, 1), roll)
        yawindicatorposition = rotatearoundaxis(yawindicatorposition, (0, 0, 1), roll)
        #rotate around x axis by pitch
        directionposition = rotatearoundaxis(directionposition, (0, 1, 0), pitch)
        yawindicatorposition = rotatearoundaxis(yawindicatorposition, (0, 1, 0), pitch)
        #rotate around y axis by yaw
        directionposition = rotatearoundaxis(directionposition, (0, 0, 1), -yaw)
        yawindicatorposition = rotatearoundaxis(yawindicatorposition, (0, 0, 1), -yaw)

        #add the drone position
        directionposition = np.add(position, directionposition)
        yawindicatorposition = np.add(position, yawindicatorposition)
        overlay_markers.append((tuple(directionposition), DEFAULT_PYRO_OVERLAY_DIRECTION_COLOR))
        overlay_markers.append((tuple(yawindicatorposition), DEFAULT_PYRO_OVERLAY_YAW_COLOR))

    pyro_control.update_pyro_overlay_markers(overlay_markers)
    pyro_control.update_pyro_overlay_info_blocks(overlay_info_blocks)


def ensure_overlays_enabled():
    """Ensures that the pyro marker overlay is enabled after loading a file."""
    pyro_control = bpy.context.scene.skybrush.pyro_control
    pyro_control.ensure_overlays_enabled_if_needed()


def run_tasks_post_load(*args):
    """Runs all the tasks that should be completed after loading a file."""
    ensure_overlays_enabled()


@contextmanager
def suspended_pyro_effects() -> Iterator[None]:
    """Context manager that suspends pyro marker overlay when the context is entered
    and re-enables them when the context is exited.
    """
    global _suspension_counter
    _suspension_counter += 1
    try:
        yield
    finally:
        _suspension_counter -= 1


class PyroEffectsTask(Task):
    """Background task that is invoked after every frame change and that
    updates pyro overlay markers if needed.
    """

    functions = {
        "depsgraph_update_post": run_update_pyro_overlay_markers,
        "frame_change_post": run_update_pyro_overlay_markers,
        "load_post": run_tasks_post_load,
    }
