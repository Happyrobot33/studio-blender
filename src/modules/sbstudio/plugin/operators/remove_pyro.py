from bpy.props import FloatProperty, IntProperty, StringProperty
from bpy.types import Operator

from sbstudio.plugin.constants import NUM_PYRO_CHANNELS
from sbstudio.model.pyro_markers import PyroMarker, PyroPayload
from sbstudio.plugin.selection import get_selected_drones
from sbstudio.plugin.utils.pyro_markers import remove_pyro_marker_from_object
from sbstudio.plugin.constants import Collections

__all__ = ("RemovePyroOnSelectedDronesOperator",)


class RemovePyroOnSelectedDronesOperator(Operator):

    bl_idname = "skybrush.remove_pyro_on_selection"
    bl_label = "Remove Pyro on Selected Drones"
    bl_description = (
        "Removes pyro effects at the current frame"
        "on the currently selected drones"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # This code path is invoked after an undo-redo
        return {"FINISHED"} if self._run(context) else {"CANCELLED"}

    def invoke(self, context, event):
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
            self.report({"INFO"}, "Select some drones first to remove pyro")
            return False

        frame = context.scene.frame_current
        for drone in selection:
            self._remove_pyro_on_single_drone(drone, frame)
        
        from sbstudio.plugin.operators import CalculatePyroMarkers
        CalculatePyroMarkers._recalculate_pyro_markers(context)

        return True

    def _remove_pyro_on_single_drone(self, drone, frame: int):
        remove_pyro_marker_from_object(
            drone,
            frame=frame,
        )
