from __future__ import annotations

import random
import datetime
from collections import Counter
from typing import TYPE_CHECKING, Optional, Literal, Any

import discord
from discord import app_commands
from discord.ext import commands

from src.autocomplete import (
    card_rarity_autocomplete,
    card_condition_autocomplete,
    card_id_autocomplete,
    character_name_autocomplete,
    regex_autocomplete
)
from fancards import utils, enums
from fancards.custom_discord.app_commands import Group
from fancards.database import Player, CardTable
from fancards.enums.patreon import is_patreon
from fancards.factory import CardFactory, CardImage, CARD_ID_LENGTH


if TYPE_CHECKING:
    from bot import Fancards

BUTTON_COOLDOWN_CACHE = utils.from_cooldown(1, 6)


async def _confirm_card_burn_single(
    interaction: discord.Interaction,
    message: discord.WebhookMessage,
    total_silver: int,
    total_star: int,
    glistening_gems: int,
    success_text: str,
    card: CardTable,
    card_image_url: str
) -> None:
    bot: Fancards = interaction.client  # type: ignore
    player = Player(bot.pool, interaction.user.id)

    card_exists = await player.collection.get_card(card.card_id) is not None
    if not card_exists:
        embed = utils.create_interaction_embed(
            interaction,
            description="The card you wanted to burn does not exist anymore.",
            level="error"
        )
        await message.edit(embed=embed, view=None, attachments=[])
        return None
    
    await player.balance.add_silver(total_silver)
    await player.balance.add_star(total_star)

    if card.is_shiny:
        await player.inventory.add_item(enums.Item.GLISTENING_GEM, glistening_gems)

    await player.collection.delete_card(card.card_id)
    embed = utils.create_interaction_embed(
        interaction,
        description=success_text,
        level="success"
    )
    embed.set_thumbnail(url=card_image_url)
    await message.edit(embed=embed, view=None)


async def _confirm_card_burn_multi(
    interaction: discord.Interaction,
    player: Player,
    message: discord.WebhookMessage,
    valid_card_ids: list[str],
    total_silver: int,
    total_star: int,
    total_glistening_gem: int,
    success_text: str,
    has_shiny: bool
) -> None:
    await _confirm_card_burn_all(
        interaction,
        player,
        message,
        valid_card_ids,
        total_silver,
        total_star,
        total_glistening_gem,
        success_text,
        has_shiny
    )


async def _confirm_card_burn_all(
    interaction: discord.Interaction,
    player: Player,
    message: discord.WebhookMessage,
    valid_card_ids: list[str],
    total_silver: int,
    total_star: int,
    total_glistening_gem: int,
    success_text: str,
    has_shiny: bool
) -> None:
    cards = await player.collection.get_cards_by_card_id(valid_card_ids)
    if not cards or len(cards) != len(valid_card_ids):
        utils.reset_command_cooldown(interaction)
        embed = utils.create_interaction_embed(
            interaction,
            description="Some of the cards you wanted to burn does not exist anymore.",
            level="error"
        )
        await message.edit(embed=embed, view=None, attachments=[])
        return None
    
    await player.collection.delete_cards_by_card_id(valid_card_ids)
    
    await player.balance.add_silver(total_silver)
    await player.balance.add_star(total_star)

    if has_shiny:
        await player.inventory.add_item(enums.Item.GLISTENING_GEM, total_glistening_gem)

    embed = utils.create_interaction_embed(
        interaction,
        description=success_text,
        level="success"
    )
    await message.edit(embed=embed, view=None)


