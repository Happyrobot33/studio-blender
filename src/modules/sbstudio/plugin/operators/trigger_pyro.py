from bpy.props import FloatProperty, IntProperty, StringProperty
from bpy.types import Operator

from sbstudio.plugin.constants import NUM_PYRO_CHANNELS
from sbstudio.model.pyro_markers import PyroMarker, PyroPayload
from sbstudio.plugin.selection import get_selected_drones
from sbstudio.plugin.utils.pyro_markers import add_pyro_marker_to_object, get_pyro_markers_of_object
from sbstudio.plugin.constants import Collections

__all__ = ("TriggerPyroOnSelectedDronesOperator",)


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

    channel = IntProperty(
        name="Channel",
        description="The (1-based) channel index the pyro is attached to",
        min=0,
        max=NUM_PYRO_CHANNELS,
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

    def execute(self, context):
        # This code path is invoked after an undo-redo
        return {"FINISHED"} if self._run(context) else {"CANCELLED"}

    def invoke(self, context, event):
        # Inherit properties from the Pyro control panel
        pyro_control = context.scene.skybrush.pyro_control

        self.channel = pyro_control.channel
        self.name = pyro_control.name
        self.duration = pyro_control.duration
        self.prefire_time = pyro_control.prefire_time
        self.pitch = pyro_control.pitch
        self.yaw = pyro_control.yaw
        self.roll = pyro_control.roll

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
                channel=self.channel,
                payload=PyroPayload(
                    name=self.name,
                    duration=self.duration,
                    prefire_time=self.prefire_time,
                ),
                pitch=self.pitch,
                yaw=self.yaw,
                roll=self.roll
            ),
        )
