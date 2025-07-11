from __future__ import annotations

import random
import string
from math import ceil
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageChops, ImageFont

from fancards.enums import (
    Weight,
    CardRarity,
    CardCondition,
    Character
)
from fancards.enums.card_property.condition import Texture


if TYPE_CHECKING:
    from fancards.enums.character import CharacterData

__all__ = (
    "CardFactory",
    "CardImage",
    "CARD_ID_LENGTH"
)

BALOO_FONT_PATH = "assets/Baloo.ttf"
CARD_ID_LENGTH = 6


def _random_number() -> float:
    return random.random() * 100


def _convert_resize_texture(card_image: Image.Image, texture: Image.Image) -> Image.Image:
    texture = texture.convert("RGBA")
    texture = texture.resize(card_image.size)
    return texture


def _generate_card(
    *,
    card_id: Optional[str],
    rarity: Optional[CardRarity],
    condition: Optional[CardCondition],
    character_name: Optional[str],
    weight: Optional[Weight],
    shiny: bool,
    patreon: bool,
    show_card_id: bool,
    show_card_condition: bool,
    show_card_character_image: bool
) -> CardImage:
    card_rarity = rarity or CardFactory.get_card_rarity(weight)
    card_image = Image.open(f"assets/card_templates/{card_rarity.name.lower()}.png")
    card_condition = condition or CardFactory.get_card_condition(weight)
    is_shiny = shiny or CardFactory.get_shiny(weight, patreon)
    card_id = card_id or CardFactory.generate_card_id()

    if character_name is None:
        character = Character.get_random_character(card_rarity)
    else:
        character = Character.get_character_data(character_name)

    if character.display_name == "Troll":
        card_id = "7R0115"

    if show_card_id:
        card_image = CardFactory.add_card_id(card_image, card_id)

    if show_card_character_image:
        card_image = CardFactory.add_character_image(card_image, character)

    if show_card_condition:
        card_image = CardFactory.add_texture(card_image, card_condition, is_shiny)

    card = CardImage(
        image=card_image,
        rarity=card_rarity,
        condition=card_condition,
        character=character,
        card_id=card_id,
        is_shiny=is_shiny
    )

    return card


@dataclass
class CardImage:
    image: Image.Image
    rarity: CardRarity
    condition: CardCondition
    character: CharacterData
    card_id: str
    is_shiny: bool