async def _handle_card_burn_single(interaction: discord.Interaction, card: CardTable) -> None:
    card_id = card.card_id
    card_rarity = card.rarity
    card_condition = card.condition
    card_character_name = card.character_name
    card_is_shiny = card.is_shiny
    card_created_at = card.created_at
    
    card_image = CardFactory.generate_card(
        card_id=card_id,
        rarity=card_rarity,
        condition=card_condition,
        character_name=card_character_name,
        shiny=card_is_shiny
    ).image
    card_image_url, card_image_file = utils.save_image_to_discord_file(card_image, filename="card")
    card_property_text = utils.get_card_property_text(
        card_id=card_id,
        rarity=card_rarity,
        condition=card_condition,
        character_name=card_character_name,
        is_shiny=card_is_shiny,
        in_sleeve=card.in_sleeve
    )

    if card_rarity.is_valuable:
        utils.reset_command_cooldown(interaction)
        embed = utils.create_interaction_embed(
            interaction,
            description=f"This card cannot be burned as it is too valuable.\n{card_property_text}",
            level="error"
        )
        embed.set_thumbnail(url=card_image_url)
        await interaction.followup.send(embed=embed, file=card_image_file)
        return None
    
    if card.is_locked:
        utils.reset_command_cooldown(interaction)
        embed = utils.create_interaction_embed(
            interaction,
            description=f"Unlock this card first before burning it.",
            level="error"
        )
        embed.set_thumbnail(url=card_image_url)
        await interaction.followup.send(embed=embed, file=card_image_file)
        return None
    
    assert card_rarity.silver_values
    card_rarity_silver_value = random.randint(*card_rarity.silver_values)
    card_condition_star_value = card_condition.star_value

    total_silver = card_rarity_silver_value + _calculate_bonus_days(card_rarity_silver_value, card_created_at)
    total_star = card_condition_star_value + _calculate_bonus_days(card_condition_star_value, card_created_at)
    glistening_gems = 1

    assert isinstance(interaction.user, discord.Member)
    view = utils.Confirm(interaction.user)

    rewards_text = f"{enums.Currency.SILVER.emoji} {total_silver:,}\n{enums.Currency.STAR.emoji} {total_star:,}"
    if card_is_shiny:
        rewards_text = f"{rewards_text}\n{enums.Item.GLISTENING_GEM.display()} `x{glistening_gems}`"

    embed = utils.create_interaction_embed(
        interaction,
        description=f"Are you sure you wanna burn this card?\n\n**You will receive:**\n{rewards_text}\n\n{card_property_text}",
        level="warning"
    )
    embed.set_thumbnail(url=card_image_url)
    success_text = f"Burning successful!\n\n**You received:**\n{rewards_text}"

    message = await interaction.followup.send(embed=embed, file=card_image_file, view=view, wait=True)
    await utils.wait_for_confirmation(
        interaction,
        view,
        message,
        _confirm_card_burn_single,
        interaction=interaction,
        message=message,
        total_silver=total_silver,
        total_star=total_star,
        glistening_gems=glistening_gems,
        success_text=success_text,
        card=card,
        card_image_url=card_image_url
    )


async def _handle_card_burn_multi(interaction: discord.Interaction, cards: list[CardTable]) -> None:
    bot: Fancards = interaction.client  # type: ignore
    player = Player(bot.pool, interaction.user.id)

    all_pages: list[list[str]] = []
    valid_card_ids: list[str] = []
    invalid_card_count = 0

    # get card properties and save the ones that can be burned
    end = 10
    for start in range(0, len(cards), 10):
        current_cards = cards[start:end]
        end += 10

        pages: list[str] = []
        for card in current_cards:
            card_property_text = utils.get_card_property_text(
                card_id=card.card_id,
                rarity=card.rarity,
                condition=card.condition,
                character_name=card.character_name,
                is_shiny=card.is_shiny,
                is_locked=card.is_locked,
                in_sleeve=card.in_sleeve
            )

            if card.rarity.is_valuable:
                card_property_text += " `[Too Valuable]`"
                invalid_card_count += 1
                pages.append(card_property_text)
                continue

            player_table = await player.get_table()
            assert player_table
            if card.fk_user_id != player_table.id:
                card_property_text += " `[Not Owned]`"
                invalid_card_count += 1
                pages.append(card_property_text)
                continue

            if card.is_locked:
                card_property_text += " `[Locked]`"
                invalid_card_count += 1
                pages.append(card_property_text)
                continue

            valid_card_ids.append(card.card_id)
            pages.append(card_property_text)

        all_pages.append(pages)

    # calculate rewards
    total_silver = 0
    total_star = 0
    total_glistening_gem = 0
    has_shiny = False
    for card in cards:
        if card.card_id not in valid_card_ids:
            continue

        card_rarity = card.rarity
        card_created_at = card.created_at
        
        assert card_rarity.silver_values
        card_rarity_silver_value = random.randint(*card_rarity.silver_values)
        card_condition_star_value = card.condition.star_value
        total_silver += card_rarity_silver_value + _calculate_bonus_days(card_rarity_silver_value, card_created_at)
        total_star += card_condition_star_value + _calculate_bonus_days(card_condition_star_value, card_created_at)

        if card.is_shiny:
            total_glistening_gem += 1
            has_shiny = True

    # make embeds
    rewards_text = f"{enums.Currency.SILVER.emoji} {total_silver:,}\n{enums.Currency.STAR.emoji} {total_star:,}"
    if has_shiny:
        rewards_text = f"{rewards_text}\n{enums.Item.GLISTENING_GEM.display()} `x{total_glistening_gem}`"

    success_text = f"Burning successful!\n\n**You received:**\n{rewards_text}"
    embeds: list[discord.Embed] = []
    for page in all_pages:
        page = "\n".join(page)
        embed = utils.create_interaction_embed(
            interaction,
            description=f"Are you sure you wanna burn all these cards?\nBurnable cards: `x{len(valid_card_ids)}`\n\n**You will receive:**\n{rewards_text}\n\n{page}",
            level="warning"
        )
        embeds.append(embed)

    if invalid_card_count == len(cards):
        utils.reset_command_cooldown(interaction)
        embed = utils.create_interaction_embed(
            interaction,
            description="The cards you provided cannot be burned.",
            level="error"
        )
        await interaction.followup.send(embed=embed)
        return None
    
    assert isinstance(interaction.user, discord.Member)
    view = utils.EmbedPaginatorConfirm(interaction, embeds)
    embed = view.index_page
    message = await interaction.followup.send(embed=embed, view=view, wait=True)
    await utils.wait_for_confirmation(
        interaction,
        view,
        message,
        _confirm_card_burn_multi,
        interaction=interaction,
        player=player,
        message=message,
        valid_card_ids=valid_card_ids,
        total_silver=total_silver,
        total_star=total_star,
        total_glistening_gem=total_glistening_gem,
        success_text=success_text,
        has_shiny=has_shiny
    )
    

