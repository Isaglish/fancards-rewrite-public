from __future__ import annotations

import re
from typing import TYPE_CHECKING

import discord
from discord import app_commands

from fancards.database import Player
from fancards.enums import CardRarity, CardCondition, Character


if TYPE_CHECKING:
    from bot import Fancards

OPTION_LIMIT = 25
Choices = list[app_commands.Choice[str]]


def regex_autocomplete(prefix: str, words: list[str]) -> list[str]:
    """Returns the list of ``words`` that begins with ``prefix`` or more."""
    pattern = re.compile(f'^{prefix}.*', flags=re.IGNORECASE)
    return [word for word in words if pattern.match(word)]


async def autocomplete_close_matches(interaction: discord.Interaction, current: str, words: list[str]) -> Choices:
    close_matches = regex_autocomplete(current, words)
    if close_matches:
        return [
            app_commands.Choice(name=close_match, value=close_match) for close_match in close_matches[:OPTION_LIMIT]
        ]
        
    return [
        app_commands.Choice(name=word, value=word) for word in words[:OPTION_LIMIT]
    ]


async def card_rarity_autocomplete(interaction: discord.Interaction, current: str) -> Choices:
    rarities = [str(rarity) for rarity in CardRarity if rarity not in CardRarity.get_exclusive_rarities()]
    return await autocomplete_close_matches(interaction, current, rarities)


async def card_condition_autocomplete(interaction: discord.Interaction, current: str) -> Choices:
    conditions = [str(condition) for condition in CardCondition]
    return await autocomplete_close_matches(interaction, current, conditions)


async def card_id_autocomplete(interaction: discord.Interaction, current: str) -> Choices:
    bot: Fancards = interaction.client  # type: ignore
    player = Player(bot.pool, interaction.user.id)
    close_matches = await player.collection.get_close_matches_by_card_id(current)
    if close_matches:
        return [
            app_commands.Choice(
                name=f"{card_table.card_id} ({card_table.character_name}) ({card_table.condition.unicode})",
                value=card_table.card_id
            ) for card_table in close_matches[:OPTION_LIMIT]
        ]
    
    return []


async def character_name_autocomplete(interaction: discord.Interaction, current: str) -> Choices:
    character_names = [character.display_name for character in Character.get_all_characters()]
    return await autocomplete_close_matches(interaction, current, character_names)
