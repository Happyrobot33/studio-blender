from bpy.props import FloatProperty, IntProperty, StringProperty
from bpy.types import Operator

from sbstudio.plugin.constants import NUM_PYRO_CHANNELS
from sbstudio.model.pyro_markers import PyroMarker, PyroPayload
from sbstudio.plugin.selection import get_selected_drones
from sbstudio.plugin.utils.pyro_markers import add_pyro_marker_to_object, get_pyro_markers_of_object
from sbstudio.plugin.constants import Collections

__all__ = ("CalculatePyroMarkers",)


class CalculatePyroMarkers(Operator):

    bl_idname = "skybrush.calculate_pyro_markers"
    bl_label = "Calculate Pyro Markers"
    bl_description = (
        "Calculates and updates the timeline markers for pyro effects"
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
        
        CalculatePyroMarkers._recalculate_pyro_markers(context)

        return True
    
    def _recalculate_pyro_markers(context):
        #get all the pyro triggers
        scene = context.scene

        markers = scene.timeline_markers
        for m in markers:
            if m.name.startswith("Pyro"):
                markers.remove(m)

        drones = Collections.find_drones(create=False)

        for drone in drones.objects:
            markers = get_pyro_markers_of_object(drone)
            for frame in markers.markers:
                channel = markers.markers[frame].channel
                pitch = markers.markers[frame].pitch
                yaw = markers.markers[frame].yaw
                roll = markers.markers[frame].roll
                prefire = markers.markers[frame].payload.prefire_time
                m = scene.timeline_markers.new(name=f"Pyro {channel} on {drone.name}, Pitch: {pitch}, Yaw: {yaw}, Roll: {roll} Prefire: {prefire}", frame=frame)
