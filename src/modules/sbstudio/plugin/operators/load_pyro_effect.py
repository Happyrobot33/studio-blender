"""Operator to load a pyro effect's values into the inspector."""

from bpy.types import Context, Operator
from bpy.props import StringProperty, IntProperty

__all__ = ("PYRO_OT_load_effect",)


class PYRO_OT_load_effect(Operator):
    """Load a pyro effect's values into the inspector."""
    
    bl_idname = "pyro.load_effect"
    bl_label = "Load Pyro Effect"
    bl_options = {'REGISTER', 'UNDO'}
    
    drone_name: StringProperty(
        name="Drone Name",
        description="Name of the drone with the effect",
    )
    
    frame: IntProperty(
        name="Frame",
        description="Frame number of the effect",
        default=0,
    )
    
    def execute(self, context: Context):
        scene = context.scene
        
        # Get the drone object
        drone = scene.objects.get(self.drone_name)
        if not drone:
            self.report({'ERROR'}, f"Drone '{self.drone_name}' not found")
            return {'CANCELLED'}
        
        # Get the pyro markers for this drone
        from sbstudio.plugin.utils.pyro_markers import get_pyro_markers_of_object
        markers = get_pyro_markers_of_object(drone)
        
        if self.frame not in markers.markers:
            self.report({'ERROR'}, f"No effect found on frame {self.frame}")
            return {'CANCELLED'}
        
        # Get the marker and load its values
        marker = markers.markers[self.frame]
        pyro_control = scene.skybrush.pyro_control
        
        pyro_control.channel = str(marker.channel)
        pyro_control.name = marker.payload.name
        pyro_control.duration = marker.payload.duration
        
        # Load prefire_time into the channel's custom info if available
        custom_channel = pyro_control.get_current_channel_custom_info()
        if custom_channel:
            custom_channel.prefire_time = marker.payload.prefire_time
        
        pyro_control.pitch = marker.pitch
        pyro_control.yaw = marker.yaw
        pyro_control.roll = marker.roll
        pyro_control.primary_color = marker.primary_color
        pyro_control.secondary_color = marker.secondary_color
        pyro_control.volume = marker.volume
        
        return {'FINISHED'}
