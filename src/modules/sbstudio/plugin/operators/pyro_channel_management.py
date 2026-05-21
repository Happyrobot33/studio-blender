"""Operators for managing custom pyro channel configurations."""

from bpy.types import Context, Operator
from bpy.props import IntProperty


__all__ = (
    "AddPyroChannelOperator",
    "RemovePyroChannelOperator",
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
