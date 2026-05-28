from bpy.props import EnumProperty, FloatProperty, IntProperty, StringProperty, BoolProperty, CollectionProperty
from bpy.types import Context, PropertyGroup

from typing import overload

from sbstudio.plugin.constants import Collections
from sbstudio.plugin.props.color import ColorProperty
from sbstudio.plugin.utils.pyro_markers import update_pyro_particles_of_object
from sbstudio.plugin.overlays.pyro import (
    PyroOverlay,
    PyroOverlayInfo,
    PyroOverlayMarker,
)

__all__ = ("PyroChannelOption", "PyroControlPanelProperties", "get_default_pyro_channel_options")


def _get_channel_enum_items(self, context):
    """Callback for channel EnumProperty - returns custom channels from scene."""
    if context and hasattr(context, 'scene'):
        scene = context.scene
        if scene and hasattr(scene, 'skybrush'):
            pyro_control = scene.skybrush.pyro_control
            if pyro_control and hasattr(pyro_control, 'custom_channels'):
                items = []
                for channel in pyro_control.custom_channels:
                    items.append((str(channel.channel_index), channel.effect_name, channel.description or ""))
                if items:
                    return items
    # Fallback: return all 256 channels
    return [(str(i), str(i), "") for i in range(256)]


def get_default_pyro_channel_options():
    """Return the default pyro channel options."""
    return []


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


class PyroChannelOption(PropertyGroup):
    """PropertyGroup for custom pyro channel options."""
    
    channel_index: IntProperty(
        name="Channel Index",
        description="The channel index (0-255)",
        min=0,
        max=255,
        default=0
    )
    
    effect_name: StringProperty(
        name="Effect Name",
        description="The name of the pyro effect",
        default="Custom Effect"
    )
    
    description: StringProperty(
        name="Description",
        description="Additional description of the effect",
        default=""
    )
    
    prefire_time: FloatProperty(
        name="Prefire time",
        description="The time needed for the pyro effect to show up after it gets triggered",
        min=0,
        unit="TIME",
        step=100,  # button step is 1/100th of step
    )


def get_pyro_channel_options():
    """Get the combined list of static and custom pyro channel options."""
    import bpy
    
    options = list(get_default_pyro_channel_options())
    
    # Add custom channels if available
    try:
        scene = bpy.context.scene
        if scene and hasattr(scene, 'skybrush'):
            pyro_control = scene.skybrush.pyro_control
            if pyro_control and hasattr(pyro_control, 'custom_channels'):
                for channel in pyro_control.custom_channels:
                    index_str = str(channel.channel_index)
                    # Replace the default option if it exists and has no custom name
                    replaced = False
                    for i, (value, name, desc) in enumerate(options):
                        if value == index_str and name == index_str:
                            # Replace the generic entry with the custom one
                            options[i] = (index_str, channel.effect_name, channel.description or "")
                            replaced = True
                            break
                    if not replaced and 0 <= channel.channel_index < 256:
                        # Add new custom channel if not already in the list
                        options.append((index_str, channel.effect_name, channel.description or ""))
    except (AttributeError, TypeError):
        # Context not available or scene doesn't have skybrush
        pass
    
    return options


class PyroControlPanelProperties(PropertyGroup):
    visualization = EnumProperty(
        items=[
            ("NONE", "None", "No rendering is very quick but invisible", 1),
            ("MARKERS", "Markers", "Markers are simple but quick", 2),
            ("PARTICLES", "Particles", "Particles are spectacular but slow", 3),
            ("INFO", "Info", "Static pyro info for aiding pre-flight handling", 4),
        ],
        name="Visualization",
        description=("The visualization method of the pyro effect."),
        default="MARKERS",
        update=visualization_updated,
    )

    channel = EnumProperty(
        name="Channel",
        description="The pyro channel and effect type",
        items=_get_channel_enum_items,
        default=1,
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

    # TODO: add yaw and pitch angle relative to the drone, if needed

    pitch = IntProperty(
        name="Pitch",
        description="The pitch angle of the pyro effect",
        default=0,
        min=-180,
        max=180
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

    primary_color = ColorProperty(
        name="Primary Color",
        description="The primary color of the pyro effect",
        default=(1.0, 1.0, 1.0)
    )

    secondary_color = ColorProperty(
        name="Secondary Color",
        description="The secondary color of the pyro effect",
        default=(0.0, 0.0, 0.0)
    )

    volume = FloatProperty(
        name="Volume",
        description="The volume level of the pyro effect (0 to 1)",
        default=1.0,
        min=0.0,
        max=1.0,
        step=10  # button step is 1/10th of step
    )

    show_frame_effects = BoolProperty(
        name="Show Frame Effects",
        description="Show all pyro effects fired on the current frame",
        default=True,
    )

    custom_channels: CollectionProperty(
        name="Custom Channels",
        description="Custom pyro channel configurations",
        type=PyroChannelOption,
    )

    custom_channels_index: IntProperty(
        name="Custom Channels Index",
        description="Index of the active custom channel",
        default=0,
        min=0,
    )

    def get_current_channel_custom_info(self) -> PyroChannelOption | None:
        """Get the custom channel info for the currently selected channel, if it exists."""
        channel_idx = int(self.channel)
        for custom_channel in self.custom_channels:
            if custom_channel.channel_index == channel_idx:
                return custom_channel
        return None

    def clear_pyro_overlay_markers(self) -> None:
        """Clears the pyro overlay markers."""
        self.ensure_overlays_enabled_if_needed()

        overlay = get_overlay(create=False)
        if overlay:
            overlay.markers = []

    def ensure_overlays_enabled_if_needed(self) -> None:
        get_overlay().enabled = self.visualization in ["MARKERS", "INFO"]

    def update_pyro_overlay_markers(self, markers: list[PyroOverlayMarker]) -> None:
        """Updates the pyro overlay markers."""
        self.ensure_overlays_enabled_if_needed()

        overlay = get_overlay(create=False)
        if overlay:
            overlay.markers = markers

    def update_pyro_overlay_info_blocks(
        self, info_blocks: list[PyroOverlayInfo]
    ) -> None:
        """Updates the pyro overlay info blocks."""
        self.ensure_overlays_enabled_if_needed()

        overlay = get_overlay(create=False)
        if overlay:
            overlay.info_blocks = info_blocks
