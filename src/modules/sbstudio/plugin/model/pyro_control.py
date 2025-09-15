from bpy.props import EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Context, PropertyGroup

from typing import overload

from sbstudio.plugin.constants import Collections, NUM_PYRO_CHANNELS

from sbstudio.plugin.utils.pyro_markers import update_pyro_particles_of_object
from sbstudio.plugin.overlays.pyro import (
    PyroOverlay,
    PyroOverlayMarker,
)

__all__ = ("PyroControlPanelProperties",)

#: Global pyro marker overlay. This cannot be an attribute of PyroControlPanelProperties
#: for some reason; Blender PropertyGroup objects are weird.
_overlay = None


@overload
def get_overlay() -> PyroOverlay: ...


@overload
def get_overlay(create: bool) -> PyroOverlay | None: ...


def get_overlay(create: bool = True):
    global _overlay

    if _overlay is None and create:
        _overlay = PyroOverlay()

    return _overlay


def visualization_updated(
    self: "PyroControlPanelProperties", context: Context | None = None
):
    """Called when user changes the visualization type of pyro effects."""
    drones = Collections.find_drones(create=False)

    if not drones:
        return

    for drone in drones.objects:
        update_pyro_particles_of_object(drone)


class PyroControlPanelProperties(PropertyGroup):
    visualization = EnumProperty(
        items=[
            ("NONE", "None", "No rendering is very quick but invisible", 1),
            ("MARKERS", "Markers", "Markers are simple but quick", 2),
            ("PARTICLES", "Particles", "Particles are spectacular but slow", 3),
        ],
        name="Visualization",
        description=("The visualization method of the pyro effect."),
        default="MARKERS",
        update=visualization_updated,
    )

    channel = IntProperty(
        name="Channel",
        description="The (1-based) channel index the pyro is attached to",
        default=1,
        min=1,
        max=NUM_PYRO_CHANNELS,
    )

    # pyro payload properties

    name = StringProperty(
        name="Name",
        description="Name of the pyro effect to trigger",
        default="30s Gold Glittering Gerb",
    )

    duration = FloatProperty(
        name="Duration",
        description="The duration of the pyro effect",
        default=30,
        min=0.1,
        unit="TIME",
        step=100,  # button step is 1/100th of step
    )

    prefire_time = FloatProperty(
        name="Prefire time",
        description="The time needed for the pyro effect to show up after it gets triggered",
        min=0,
        unit="TIME",
        step=100,  # button step is 1/100th of step
    )

    # TODO: add yaw and pitch angle relative to the drone, if needed

    pitch = IntProperty(
        name="Pitch",
        description="The pitch angle of the pyro effect",
        default=0,
        min=-90,
        max=90
    )

    yaw = IntProperty(
        name="Yaw",
        description="The yaw angle of the pyro effect",
        default=0,
        min=-180,
        max=180
    )

    roll = IntProperty(
        name="Roll",
        description="The roll angle of the pyro effect",
        default=0,
        min=-180,
        max=180
    )

    def clear_pyro_overlay_markers(self) -> None:
        """Clears the pyro overlay markers."""
        self.ensure_overlays_enabled_if_needed()

        overlay = get_overlay(create=False)
        if overlay:
            overlay.markers = []

    def ensure_overlays_enabled_if_needed(self) -> None:
        get_overlay().enabled = self.visualization == "MARKERS"

    def update_pyro_overlay_markers(self, markers: list[PyroOverlayMarker]) -> None:
        """Updates the pyro overlay markers."""
        self.ensure_overlays_enabled_if_needed()

        overlay = get_overlay(create=False)
        if overlay:
            overlay.markers = markers
