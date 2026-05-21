from bpy.types import Panel, Context

from sbstudio.plugin.constants import Collections
from sbstudio.plugin.operators import (
    TriggerPyroOnSelectedDronesOperator as TriggerPyro,
    RemovePyroOnSelectedDronesOperator as RemovePyro,
    CalculatePyroMarkers as CalculatePyroMarkers,
)
from sbstudio.plugin.utils.pyro_markers import get_pyro_markers_of_object
from sbstudio.plugin.model.pyro_control import get_default_pyro_channel_options


def get_channel_name(channel_index: str) -> str:
    """Get the display name for a pyro channel."""
    for value, name, _ in get_default_pyro_channel_options():
        if value == channel_index:
            return name
    return f"Channel {channel_index}"


class PyroControlPanel(Panel):
    """Custom Blender panel that allows the user to control trigger events
    for drone-launched fireworks in the current drone show.
    """

    bl_idname = "OBJECT_PT_skybrush_pyro_control_panel"
    bl_label = "Pyro Control"

    # The following three settings determine that the Pyro control panel gets
    # added to the sidebar of the 3D view
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pyro"

    @classmethod
    def poll(cls, context):
        return context.scene.skybrush.pyro_control

    def draw(self, context):
        scene = context.scene
        pyro_control = scene.skybrush.pyro_control
        if not pyro_control:
            return

        layout = self.layout

        layout.prop(pyro_control, "visualization", text="Render")

        layout.separator()

        layout.prop(pyro_control, "channel")

        layout.separator()

        layout.prop(pyro_control, "name")
        layout.prop(pyro_control, "duration")
        layout.prop(pyro_control, "prefire_time")

        layout.separator()

        layout.prop(pyro_control, "pitch")
        layout.prop(pyro_control, "yaw")
        layout.prop(pyro_control, "roll")

        layout.separator()

        layout.prop(pyro_control, "primary_color")
        layout.prop(pyro_control, "secondary_color")
        layout.prop(pyro_control, "volume")

        layout.separator()

        layout.operator(TriggerPyro.bl_idname, text="Trigger")
        layout.operator(RemovePyro.bl_idname, text="Remove on this frame")
        layout.operator(CalculatePyroMarkers.bl_idname, text="Recalculate Markers")

        layout.separator()

        # Collapsible section for effects fired on current frame
        box = layout.box()
        row = box.row()
        row.prop(
            pyro_control, 
            "show_frame_effects", 
            text="Effects on Frame",
            icon="TRIA_DOWN" if pyro_control.show_frame_effects else "TRIA_RIGHT",
            emboss=False,
        )

        if pyro_control.show_frame_effects:
            frame = context.scene.frame_current
            drones = Collections.find_drones(create=False)

            if not drones:
                box.label(text="No drones found")
                return

            has_effects = False
            for drone in drones.objects:
                markers = get_pyro_markers_of_object(drone)
                if frame not in markers.markers:
                    continue

                has_effects = True
                marker = markers.markers[frame]

                # Create a sub-box for each effect
                effect_box = box.box()
                
                # Drone name and action buttons
                header_row = effect_box.row()
                header_row.label(text=f"Drone: {drone.name}", icon="OBJECT_DATA")
                
                # Load button
                load_op = header_row.operator("pyro.load_effect", text="", icon="IMPORT")
                load_op.drone_name = drone.name
                load_op.frame = frame
                
                # Select button (replace selection)
                select_op = header_row.operator("pyro.select_drone", text="", icon="RESTRICT_SELECT_OFF")
                select_op.drone_name = drone.name
                
                # Add to selection button
                add_select_op = header_row.operator("pyro.add_drone_to_selection", text="", icon="ADD")
                add_select_op.drone_name = drone.name
                
                # Channel and effect type
                channel_name = get_channel_name(str(marker.channel))
                effect_box.label(text=f"Channel: {channel_name}")
                
                # Payload info
                payload = marker.payload
                effect_box.label(text=f"Effect: {payload.name}")
                effect_box.label(text=f"Duration: {payload.duration:.4f}s")
                effect_box.label(text=f"Prefire: {payload.prefire_time:.4f}s")
                
                # Rotation angles
                rotation_box = effect_box.box()
                rotation_box.label(text="Rotation:", icon="ORIENTATION_GIMBAL")
                rotation_box.label(text=f"  Pitch: {marker.pitch}°")
                rotation_box.label(text=f"  Yaw: {marker.yaw}°")
                rotation_box.label(text=f"  Roll: {marker.roll}°")
                
                # Colors
                colors_box = effect_box.box()
                colors_row = colors_box.row()
                
                # Primary color - display as color swatch
                r, g, b = marker.primary_color
                colors_row.label(text="Primary:")
                colors_row.separator()
                colors_box.label(text=f"  RGB({r:.2f}, {g:.2f}, {b:.2f})")
                
                # Secondary color - display as color swatch
                r, g, b = marker.secondary_color
                colors_row2 = colors_box.row()
                colors_row2.label(text="Secondary:")
                colors_row2.separator()
                colors_box.label(text=f"  RGB({r:.2f}, {g:.2f}, {b:.2f})")
                
                # Volume
                volume_row = effect_box.row()
                volume_row.label(text="Volume:")
                volume_row.label(text=f"{marker.volume:.1%}")

            if not has_effects:
                box.label(text="No effects on this frame")
