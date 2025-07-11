from typing import Union

import discord
from discord.ext import commands


__all__ = (
    "ButtonOnCooldown",
    "from_cooldown",
    "reset_command_cooldown",
    "reset_cooldown"
)

CooldownMapping = commands.CooldownMapping[discord.Interaction]


class BucketType:
    @classmethod
    def user(cls, interaction: discord.Interaction) -> Union[discord.User, discord.Member]:
        return interaction.user


class ButtonOnCooldown(commands.CommandError):
    """An exception that is raised when a button view being interacted with is on cooldown"""
    def __init__(self, retry_after: float):
        self.retry_after = retry_after


def from_cooldown(rate: float, per: float) -> CooldownMapping:
    return commands.CooldownMapping.from_cooldown(rate, per, BucketType.user)


def reset_command_cooldown(interaction: discord.Interaction) -> None:
    """Resets the cooldown of a :class:`app_commands.Command`."""
    command = interaction.command
    if command is None:
        return None
    
    cooldown: CooldownMapping = command.extras["cooldown"]
    bucket = cooldown.get_bucket(interaction)
    if bucket is not None:
        bucket.reset()


def reset_cooldown(interaction: discord.Interaction, cooldown: commands.CooldownMapping[discord.Interaction]) -> None:
    """Reset a custom cooldown."""
    bucket = cooldown.get_bucket(interaction)
    assert bucket
    bucket.reset()
