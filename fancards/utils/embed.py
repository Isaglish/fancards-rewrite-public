from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Union, Any, Optional

from discord import Embed, Interaction, Color

from fancards.enums import Fancolor, Fanrole


if TYPE_CHECKING:
    from bot import Fancards
    from discord.ext import commands

    Context = commands.Context["Fancards"]

__all__ = (
    "create_interaction_embed",
    "create_context_embed",
)

Level = Literal["error", "warning", "info", "success"]


def _get_level_color(level: Level) -> Color:
    mapping = {
        "error": Fancolor.RED(),
        "warning": Fancolor.YELLOW(),
        "info": Fancolor.LIGHT_BLUE(),
        "success": Fancolor.LIGHT_GREEN()
    }
    return mapping[level]


def _create_embed(
    interaction: Union[Interaction, Context],
    *,
    description: Optional[Any] = None,
    color: Optional[Union[int, Color]] = None,
    title: Optional[Any] = None,
    footer: Optional[Any] = None,
    level: Level = "info"
) -> Embed:
    color = _get_level_color(level) if color is None else color
    
    if isinstance(interaction, Interaction):
        user = interaction.user
    else:
        user = interaction.author

    icon_url = user.display_avatar.url
    fanrole = Fanrole.get_fanrole(user.id)
    embed = Embed(
        color=color,
        description=description,
        title=title
    )
    embed.set_author(name=f"【{user}】═【{fanrole}】", icon_url=icon_url)

    if footer is not None:
        embed.set_footer(text=footer, icon_url=icon_url)
    
    return embed


def create_interaction_embed(
    interaction: Interaction,
    *,
    description: Optional[Any] = None,
    color: Optional[Union[int, Color]] = None,
    title: Optional[Any] = None,
    footer: Optional[Any] = None,
    level: Level = "info"
) -> Embed:
    return _create_embed(
        interaction,
        description=description,
        color=color,
        title=title,
        footer=footer,
        level=level
    )


def create_context_embed(
    ctx: Context,
    *,
    description: Optional[Any] = None,
    color: Optional[Union[int, Color]] = None,
    title: Optional[Any] = None,
    footer: Optional[Any] = None,
    level: Level = "info"
) -> Embed:
    return _create_embed(
        ctx,
        description=description,
        color=color,
        title=title,
        footer=footer,
        level=level
    )

