from bpy.props import EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Operator

from sbstudio.plugin.props.color import ColorProperty
from sbstudio.model.pyro_markers import PyroMarker, PyroPayload
from sbstudio.plugin.selection import get_selected_drones
from sbstudio.plugin.utils.pyro_markers import add_pyro_marker_to_object, get_pyro_markers_of_object
from sbstudio.plugin.constants import Collections

__all__ = ("TriggerPyroOnSelectedDronesOperator",)


def _get_channel_items_for_operator(self, context):
    """Callback for operator channel EnumProperty - returns custom channels from scene."""
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


class TriggerPyroOnSelectedDronesOperator(Operator):
    """Triggers the defined pyro effect of the Pyro control panel
    on the currently selected drones."""

    bl_idname = "skybrush.trigger_pyro_on_selection"
    bl_label = "Trigger Pyro on Selected Drones"
    bl_description = (
        "Triggers the defined pyro effect of the Pyro control panel "
        "on the currently selected drones"
    )
    bl_options = {"REGISTER", "UNDO"}

    channel = EnumProperty(
        name="Channel",
        description="The pyro channel and effect type",
        items=_get_channel_items_for_operator,
        default=1,
    )

    name = StringProperty(
        name="Name",
        description="Descriptor of the pyro effect to trigger",
    )

    duration = FloatProperty(
        name="Duration",
        description="The duration of the pyro effect",
        default=30,
        min=0,
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
        step=10
    )

    def execute(self, context):
        # This code path is invoked after an undo-redo
        return {"FINISHED"} if self._run(context) else {"CANCELLED"}

    def invoke(self, context, event):
        # Inherit properties from the Pyro control panel
        pyro_control = context.scene.skybrush.pyro_control

        self.channel = pyro_control.channel
        self.name = pyro_control.name
        self.duration = pyro_control.duration
        
        # Get prefire_time from the channel's custom info if available
        custom_channel = pyro_control.get_current_channel_custom_info()
        self.prefire_time = custom_channel.prefire_time if custom_channel else 0
        
        self.pitch = pyro_control.pitch
        self.yaw = pyro_control.yaw
        self.roll = pyro_control.roll
        self.primary_color = pyro_control.primary_color
        self.secondary_color = pyro_control.secondary_color
        self.volume = pyro_control.volume

        if event.type == "LEFTMOUSE":
            # We are being invoked from a button in the Pyro control panel.
            # Move on straight to the execution phase.
            return self.execute(context)
        else:
            # We are probably being invoked from the Blender command palette
            # so show the props dialog.
            return context.window_manager.invoke_props_dialog(self)

    def _run(self, context):
        selection = get_selected_drones()
        num_selected = len(selection)
        if not num_selected:
            self.report({"INFO"}, "Select some drones first to trigger pyro")
            return False

        frame = context.scene.frame_current
        for drone in selection:
            self._trigger_pyro_on_single_drone(drone, frame)
        
        from sbstudio.plugin.operators import CalculatePyroMarkers
        CalculatePyroMarkers._recalculate_pyro_markers(context)

        return True

    def _trigger_pyro_on_single_drone(self, drone, frame: int):
        print(self.pitch, self.yaw, self.roll)
        add_pyro_marker_to_object(
            drone,
            frame=frame,
            marker=PyroMarker(
                channel=int(self.channel),
                payload=PyroPayload(
                    name=self.name,
                    duration=self.duration,
                    prefire_time=self.prefire_time,
                ),
                pitch=self.pitch,
                yaw=self.yaw,
                roll=self.roll,
                primary_color=tuple(self.primary_color),
                secondary_color=tuple(self.secondary_color),
                volume=self.volume
            ),
        )
