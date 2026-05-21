"""Panel for configuring custom pyro channels."""

from bpy.types import Panel

from sbstudio.plugin.operators import (
    AddPyroChannelOperator as AddPyroChannel,
    RemovePyroChannelOperator as RemovePyroChannel,
)


class PyroChannelsConfigPanel(Panel):
    """Custom Blender panel for managing custom pyro channel configurations."""
    
    bl_idname = "OBJECT_PT_skybrush_pyro_channels_config_panel"
    bl_label = "Pyro Channel Configuration"
    
    # The following three settings determine that the panel gets
    # added to the sidebar of the 3D view in the Pyro tab
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pyro"
    
    @classmethod
    def poll(cls, context):
        return context.scene.skybrush.pyro_control is not None
    
    def draw(self, context):
        scene = context.scene
        pyro_control = scene.skybrush.pyro_control
        
        layout = self.layout
        
        # Instructions
        layout.label(text="Custom Pyro Effects Library", icon="INFO")
        layout.label(text="Add and configure custom pyro effects here")
        
        layout.separator()
        
        # List of custom channels
        rows = min(len(pyro_control.custom_channels), 6)
        if rows == 0:
            rows = 3
        
        layout.template_list(
            "SKYBRUSH_UL_pyro_channels",
            "custom_pyro_channels",
            pyro_control,
            "custom_channels",
            pyro_control,
            "custom_channels_index",
            rows=rows,
        )
        
        # Add/Remove buttons
        row = layout.row()
        row.operator(AddPyroChannel.bl_idname, icon="ADD", text="Add Channel")
        row.operator(RemovePyroChannel.bl_idname, icon="REMOVE", text="Remove")
        
        layout.separator()
        
        # Properties of the selected channel
        if pyro_control.custom_channels:
            if 0 <= pyro_control.custom_channels_index < len(pyro_control.custom_channels):
                channel = pyro_control.custom_channels[pyro_control.custom_channels_index]
                
                layout.label(text="Channel Properties", icon="PROPERTIES")
                layout.prop(channel, "channel_index", text="Channel Index")
                layout.prop(channel, "effect_name", text="Effect Name")
                layout.prop(channel, "description", text="Description")
