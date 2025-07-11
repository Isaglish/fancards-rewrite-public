from __future__ import annotations

from typing import ParamSpec, Callable, Self, Optional, Any, Union

import discord
from discord import app_commands

from fancards import utils
from fancards.enums import DiscordEmoji


P = ParamSpec("P")
ConfirmT = Union["Confirm", "EmbedPaginatorConfirm"]

__all__ = (
    "wait_for_confirmation",
    "Confirm",
    "EmbedPaginator",
    "EmbedPaginatorConfirm"
)


async def wait_for_confirmation(
    _interaction: discord.Interaction,
    _view: ConfirmT,
    _message: discord.WebhookMessage,
    _callback: Callable[P, Any],
    _timeout_message: Optional[str] = None,
    *args: P.args,
    **kwargs: P.kwargs
) -> None:
    await _view.wait()
    if _view.value is None:
        if isinstance(_interaction.command, app_commands.Command) and _interaction.command.extras.get("cooldown", None) is not None:
            utils.reset_command_cooldown(_interaction)
        
        embed = utils.create_interaction_embed(
            _interaction,
            description=_timeout_message if _timeout_message is not None else "You took too long to respond.",
            level="error"
        )
        await _message.edit(embed=embed, view=None, attachments=[])
        return None

    elif _view.value:
        await _callback(*args, **kwargs)

    else:
        embed = embed = utils.create_interaction_embed(
            _interaction,
            description="Command canceled.",
            level="error"
        )
        await _message.edit(embed=embed, view=None, attachments=[])
        return None


class Confirm(discord.ui.View):
    def __init__(self, author: discord.Member, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.value = None
        self.author = author

    @discord.ui.button(emoji=str(DiscordEmoji.ICON_CHECK), style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button[Self]) -> None:
        self.value = True
        self.stop()

    @discord.ui.button(emoji=str(DiscordEmoji.ICON_CROSS), style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button[Self]) -> None:
        self.value = False
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author != interaction.user:
            await interaction.response.send_message("You don't have the permission to do that.", ephemeral=True)
            return False
           
        return True


class EmbedPaginator(discord.ui.View):
    def __init__(
        self,
        interaction: discord.Interaction,
        *,
        embeds: list[discord.Embed],
        footer: Optional[str] = None
    ):
        super().__init__(timeout=None)
        self.current_page = 0
        self.max_pages = len(embeds)
        self.interaction = interaction
        self.author = interaction.user
        self.embeds = embeds
        self.footer = footer

    @property
    def index_page(self) -> discord.Embed:
        if self.max_pages > 1:
            self.next_page.disabled = False
            
        if self.max_pages > 2:
            self.last_page.disabled = False

        if self.max_pages < 2:
            self.remove_item(self.previous_page)
            self.remove_item(self.next_page)
            self.remove_item(self.quit_button)

        if self.max_pages < 3:
            self.remove_item(self.last_page)
            self.remove_item(self.first_page)

        embed = self.embeds[0]
        embed.set_footer(text=self.get_footer())
        return embed
    
    def get_footer(self) -> str:
        footer = self.footer
        current_page = self.current_page + 1
        max_pages = self.max_pages

        parse_table = {
            "$current_page": current_page,
            "$max_pages": max_pages
        }
        if footer is None:
            return utils.parse_arguments(parse_table, "Page $current_page/$max_pages")
        
        return utils.parse_arguments(parse_table, footer)

    @discord.ui.button(emoji=str(DiscordEmoji.ICON_FIRST_PAGE), style=discord.ButtonStyle.blurple, custom_id="first_page:button", disabled=True)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button[Self]) -> None:
        self.current_page = 0
        button.disabled = True
        self.previous_page.disabled = True

        if self.max_pages > 1:
            self.next_page.disabled = False

        if self.max_pages > 2:
            self.last_page.disabled = False

        embed = self.embeds[self.current_page]
        embed.set_footer(text=self.get_footer())
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=str(DiscordEmoji.ICON_PREVIOUS), style=discord.ButtonStyle.blurple, custom_id="prev_page:button", disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button[Self]) -> None:
        self.current_page  = self.current_page - 1 if self.current_page - 1 != -1 else self.current_page
        button.disabled = self.current_page - 1 == -1
        self.first_page.disabled = self.current_page - 1 == -1

        if self.max_pages > 1 and (self.current_page - 1 == -1 or self.current_page - 1 != -1):
            self.next_page.disabled = False
            
        if self.max_pages > 2 and self.current_page - 1 != -1:
            self.last_page.disabled = False
        
        embed = self.embeds[self.current_page]
        embed.set_footer(text=self.get_footer())
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=str(DiscordEmoji.ICON_NEXT), style=discord.ButtonStyle.blurple, custom_id="next_page:button", disabled=True)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button[Self]) -> None:
        self.current_page = self.current_page + 1 if self.current_page + 1 != self.max_pages else self.current_page
        button.disabled = self.current_page + 1 >= self.max_pages
        self.last_page.disabled = self.current_page + 1 >= self.max_pages

        if self.max_pages > 1:
            self.previous_page.disabled = False

        if self.max_pages > 2:
            self.first_page.disabled = False

        embed = self.embeds[self.current_page]
        embed.set_footer(text=self.get_footer())
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=str(DiscordEmoji.ICON_LAST_PAGE), style=discord.ButtonStyle.blurple, custom_id="last_page:button", disabled=True)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button[Self]) -> None:
        self.current_page = self.max_pages - 1
        button.disabled = True
        
        if self.max_pages > 1:
            self.next_page.disabled = True
            self.previous_page.disabled = False

        if self.max_pages > 2:
            self.first_page.disabled = False

        embed = self.embeds[self.current_page]
        embed.set_footer(text=self.get_footer())
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=str(DiscordEmoji.ICON_POWER), style=discord.ButtonStyle.red, custom_id="quit:button")
    async def quit_button(self, interaction: discord.Interaction, button: discord.ui.Button[Self]) -> None:
        embed = self.embeds[self.current_page]
        embed.set_footer(text=self.get_footer())
        await interaction.response.edit_message(embed=embed, view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author != interaction.user:
            await interaction.response.send_message("You don't have the permission to do that.", ephemeral=True)
            return False

        return True


class EmbedPaginatorConfirm(EmbedPaginator):
    def __init__(self, interaction: discord.Interaction, embeds: list[discord.Embed]):
        super().__init__(interaction, embeds=embeds)
        self.value = None
        self.remove_item(self.quit_button)

    @discord.ui.button(emoji=str(DiscordEmoji.ICON_CHECK), style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button[Self]) -> None:
        self.value = True
        self.stop()

    @discord.ui.button(emoji=str(DiscordEmoji.ICON_CROSS), style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button[Self]) -> None:
        self.value = False
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await super().interaction_check(interaction):
            return False
        
        return True
