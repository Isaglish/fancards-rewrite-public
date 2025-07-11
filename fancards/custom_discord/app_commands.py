from typing import Any, TypeVar, Callable

import discord
from discord.ext import commands
from discord import app_commands

from fancards.utils import (
    create_interaction_embed,
    seconds_to_human,
    from_cooldown,
)

CommandT = TypeVar("CommandT", bound=app_commands.Command[Any, ..., Any])
CooldownMapping = commands.CooldownMapping[discord.Interaction]


class Group(app_commands.Group):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            human_time = seconds_to_human(error.retry_after)
            embed = create_interaction_embed(
                interaction=interaction,
                level="error", 
                description=f"You are currently on cooldown, please wait for `{human_time}` before using this command again."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            raise error
        
    def cooldown(self, rate: float, per: float) -> Callable[[CommandT], CommandT]:
        """Add a resettable cooldown to a :class:`app_commands.Command`. Has to be implemented before the ``@command`` decorator!"""
        def decorator(command: CommandT) -> CommandT:
            command.extras["cooldown"] = from_cooldown(rate, per)
            cooldown: CooldownMapping = command.extras["cooldown"]
            
            def wrapper(interaction: discord.Interaction) -> bool:
                bucket = cooldown.get_bucket(interaction)
                assert bucket
                retry_after = cooldown.update_rate_limit(interaction)
                if retry_after and retry_after > 1:
                    raise app_commands.CommandOnCooldown(bucket, retry_after)

                return True

            cmd = app_commands.check(wrapper)
            return cmd(command)

        return decorator
