"""Operators for selecting drones."""

from bpy.types import Context, Operator
from bpy.props import StringProperty

__all__ = (
    "PYRO_OT_select_drone",
    "PYRO_OT_add_drone_to_selection",
)


class PYRO_OT_select_drone(Operator):
    """Select a drone by name."""
    
    bl_idname = "pyro.select_drone"
    bl_label = "Select Drone"
    bl_options = {'REGISTER', 'UNDO'}
    
    drone_name: StringProperty(
        name="Drone Name",
        description="Name of the drone to select",
    )
    
    def execute(self, context: Context):
        scene = context.scene
        
        # Get the drone object
        drone = scene.objects.get(self.drone_name)
        if not drone:
            self.report({'ERROR'}, f"Drone '{self.drone_name}' not found")
            return {'CANCELLED'}
        
        # Deselect all objects
        for obj in scene.objects:
            obj.select_set(False)
        
        # Select the drone
        drone.select_set(True)
        context.view_layer.objects.active = drone
        
        return {'FINISHED'}


class PYRO_OT_add_drone_to_selection(Operator):
    """Add a drone to the current selection."""
    
    bl_idname = "pyro.add_drone_to_selection"
    bl_label = "Add Drone to Selection"
    bl_options = {'REGISTER', 'UNDO'}
    
    drone_name: StringProperty(
        name="Drone Name",
        description="Name of the drone to add to selection",
    )
    
    def execute(self, context: Context):
        scene = context.scene
        
        # Get the drone object
        drone = scene.objects.get(self.drone_name)
        if not drone:
            self.report({'ERROR'}, f"Drone '{self.drone_name}' not found")
            return {'CANCELLED'}
        
        # Add the drone to the selection
        drone.select_set(True)
        context.view_layer.objects.active = drone
        
        return {'FINISHED'}