async def _handle_card_burn_all(interaction: discord.Interaction) -> None:
    bot: Fancards = interaction.client  # type: ignore
    player = Player(bot.pool, interaction.user.id)

    cards = await player.collection.get_cards()
    if not cards:
        utils.reset_command_cooldown(interaction)
        embed = utils.create_interaction_embed(
            interaction,
            description="You currently don't have any cards.",
            level="error"
        )
        await interaction.followup.send(embed=embed)
        return None
    
    total_silver = 0
    total_star = 0
    total_glistening_gem = 0
    has_shiny = False
    invalid_card_count = 0
    valid_card_ids: list[str] = []
    for card in cards:
        if card.is_locked:
            continue

        card_rarity = card.rarity
        card_created_at = card.created_at

        if card_rarity.is_valuable:
            invalid_card_count += 1
            continue

        assert card_rarity.silver_values
        card_rarity_silver_value = random.randint(*card_rarity.silver_values)
        card_condition_star_value = card.condition.star_value

        total_silver += card_rarity_silver_value + _calculate_bonus_days(card_rarity_silver_value, card_created_at)
        total_star += card_condition_star_value + _calculate_bonus_days(card_condition_star_value, card_created_at)

        if card.is_shiny:
            total_glistening_gem += 1
            has_shiny = True

        valid_card_ids.append(card.card_id)

    rewards_text = f"{enums.Currency.SILVER.emoji} {total_silver:,}\n{enums.Currency.STAR.emoji} {total_star:,}"
    if has_shiny:
        rewards_text = f"{rewards_text}\n{enums.Item.GLISTENING_GEM.display()} `x{total_glistening_gem}`"

    embed = utils.create_interaction_embed(
        interaction,
        description=f"Are you sure you wanna burn all your cards except the locked ones?\nBurnable cards: `x{len(valid_card_ids)}`\n\n**You will receive:**\n{rewards_text}",
        level="warning"
    )
    success_text = f"Burning successful!\n\n**You received:**\n{rewards_text}"

    if invalid_card_count == len(cards):
        utils.reset_command_cooldown(interaction)
        embed = utils.create_interaction_embed(
            interaction,
            description="The cards you provided cannot be burned.",
            level="error"
        )
        await interaction.followup.send(embed=embed)
        return None
    
    assert isinstance(interaction.user, discord.Member)
    view = utils.Confirm(interaction.user)

    message = await interaction.followup.send(embed=embed, view=view, wait=True)
    await utils.wait_for_confirmation(
        interaction,
        view,
        message,
        _confirm_card_burn_all,
        interaction=interaction,
        player=player,
        message=message,
        valid_card_ids=valid_card_ids,
        total_silver=total_silver,
        total_star=total_star,
        total_glistening_gem=total_glistening_gem,
        success_text=success_text,
        has_shiny=has_shiny
    )


async def _handle_card_lock(
    interaction: discord.Interaction,
    mode: Literal["lock", "unlock"],
    card_ids: Optional[str] = None
) -> None:
    bot: Fancards = interaction.client  # type: ignore
    player = Player(bot.pool, interaction.user.id)

    if card_ids is None:
        recent_card = player.collection.get_most_recently_obtained_card()
        if recent_card is None:
            embed = utils.create_interaction_embed(
                interaction,
                description="You currently don't own any cards.",
                level="error"
            )
            await interaction.followup.send(embed=embed)
            return None


async def _paginate_character_count(
    interaction: discord.Interaction,
    cards: list[CardTable],
    user: discord.Member | discord.User,
    card_limit: Optional[int] = None,
    descending: bool = False
) -> None:
    embeds: list[discord.Embed] = []
    end = 10
    character_count_map = Counter([(card.rarity, card.character_name) for card in cards])
    for start in range(0, len(character_count_map), 10):
        characters = [(character_name, rarity, count) for ((rarity, character_name), count) in character_count_map.items()]
        current_properties = sorted(characters, key=lambda c: c[1].index, reverse=descending)[start:end]
        end += 10

        pages: list[str] = []
        for character_name, rarity, count in current_properties:
            pages.append(f"{rarity.display_emoji(True)} **{character_name}** `x{count}`")

        joined_pages = "\n".join(pages)
        total_cards_text = f"Total cards: `x{len(cards):,}`/`{card_limit:,}`" if card_limit is not None else f"Total cards: `x{len(cards):,}`"
        embed = utils.create_interaction_embed(
            interaction,
            description=f"Viewing the card collection of {user.mention}.\n{total_cards_text}\n\n{joined_pages}"
        )
        embeds.append(embed)

    paginator = utils.EmbedPaginator(interaction, embeds=embeds)
    embed = paginator.index_page
    await interaction.followup.send(embed=embed, view=paginator)