class CardFactory:
    @staticmethod
    def get_card_rarity(weight: Optional[Weight] = None) -> CardRarity:
        """Gets a random :class:`CardRarity` based on the given ``weight``.
        
        Parameters
        ----------
        weight: Optional[:class:`Weight`].
            The weight type to use for comparison. Defaults to ``Weight.NORMAL`` if ``None``.
        
        Returns
        -------
        :class:`CardRarity`
            The rarest rarity if possible, otherwise the most common rarity of the list of options.
        """
        weight = weight or Weight.NORMAL
        random_number = _random_number()
        rarities = CardRarity.get_non_exclusive_rarities()

        possible_rarities: list[CardRarity] = []
        for rarity in rarities:
            if rarity.weight is None:
                continue

            rarity_weight: Optional[float] = getattr(rarity.weight, weight.name.lower())  # similar to rarity.weight.normal
            if rarity_weight is not None and random_number <= rarity_weight :
                possible_rarities.append(rarity)

        if len(possible_rarities) > 0:
            return max(possible_rarities, key=lambda r: r.index)  # return the rarest rarity
        
        # return the most common rarity of that specific weight
        return max(
            [rarity for rarity in rarities if rarity.weight is not None],
            key=lambda r: getattr(r.weight, weight.name.lower()) or -1
        )

    @staticmethod
    def get_card_condition(weight: Optional[Weight] = None) -> CardCondition:
        """Gets a random condition based on the given ``weight``.
        
        Parameters
        ----------
        weight: Optional[:class:`Weight`].
            The weight type to use for comparison. Defaults to ``Weight.NORMAL`` if ``None``.
        
        Returns
        -------
        :class:`CardCondition`
            A random condition if possible, otherwise ``CardCondition.GOOD``.
        """
        weight = weight or Weight.NORMAL
        random_number = _random_number()
        conditions = [condition for condition in CardCondition]

        possible_conditions: list[CardCondition] = []
        for condition in conditions:
            condition_weight: Optional[float] = getattr(condition.weight, weight.name.lower())  # similar to condition.weight.new_user
            if condition_weight is not None and random_number <= condition_weight:
                possible_conditions.append(condition)

        if len(possible_conditions) > 0:
            return random.choice(possible_conditions)
        
        return CardCondition.GOOD  # return 'GOOD' if the random number is too high
    
    @staticmethod
    def get_shiny_weight(weight: Weight, patreon: bool) -> float:
        match weight:
            case Weight.NEW_USER:
                shiny_weight = -1  # no shiny for new users
            case Weight.NORMAL:
                shiny_weight = 0.05
            case Weight.PREMIUM:
                shiny_weight = 0.2

        if patreon:
            shiny_weight *= 2

        return shiny_weight

    @classmethod
    def get_shiny(cls, weight: Optional[Weight] = None, patreon: bool = False) -> bool:
        """Determines if an item is shiny based on the provided ``weight``.
        
        Parameters
        ----------
        weight: Optional[:class:`Weight`].
            The weight type to use for comparison. Defaults to ``Weight.NORMAL`` if ``None``.
        patreon: :class:`bool`
            Doubles the value of ``weight`` if ``True``.
        
        Returns
        -------
        :class:`bool`
            The shiny state.
        """
        weight = weight or Weight.NORMAL
        random_number = _random_number()
        shiny_weight = cls.get_shiny_weight(weight, patreon)
        return random_number <= shiny_weight
    
    @classmethod
    def generate_card(
        cls,
        *,
        card_id: Optional[str] = None,
        rarity: Optional[CardRarity] = None,
        condition: Optional[CardCondition] = None,
        character_name: Optional[str] = None,
        weight: Optional[Weight] = None,
        shiny: bool = False,
        patreon: bool = False,
        show_card_id: bool = True,
        show_card_condition: bool = True,
        show_card_character_image: bool = True
    ) -> CardImage:
        """Generates a card.
        
        Parameters
        ----------
        rarity: Optional[:class:`CardRarity`]
            The rarity of the card.
            If ``None`` then a random rarity is generated based on ``weight``.
        condition: Optional[:class:`CardCondition`]
            The condition of the card.
            If ``None`` then a random condition is generated based on ``weight``.
        weight: Optional[:class:`Weight`]
            The weight type to use for randomized ``rarity``, ``condition``, and ``shiny``.
            Defaults to ``Weight.NORMAL``
        shiny: :class:`bool`
            Whether or not the card is shiny.
        
        Returns
        -------
        :class:`CardImage`
            The generated card.
        """
        card = _generate_card(
            card_id=card_id,
            rarity=rarity,
            condition=condition,
            character_name=character_name,
            weight=weight,
            shiny=shiny,
            patreon=patreon,
            show_card_id=show_card_id,
            show_card_condition=show_card_condition,
            show_card_character_image=show_card_character_image
        )
        return card

    @classmethod
    def generate_cards(
        cls,
        *,
        amount: int = 3,
        card_id: Optional[str] = None,
        rarity: Optional[CardRarity] = None,
        condition: Optional[CardCondition] = None,
        character_name: Optional[str] = None,
        weight: Optional[Weight] = None,
        shiny: bool = False,
        patreon: bool = False,
        show_card_id: bool = True,
        show_card_condition: bool = True,
        show_card_character_image: bool = True
    ) -> list[CardImage]:
        """Generates a specified ``amount`` of cards.
        
        Parameters
        ----------
        amount: :class:`int`
            The amount of cards to generate.
        rarity: Optional[:class:`CardRarity`]
            The rarity of the cards.
            If ``None`` then a random rarity is generated based on ``weight``.
        condition: Optional[:class:`CardCondition`]
            The condition of the cards.
            If ``None`` then a random condition is generated based on ``weight``.
        weight: Optional[:class:`Weight`]
            The weight type to use for randomized ``rarity``, ``condition``, and ``shiny``.
            Defaults to ``Weight.NORMAL``
        shiny: :class:`bool`
            Whether or not the cards are shiny.
        
        Returns
        -------
        list[:class:`CardImage`]
            The list of generated cards.
        """
        cards: list[CardImage] = []
        for _ in range(amount):
            card = _generate_card(
                card_id=card_id,
                rarity=rarity,
                condition=condition,
                character_name=character_name,
                weight=weight,
                shiny=shiny,
                patreon=patreon,
                show_card_id=show_card_id,
                show_card_condition=show_card_condition,
                show_card_character_image=show_card_character_image
            )
            cards.append(card)
        return cards

    @staticmethod
    def generate_card_id() -> str:
        """Generates a random six-letter card ID. 
        
        Returns
        -------
        :class:`str`
            The generated card ID.
        """
        card_id = string.digits + string.ascii_lowercase + string.digits
        return "".join(random.choices(card_id, k=CARD_ID_LENGTH))

    @staticmethod
    def add_texture(card_image: Image.Image, condition: CardCondition, shiny: bool) -> Image.Image:
        """Adds a texture to ``card_image`` based on ``condition`` and ``shiny``.
        
        Parameters
        ----------
        card_image: :class:`PIL.Image.Image`
            The image to add textures to.
        condition: :class:`CardCondition`
            The condition texture to add.
        shiny: :class:`bool`
            Set to ``True`` to add a shiny texture.
        
        Returns
        -------
        :class:`PIL.Image.Image`
            The image with the added textures.
        """
        card_image = card_image.convert("RGBA")
        transparent_image = Image.new("RGBA", card_image.size, (0, 0, 0, 0))
        
        if shiny:
            texture = Image.open(Texture.SHINY.get_image_path())
            texture = _convert_resize_texture(card_image, texture)
            texture = Image.blend(transparent_image, texture, alpha=0.4)
            card_image = ImageChops.screen(card_image, texture)

        if condition is CardCondition.MINT:
            return card_image  # 'MINT' condition does not have a texture
        
        texture = Image.open(getattr(Texture, condition.name).get_image_path())  # similar to Image.open(Texture.CONDITION.get_image_path())
        if condition is CardCondition.PRISTINE:
            texture = _convert_resize_texture(card_image, texture)
            return Image.alpha_composite(card_image, texture)
        
        elif condition is CardCondition.NEAR_MINT:
            texture = _convert_resize_texture(card_image, texture)
            texture = Image.blend(transparent_image, texture, alpha=0.5)
            return ImageChops.screen(card_image, texture)

        else:
            texture = _convert_resize_texture(card_image, texture)
            return ImageChops.screen(card_image, texture)
        
    @staticmethod
    def add_card_id(card_image: Image.Image, card_id: str) -> Image.Image:
        """Adds ``card_id`` as text to ``card_image``.
        
        Parameters
        ----------
        card_image: :class:`PIL.Image.Image`
            The image to add the text on.
        card_id: :class:`str`
            The text to add.
        
        Returns
        -------
        :class:`PIL.Image.Image`
            The image with the added text.
        """
        font = ImageFont.truetype(BALOO_FONT_PATH, 17)
        draw = ImageDraw.Draw(card_image)
        draw.text((37, 510), f"#{card_id}", font=font)  # type: ignore
        return card_image

    @staticmethod
    def add_character_name(card_image: Image.Image, character_name: str) -> Image.Image:
        """Adds ``character_name`` as text to ``card_image``.
        
        Parameters
        ----------
        card_image: :class:`PIL.Image.Image`
            The image to add the text on.
        character_name: :class:`str`
            The text to add.
        
        Returns
        -------
        :class:`PIL.Image.Image`
            The image with the added text.
        """
        bound_width = 285
        bound_height = 50
        font_size = 49

        draw = ImageDraw.Draw(card_image)
        font = ImageFont.truetype(BALOO_FONT_PATH, font_size)
        width, height = draw.multiline_textsize(character_name, font=font)

        while width > bound_width:
            font_size -= 1
            font = ImageFont.truetype(BALOO_FONT_PATH, font_size)
            width, height = draw.textbbox((0, 0), character_name, font=font)[2:]

        x = (card_image.width - width) / 2
        y = (900 - height) / 2 + 5

        if height > bound_height:
            y -= 5

        draw.multiline_text((x, y), character_name, font=font)
        return card_image

    @classmethod
    def add_character_image(cls, card_image: Image.Image, character: CharacterData) -> Image.Image:
        """Adds the image of ``character`` to ``card_image``.
        
        Parameters
        ----------
        card_image: :class:`PIL.Image.Image`
            The image to paste the character image on.
        character: :class:`CharacterData`
            The data of the character.
        
        Returns
        -------
        :class:`PIL.Image.Image`
            The image with the character image pasted.
        """
        character_image = Image.open(f"assets/character_images/{character.reference_name}.png")
        card_image = cls.add_character_name(card_image, character.display_name)
        card_image.paste(character_image, (0, 0), mask=character_image)
        return card_image

    @staticmethod
    def align_card_images(
        card_images: list[Image.Image],
        cards_per_row: int = 3,
        pixel_offset: int = 30
    ) -> Image.Image:
        """Aligns the ``card_images`` for display.
        
        Parameters
        ----------
        card_images: list[:class:`PIL.Image.Image`]
            The list of images to align.
        cards_per_row: :class:`int`
            How many cards to align per row.
        pixel_offset: :class:`int`
            The amount of offset in pixels. (The gap between images)
        
        Returns
        -------
        :class:`PIL.Image.Image`
            The image with the aligned ``card_images``.
        """
        width = max([card_image.width for card_image in card_images]) + pixel_offset
        height = max([card_image.height for card_image in card_images]) + pixel_offset

        # TODO: implement this when album gets added.
        # if album:
        #     page_width = width * cards_per_row
        #     page_height = height * cards_per_row

        page_width = width * len(card_images)
        page_width = width * cards_per_row if page_width > width * cards_per_row else page_width
        page_height = height * ceil((1*len(card_images)) / cards_per_row)

        page = Image.new("RGBA", (page_width, page_height), (0, 0, 0, 0))

        row = 0
        column = 0
        for card_image in card_images:
            if column != 0 and column % cards_per_row == 0:
                column = 0
                row += 1

            page.paste(card_image, (width*column, height*row))
            column += 1

        return page

    @staticmethod
    def upgrade_condition(condition: CardCondition) -> CardCondition:
        """Increases the ``condition.index`` by ``1``; upgrades the ``condition``.
        
        Parameters
        ----------
        condition: :class:`CardCondition`
            The condition to upgrade.
        
        Returns
        -------
        :class:`CardCondition`
            The upgraded condition.
            The original condition is returned if its index is the highest of all.
        """
        if condition == max(CardCondition):
            return condition
        
        condition_mapping = {condition.index: condition for condition in CardCondition}
        return condition_mapping[condition.index + 1]

    @staticmethod
    def downgrade_condition(condition: CardCondition) -> CardCondition:
        """Decreases the ``condition.index`` by ``1``; downgrades the ``condition``.
        
        Parameters
        ----------
        condition: :class:`CardCondition`
            The condition to downgrade.
        
        Returns
        -------
        :class:`CardCondition`
            The downgraded condition.
            The original condition is returned if its index is the lowest of all.
        """
        if condition == min(CardCondition):
            return condition
        
        condition_mapping = {condition.index: condition for condition in CardCondition}
        return condition_mapping[condition.index - 1]

    @classmethod
    def condition_comparison(cls, card: CardImage, old_condition: CardCondition, new_condition: CardCondition) -> Image.Image:
        """Creates a comparison image for preview. e.g. When upgrading a card's condition.
        
        Parameters
        ----------
        card: :class:`CardImage`
            The card to display.
        old_condition: :class:`CardCondition`
            The condition of the first card image.
        new_condition: :class:`CardCondition`
            The condition of the second card image.
        
        Returns
        -------
        :class:`PIL.Image.Image`
            The image created.
        """
        card_image = card.image
        original_image = cls.add_texture(card_image, old_condition, card.is_shiny)
        upgraded_card_image = cls.add_texture(card_image, new_condition, card.is_shiny)
        arrow_icon = Image.open("assets/arrow_right.png")

        pixel_offset = 120
        width = original_image.width + upgraded_card_image.width + pixel_offset
        height = max(original_image.height, upgraded_card_image.height)
        combined_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        combined_image.paste(original_image, (0,0))
        combined_image.paste(arrow_icon, ((combined_image.width // 2) - 50, (combined_image.height // 2) - 50))
        combined_image.paste(upgraded_card_image, (original_image.width + pixel_offset, 0))
        
        return combined_image
