"""UIList for displaying custom pyro channels."""

from __future__ import annotations

from bpy.types import UIList, Context

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sbstudio.plugin.model.pyro_control import PyroChannelOption

__all__ = ("SKYBRUSH_UL_pyro_channels",)


class SKYBRUSH_UL_pyro_channels(UIList):
    """Customized Blender UI list for custom pyro channels."""

    def draw_item(
        self,
        context: Context,
        layout,
        data,
        item: "PyroChannelOption",
        icon,
        active_data,
        active_propname,
        index,
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.use_property_decorate = False
            layout.alignment = "EXPAND"
            
            row = layout.row(align=True)
            row.label(text=f"Ch. {item.channel_index}", translate=False)
            row.prop(item, "effect_name", text="", emboss=False)
            
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=f"Ch. {item.channel_index}", translate=False)