async def _paginate_card_collection(
    interaction: discord.Interaction,
    cards: list[CardTable],
    card_count: int,
    user: discord.Member | discord.User,
    card_limit: Optional[int] = None
) -> None:
    filtered_cards_count = len(cards)
    embeds: list[discord.Embed] = []
    end = 10
    for start in range(0, filtered_cards_count, 10):
        current_cards = cards[start:end]
        end += 10

        pages: list[str] = []
        for card in current_cards:
            card_property_text = utils.get_card_property_text(
                card_id=card.card_id,
                rarity=card.rarity,
                condition=card.condition,
                character_name=card.character_name,
                is_shiny=card.is_shiny,
                is_locked=card.is_locked,
                in_sleeve=card.in_sleeve
            )
            pages.append(card_property_text)

        joined_pages = "\n".join(pages)
        card_count_text = f"Total cards: `x{card_count:,}`/`{card_limit:,}`" if card_limit is not None else f"Total cards: `x{card_count:,}`"

        if filtered_cards_count != card_count:
            card_count_text += f"\nFiltered cards: `x{filtered_cards_count:,}`"
        
        embed = utils.create_interaction_embed(
            interaction,
            description=f"Viewing the card collection of {user.mention}.\n{card_count_text}\n\n{joined_pages}"
        )
        embeds.append(embed)

    paginator = utils.EmbedPaginator(interaction, embeds=embeds)
    embed = paginator.index_page
    await interaction.followup.send(embed=embed, view=paginator)


