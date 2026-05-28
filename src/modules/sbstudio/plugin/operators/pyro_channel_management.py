"""Operators for managing custom pyro channel configurations."""

from bpy.types import Context, Operator
from bpy.props import IntProperty


__all__ = (
    "AddPyroChannelOperator",
    "RemovePyroChannelOperator",
    "UpdatePyroChannelMarkersOperator",
)


class AddPyroChannelOperator(Operator):
    """Add a new custom pyro channel."""
    
    bl_idname = "skybrush.add_pyro_channel"
    bl_label = "Add Pyro Channel"
    bl_description = "Add a new custom pyro channel configuration"
    
    def execute(self, context: Context):
        pyro_control = context.scene.skybrush.pyro_control
        
        # Find the next available channel index
        used_indices = {channel.channel_index for channel in pyro_control.custom_channels}
        next_index = 0
        while next_index in used_indices:
            next_index += 1
        
        # Create new channel
        new_channel = pyro_control.custom_channels.add()
        new_channel.channel_index = next_index
        new_channel.effect_name = f"Custom Effect {next_index}"
        new_channel.description = ""
        
        # Set as active
        pyro_control.custom_channels_index = len(pyro_control.custom_channels) - 1
        
        return {"FINISHED"}


class RemovePyroChannelOperator(Operator):
    """Remove a custom pyro channel."""
    
    bl_idname = "skybrush.remove_pyro_channel"
    bl_label = "Remove Pyro Channel"
    bl_description = "Remove the selected custom pyro channel configuration"
    
    index: IntProperty(
        name="Index",
        description="Index of the channel to remove",
        default=-1,
    )
    
    def execute(self, context: Context):
        pyro_control = context.scene.skybrush.pyro_control
        
        # Use provided index or active index
        index = self.index if self.index >= 0 else pyro_control.custom_channels_index
        
        if 0 <= index < len(pyro_control.custom_channels):
            pyro_control.custom_channels.remove(index)
            
            # Adjust active index if needed
            if pyro_control.custom_channels_index >= len(pyro_control.custom_channels):
                pyro_control.custom_channels_index = max(0, len(pyro_control.custom_channels) - 1)
        
        return {"FINISHED"}


class UpdatePyroChannelMarkersOperator(Operator):
    """Update all markers using a specific channel with the channel's current prefire time."""
    
    bl_idname = "skybrush.update_pyro_channel_markers"
    bl_label = "Update Markers for Channel"
    bl_description = "Update all markers using this channel with the channel's current prefire time"
    
    channel_index: IntProperty(
        name="Channel Index",
        description="Index of the channel to update markers for",
        default=-1,
    )
    
    def execute(self, context: Context):
        pyro_control = context.scene.skybrush.pyro_control
        
        # Get the channel to update markers for
        channel_index = self.channel_index
        channel = None
        for ch in pyro_control.custom_channels:
            if ch.channel_index == channel_index:
                channel = ch
                break
        
        if not channel:
            self.report({"ERROR"}, f"Channel {channel_index} not found")
            return {"CANCELLED"}
        
        # Find all drones and update their markers
        from sbstudio.plugin.constants import Collections
        from sbstudio.plugin.utils.pyro_markers import get_pyro_markers_of_object, set_pyro_markers_of_object
        
        drones = Collections.find_drones(create=False)
        if not drones:
            self.report({"INFO"}, "No drones found")
            return {"FINISHED"}
        
        markers_updated = 0
        for drone in drones.objects:
            markers = get_pyro_markers_of_object(drone)
            for frame, marker in markers.markers.items():
                if marker.channel == channel_index:
                    # Update the prefire_time in the payload
                    marker.payload.prefire_time = channel.prefire_time
                    markers_updated += 1
            
            # Save the updated markers
            set_pyro_markers_of_object(drone, markers)
        
        self.report({"INFO"}, f"Updated {markers_updated} markers for channel {channel_index} ({channel.effect_name})")
        return {"FINISHED"}