def _calculate_bonus_days(value: int, card_created_at: datetime.datetime) -> int:
    days = (discord.utils.utcnow() - card_created_at).days
    days = min(days, 60)
    return sum([value // 4 for _ in range(days)])


def _calculate_card_value(card: CardTable) -> int:
    base_rarity_value = 10000
    multiplier_rarity_value = 5000

    base_condition_value = 500

    rarity_weight = base_rarity_value + (multiplier_rarity_value * (card.rarity.index - 1))
    condition_weight = base_condition_value * card.condition.index
    shiny_weight = 26000 if card.is_shiny else 0

    return rarity_weight + condition_weight + shiny_weight


def _filter_possible_card_ids(card_ids: str) -> list[str]:
    return list(filter(lambda cid: len(cid) == CARD_ID_LENGTH, [card_id.strip() for card_id in card_ids.split(" ")]))


def _filter_card_collection(
    cards: list[CardTable],
    rarity: Optional[str] = None,
    condition: Optional[str] = None,
    character_name: Optional[str] = None,
    card_age: Optional[str] = None,
    locked: Optional[bool] = None,
    in_sleeve: Optional[bool] = None,
    by_card_id: bool = False,
    descending: bool = False
) -> list[CardTable]:
    filtered_cards = cards
    if rarity is not None:
        try:
            rarity_map = {str(r): r for r in enums.CardRarity.get_non_exclusive_rarities()}
            _rarity = rarity_map[rarity.casefold()]
            filtered_cards = [card for card in filtered_cards if card.rarity is _rarity]
        except ValueError:
            filtered_cards = cards

    if condition is not None:
        try:
            _condition = enums.CardCondition(condition.casefold())
            filtered_cards = [card for card in filtered_cards if card.condition is _condition]
        except ValueError:
            filtered_cards = cards

    if character_name is not None:
        character_names = [character.display_name for character in enums.Character.get_all_characters()]
        character_name = regex_autocomplete(character_name, character_names)[0]
        filtered_cards = [card for card in filtered_cards if card.character_name == character_name and card.character_name in character_names]

    if card_age is not None:
        card_age_delta = utils.str_to_timedelta(card_age)
        filtered_cards = [card for card in filtered_cards if (discord.utils.utcnow() - card.created_at) <= card_age_delta]

    if locked is not None:
        if locked:
            filtered_cards = [card for card in filtered_cards if card.is_locked]
        else:
            filtered_cards = [card for card in filtered_cards if not card.is_locked]

    if in_sleeve is not None:
        if in_sleeve:
            filtered_cards = [card for card in filtered_cards if card.in_sleeve]
        else:
            filtered_cards = [card for card in filtered_cards if not card.in_sleeve]

    if by_card_id:
        filtered_cards = sorted(filtered_cards, key=lambda card: card.card_id)
    else:
        filtered_cards = sorted(filtered_cards, key=_calculate_card_value)

    if descending:
        filtered_cards.reverse()

    return filtered_cards


def _get_troll_text() -> str:
    troll_texts = [
        "Did you really just grab me?",
        "LOL you just got trolled!",
        "You must be trolling, you got a **Troll** card!",
        "Looks like fate dealt you a **Troll** card, better luck next time.",
        "Looks like the **Troll** is laughing at your success, congrats on the card!",
        "You got a wild card in the form of a **Troll**, better use it wisely.",
        "Looks like the **Troll** just played his hand, and you were the lucky one to grab it.",
        "Looks like the **Troll** is on your side today, congrats on the card!"
    ]
    return random.choice(troll_texts)


def _get_card_condition_text(condition: enums.CardCondition) -> str:
    damaged_texts = [
        "Oh.. This card is badly **damaged**.",
        "Unfortunately, this card is in a severely **damaged** condition.",
        "Oh dear, this card is in a heavily **damaged** state.",
        "It's disheartening to see this card in such a **damaged** state.",
        "The condition of this card is quite unfortunate, as it is visibly **damaged**.",
    ]
    poor_texts = [
        "Its condition is quite **poor**.",
        "Oh dear, this card is in a rather **poor** condition.",
        "It's apparent that this card has suffered from neglect and is now in **poor** condition.",
        "The **poor** state of this card is evident.",
        "The quality of this card has noticeably declined, indicating a **poor** condition."
    ]
    good_texts = [
        "It's in **good** condition.",
        "This card is in **good** shape.",
        "The overall condition of this card is **good**.",
        "Hey there, card enthusiasts! Feast your eyes on this beauty in **good** condition.",
        "Get ready to party, because this card is rocking the **good** vibes!"
    ]
    near_mint_texts = [
        "Cool! It's in **near mint** condition!",
        "**Near mint**! A collector's dream!",
        "**Near mint** condition. Impressive!",
        "Practically flawless. **Near mint**!",
        "This card is in **near mint** condition!"
    ]
    mint_texts = [
        "Awesome! It's in **mint** condition!",
        "**Mint** condition. Collector's delight.",
        "**Mint** perfection: this card is a gem in every sense.",
        "Pure **mint** condition: this card is a treasure to behold.",
        "Woah! A **mint** condition card!"
    ]
    pristine_texts = [
        "Unblemished and **pristine**, this card shines with perfection.",
        "Its in **pristine** condition, this card exudes elegance and beauty.",
        "Untouched, immaculate and **pristine**! This card is a rare find.",
        "Perfectly preserved, this card shines with perfection. A **pristine**!",
        "AHHH! This card is in **pristine** condition!"
    ]
    mapping = {
        enums.CardCondition.DAMAGED: damaged_texts,
        enums.CardCondition.POOR: poor_texts,
        enums.CardCondition.GOOD: good_texts,
        enums.CardCondition.NEAR_MINT: near_mint_texts,
        enums.CardCondition.MINT: mint_texts,
        enums.CardCondition.PRISTINE: pristine_texts
    }
    return random.choice(mapping[condition])


class _DropViewButton(discord.ui.Button[discord.ui.View]):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(style=discord.ButtonStyle.gray, *args, **kwargs)
        self.grabbed_card_indexes: list[int] = []

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(self.view, _DropView):
            return None
        
        bot: Fancards = interaction.client  # type: ignore
        user = interaction.user
        assert isinstance(user, discord.Member)
        user_is_patreon = is_patreon(user)
        drop_owner = self.view.author

        player = Player(bot.pool, user.id)
        fk_user_id = await player.register()

        cards = await player.collection.get_cards()
        card_count = len(cards) if not cards else 0
        backpack_capacity = await player.get_backpack_capacity()
        if backpack_capacity is not None and card_count >= backpack_capacity:
            embed = utils.create_interaction_embed(
                interaction,
                description="Your backpack is full! Consider burning cards or upgrading your backpack.",
                level="error"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
        
        assert self.custom_id
        selected_button_index = int(self.custom_id.partition(":")[-1])  # get the index of the button that was pressed
        if selected_button_index in self.grabbed_card_indexes:
            utils.reset_cooldown(interaction, BUTTON_COOLDOWN_CACHE)
            embed = utils.create_interaction_embed(
                interaction,
                description="That card has already been grabbed.",
                level="error"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
        
        self.grabbed_card_indexes.append(selected_button_index)
        self.disabled = True
        await interaction.response.edit_message(view=self.view)

        card: CardImage = self.view.cards[selected_button_index]
        card_rarity = card.rarity
        card_condition = card.condition
        card_character = card.character
        card_id = card.card_id
        weight = self.view.weight

        # overwrite the previously generated card to check if the user that interacted with the button is a patreon
        # and to show the condition and ID of the card.
        card = CardFactory.generate_card(
            rarity=card_rarity,
            condition=card_condition,
            character_name=card_character.display_name,
            card_id=card_id,
            shiny=user_is_patreon
        )

        card_image = card.image
        card_is_shiny = card.is_shiny
        card_rarity_weight: enums.WeightData = getattr(card_rarity.weight, weight.name.lower())
        card_condition_weight: enums.WeightData = getattr(card_condition.weight, weight.name.lower())
        card_image_url, card_image_file = utils.save_image_to_discord_file(card_image, filename="card")

        if card_character.display_name == "Troll":
            troll_text = _get_troll_text()
            embed = utils.create_interaction_embed(interaction, description=troll_text, level="error")
            embed.set_image(url=card_image_url)
            await interaction.followup.send(embed=embed, file=card_image_file)
            return None

        assert fk_user_id
        await player.collection.add_card(
            CardTable(
                card_id=card_id,
                fk_user_id=fk_user_id,
                rarity=card_rarity,
                condition=card_condition,
                character_name=card_character.display_name,
                created_at=discord.utils.utcnow(),
                is_shiny=card_is_shiny
            )
        )
        silver_values = card_rarity.silver_values
        assert silver_values
        
        reward_silver = random.randint(*map(lambda x: x//3, silver_values))
        await player.balance.add_silver(reward_silver)
        reward_xp = random.randint(1, 3)
        await player.level.add_xp(reward_xp)

        rewards_text = f"You gained **{reward_xp}** XP and earned {enums.Currency.SILVER.emoji} {reward_silver:,}!"
        rarity_text = f"a {card_rarity.display_emoji(True)} {f'{enums.DiscordEmoji.RARITY_LETTER_SHINY} ' if card_is_shiny else ''}**{card_character.display_name}**"

        condition_text = _get_card_condition_text(card_condition)
        if drop_owner != user:
            verb = "stole"
            description = f"{user.mention} {verb} {rarity_text} card **`{card_id}`** from {drop_owner.mention}!\n{condition_text}\n\n{rewards_text}"
        else:
            verb = "took"
            description = f"{user.mention} {verb} {rarity_text} card **`{card_id}`**!\n{condition_text}\n\n{rewards_text}"

        if card_is_shiny:
            shiny_weight = CardFactory.get_shiny_weight(weight, user_is_patreon)
            shiny_text = f"\nShiny ({shiny_weight}%)"
        else:
            shiny_text = ""

        embed = utils.create_interaction_embed(
            interaction,
            description=description,
            color=card_rarity.color,
            footer=f"Rarity: {card_rarity.display_name.title()} ({card_rarity_weight}%)\nCondition: {card_condition.display_name.title()} ({card_condition_weight}%){shiny_text}"
        )
        embed.set_image(url=card_image_url)
        await interaction.followup.send(embed=embed, file=card_image_file)
            

class _DropView(discord.ui.View):
    def __init__(self, author: discord.Member, weight: enums.Weight):
        super().__init__(timeout=10)
        self.author = author
        self.weight = weight
        self.cards = CardFactory.generate_cards(
            weight=weight,
            show_card_id=False,
            show_card_condition=False
        )
        self._init_buttons()

    def _init_buttons(self) -> None:
        for idx, card in enumerate(self.cards):
            button = _DropViewButton(
                emoji=str(card.rarity.display_emoji(True)),
                custom_id=f"dv_btn:{idx}"
            )
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        retry_after = BUTTON_COOLDOWN_CACHE.update_rate_limit(interaction)
        if retry_after and retry_after > 1:
            raise utils.ButtonOnCooldown(retry_after)

        return True
    
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]) -> None:
        if isinstance(error, utils.ButtonOnCooldown):
            human_time = utils.seconds_to_human(error.retry_after)
            embed = utils.create_interaction_embed(
                interaction,
                description=f"You are currently on cooldown, please wait for `{human_time}` before grabbing more cards.",
                level="error"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await super().on_error(interaction, error, item)


class CardCog(commands.Cog):
    def __init__(self, bot: Fancards):
        self.bot = bot
        self.log = bot.log

    card_command_group = Group(name="card")

    @card_command_group.cooldown(1, 15)
    @card_command_group.command(name="drop", description="Drops a set of random cards for everyone to grab")
    async def card_drop(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        user = interaction.user
        assert isinstance(user, discord.Member)

        player = Player(self.bot.pool, user.id)
        await player.register()

        item = await player.inventory.get_item(enums.Item.PREMIUM_DROP)
        item_quantity = item.item_quantity if item is not None else 0
        if item is None:
            level_table = await player.level.get_table()
            assert level_table
            weight = enums.Weight.NEW_USER if level_table.current_level < 5 else enums.Weight.NORMAL
            text_premium_drop = ""
        else:
            utils.reset_command_cooldown(interaction)
            weight = enums.Weight.PREMIUM
            text_premium_drop = f"Used {enums.Item.PREMIUM_DROP.display()} `x1`, you now have `x{item_quantity}` remaining.\n\n"

        view = _DropView(user, weight)
        cards = view.cards
        dropped_cards_image = CardFactory.align_card_images([card.image for card in cards])
        image_url, image_file = utils.save_image_to_discord_file(dropped_cards_image, filename="dropped_cards")

        rarest_card = max(cards, key=lambda c: c.rarity.index)
        card_count = len(view.cards)

        embed = utils.create_interaction_embed(
            interaction,
            description=f"{text_premium_drop}{user.mention} has dropped {card_count} cards!",
            color=rarest_card.rarity.color
        )
        embed.set_image(url=image_url)
        message = await interaction.followup.send(embed=embed, file=image_file, view=view, wait=True)

        timeout = await view.wait()
        if timeout:
            embed = utils.create_interaction_embed(
                interaction,
                description=f"{interaction.user.mention} This drop has expired. All remaining cards can no longer be grabbed.",
                level="error"
            )
            embed.set_image(url=image_url)

            for button in view.children:
                if isinstance(button, _DropViewButton):
                    button.disabled = True
                    button.style = discord.ButtonStyle.gray

        await message.edit(embed=embed, view=view)

    @card_command_group.cooldown(1, 5)
    @card_command_group.command(name="collection", description="View your card collection or specify an owner to view their collection")
    @app_commands.describe(
        owner="The owner of the card collection you want to view",
        rarity="The rarity of the cards",
        condition="The condition of the cards",
        character_name="The name of the characters on the cards",
        card_age="Show cards below/less than this time",
        locked="Whether the cards are locked",
        in_sleeve="Whether the cards are in a sleeve",
        by_card_id="Whether to sort the cards by card-id, cards are sorted by value as default",
        by_character_count="Whether to change to a character count page",
        descending="Whether to sort the cards by descending"
    )
    @app_commands.rename(
        character_name="character",
        card_age="card-age",
        in_sleeve="in-sleeve",
        by_card_id="by-card-id",
        by_character_count="by-character-count"
    )
    @app_commands.autocomplete(
        rarity=card_rarity_autocomplete,
        condition=card_condition_autocomplete,
        character_name=character_name_autocomplete
    )
    async def card_collection(
        self,
        interaction: discord.Interaction,
        owner: Optional[discord.Member | discord.User] = None,
        rarity: Optional[str] = None,
        condition: Optional[str] = None,
        character_name: Optional[str] = None,
        card_age: Optional[str] = None,
        locked: Optional[bool] = None,
        in_sleeve: Optional[bool] = None,
        by_card_id: bool = False,
        by_character_count: bool = False,
        descending: bool = False
    ):
        await interaction.response.defer(thinking=True)
        collection_owner = interaction.user if owner is None or interaction.user == owner else owner
        assert isinstance(collection_owner, discord.Member)

        player = Player(self.bot.pool, collection_owner.id)
        cards = await player.collection.get_cards()
        if not cards:
            embed = utils.create_interaction_embed(interaction, description="You currently don't own any cards.", level="error")
            if interaction.user != collection_owner:
                embed = utils.create_interaction_embed( interaction, description="This user does not own any cards.", level="error")
            
            await interaction.followup.send(embed=embed)
            return None
        
        filtered_cards = _filter_card_collection(
            cards=cards,
            rarity=rarity,
            condition=condition,
            character_name=character_name,
            card_age=card_age,
            locked=locked,
            in_sleeve=in_sleeve,
            by_card_id=by_card_id,
            descending=descending
        )
        if not filtered_cards:
            embed = utils.create_interaction_embed(interaction, description="No cards match the provided filters.", level="error")
            await interaction.followup.send(embed=embed)
            return None
        
        card_limit = await player.get_backpack_capacity()
        if not by_character_count:
            await _paginate_card_collection(
                interaction,
                cards=filtered_cards,
                card_count=len(cards),
                user=collection_owner,
                card_limit=card_limit
            )
            return None
        
        await _paginate_character_count(interaction, cards, collection_owner, card_limit, descending)

    @card_command_group.cooldown(1, 5)
    @card_command_group.command(name="view", description="View a card to reveal more information about said card")
    @app_commands.describe(card_id="The ID of the card you want to view")
    @app_commands.rename(card_id="card-id")
    @app_commands.autocomplete(card_id=card_id_autocomplete)
    async def card_view(self, interaction: discord.Interaction, card_id: Optional[str] = None):
        await interaction.response.defer(thinking=True)

        player = Player(self.bot.pool, interaction.user.id)
        if card_id is None:
            card = await player.collection.get_most_recently_obtained_card()
        else:
            card = await player.collection.get_card(card_id)

        if card is None and card_id is None:
            embed = utils.create_interaction_embed(
                interaction,
                description="You are currently not registered.",
                level="error"
            )
            await interaction.followup.send(embed=embed)
            return None
        
        if card is None:
            embed = utils.create_interaction_embed(
                interaction,
                description=f"I could not find any card with the ID **`{card_id}`**.",
                level="error"
            )
            await interaction.followup.send(embed=embed)
            return None
        
        card_id = card_id or card.card_id
        user_id = await player.collection.get_card_owner_user_id(card_id)
        assert user_id
        card_owner = await self.bot.fetch_user(user_id)
        card_age = (discord.utils.utcnow() - card.created_at).total_seconds()
        card_rarity = card.rarity
        card_condition = card.condition
        card_character_name = card.character_name
        card_is_shiny = card.is_shiny

        card_image = CardFactory.generate_card(
            card_id=card_id,
            rarity=card_rarity,
            condition=card_condition,
            character_name=card_character_name,
            shiny=card_is_shiny
        ).image
        card_image_url, card_image_file = utils.save_image_to_discord_file(card_image, filename="card_preview")

        embed = utils.create_interaction_embed(
            interaction,
            title="Viewing card information.",
            color=card_rarity.color
        )
        embed.add_field(name="Owner:", value=card_owner.mention)
        embed.add_field(name="Card ID:", value=f"**`{card_id}`**")
        embed.add_field(name="Condition:", value=card_condition.display())
        embed.add_field(name="Rarity:", value=f"{card_rarity.display_emoji(True)} **{card_rarity.display_name}**")
        embed.add_field(name="Character Name:", value=f"{f'{enums.DiscordEmoji.RARITY_LETTER_SHINY} ' if card_is_shiny else ''}**{card_character_name}**")
        embed.add_field(name="Age:", value=f"`{utils.seconds_to_human(card_age)}`")
        embed.add_field(name="Locked:", value=str(card.is_locked))
        embed.add_field(name="In Card Sleeve:", value=str(card.in_sleeve))
        embed.add_field(name="", value="")
        embed.set_image(url=card_image_url)
        await interaction.followup.send(embed=embed, file=card_image_file)

    @card_command_group.cooldown(1, 60)
    @card_command_group.command(
        name="burn", 
        description="Burn a single or multiple cards in exchange for silver and other items"
    )
    @app_commands.describe(card_ids="The ID of the cards you want to burn, separate by space, or all")
    @app_commands.rename(card_ids="card-ids")
    async def card_burn(self, interaction: discord.Interaction, card_ids: Optional[str] = None):
        await interaction.response.defer(thinking=True)

        player = Player(self.bot.pool, interaction.user.id)
        if card_ids is None:
            card = await player.collection.get_most_recently_obtained_card()
            if card is None:
                utils.reset_command_cooldown(interaction)
                embed = utils.create_interaction_embed(
                    interaction,
                    description="You currently don't own any cards.",
                    level="error"
                )
                await interaction.followup.send(embed=embed)
                return None
            
            await _handle_card_burn_single(interaction, card)
            return None
        
        if card_ids.casefold() == "all":
            await _handle_card_burn_all(interaction)
            return None
        
        filtered_card_ids = _filter_possible_card_ids(card_ids)
        if len(filtered_card_ids) == 1:
            card = await player.collection.get_card(filtered_card_ids[0])
            if card is None:
                utils.reset_command_cooldown(interaction)
                embed = utils.create_interaction_embed(
                    interaction,
                    description=f"I could not find any card with the ID **`{card_ids}`**.",
                    level="error"
                )
                await interaction.followup.send(embed=embed)
                return None
            
            player_table = await player.get_table()
            assert player_table
            if card.fk_user_id != player_table.id:
                utils.reset_command_cooldown(interaction)
                embed = utils.create_interaction_embed(
                    interaction,
                    description="You can only burn cards you own.",
                    level="error"
                )
                await interaction.followup.send(embed=embed)
                return None
            
            await _handle_card_burn_single(interaction, card)

        elif len(filtered_card_ids) > 1:
            has_duplicate_card_ids = [item for item, count in Counter(filtered_card_ids).items() if count > 1]
            if has_duplicate_card_ids:
                utils.reset_command_cooldown(interaction)
                embed = utils.create_interaction_embed(
                    interaction,
                    description="Please don't duplicate your card IDs.",
                    level="error"
                )
                await interaction.followup.send(embed=embed)
                return None
            
            cards = await player.collection.get_cards_by_card_id(filtered_card_ids)
            if not cards:
                utils.reset_command_cooldown(interaction)
                embed = utils.create_interaction_embed(
                    interaction,
                    description="I couldn't find any cards with the IDs you provided.",
                    level="error"
                )
                await interaction.followup.send(embed=embed)
                return None
            
            await _handle_card_burn_multi(interaction, cards)

    @card_command_group.command(
        name="lock",
        description="Lock a card so that you don't accidentally burn it or use it for crafting"
    )
    @app_commands.describe(card_ids="The ID of the cards you want to lock")
    @app_commands.rename(card_ids="card-ids")
    async def card_lock(self, interaction: discord.Interaction, card_ids: str):
        await interaction.response.defer(thinking=True)
        await _handle_card_lock(interaction, "lock", card_ids)
        

async def setup(bot: Fancards) -> None:
    await bot.add_cog(CardCog(bot))
