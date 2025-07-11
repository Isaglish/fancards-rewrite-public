from enum import Enum
from typing import Self, Optional
from dataclasses import dataclass

from discord import Color

from .weight import WeightData
from ..discord_emoji import DiscordEmoji
from ..fancolor import Fancolor


__all__ = ("CardRarity",)


@dataclass(frozen=True)
class CardRarityData:
    index: int
    exclusive: bool
    color: Color
    silver_values: Optional[tuple[int, int]]
    star_value: Optional[int]
    letter_emoji: DiscordEmoji
    card_emoji: DiscordEmoji
    weight: Optional[WeightData]


class CardRarity(Enum):
    """Represents a card rarity.
    
    Supports rich comparison.
    """
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    MYTHIC = "mythic"
    LEGENDARY = "legendary"
    EXOTIC = "exotic"
    NIGHTMARE = "nightmare"
    ICICLE = "icicle"
    
    def __str__(self) -> str:
        return self.value
    
    def __hash__(self) -> int:
        return hash(self.value)
    
    def __eq__(self, other: Self) -> bool:
        return self.index == other.index
    
    def __ne__(self, other: Self) -> bool:
        return self.index != other.index

    def __lt__(self, other: Self) -> bool:
        return self.index < other.index
    
    def __le__(self, other: Self) -> bool:
        return self.index <= other.index

    def __gt__(self, other: Self) -> bool:
        return self.index > other.index
    
    def __ge__(self, other: Self) -> bool:
        return self.index >= other.index
    
    @property
    def display_name(self) -> str:
        name = self.value
        if self.exclusive:
            name = f"exclusive - {name}"
            return name.title()
    
        return name.title()

    @property
    def index(self) -> int:
        return self.get_data().index

    @property
    def exclusive(self) -> bool:
        return self.get_data().exclusive
    
    @property
    def color(self) -> Color:
        return self.get_data().color
    
    @property
    def silver_values(self) -> Optional[tuple[int, int]]:
        return self.get_data().silver_values
    
    @property
    def star_value(self) -> Optional[int]:
        return self.get_data().star_value
    
    @property
    def weight(self) -> Optional[WeightData]:
        return self.get_data().weight
    
    @property
    def is_valuable(self) -> bool:
        return self.silver_values is None or self.star_value is None
    
    def display_emoji(self, letter: bool) -> DiscordEmoji:
        data = self.get_data()
        return data.letter_emoji if letter else data.card_emoji
    
    @classmethod
    def get_non_exclusive_rarities(cls) -> list[Self]:
        return [rarity for rarity in cls if not rarity.exclusive]
    
    @classmethod
    def get_exclusive_rarities(cls) -> list[Self]:
        return [rarity for rarity in cls if rarity.exclusive]
    
    def get_data(self) -> CardRarityData:
        mapping = {
            self.COMMON: CardRarityData(
                index=1,
                exclusive=False,
                color=Fancolor.GRAY(),
                silver_values=(10, 40),
                star_value=3,
                letter_emoji=DiscordEmoji.RARITY_LETTER_COMMON,
                card_emoji=DiscordEmoji.RARITY_CARD_COMMON,
                weight=WeightData(
                    new_user=65,
                    normal=46.5,
                    premium=None
                )
            ),
            self.UNCOMMON: CardRarityData(
                index=2,
                exclusive=False,
                color=Fancolor.LIGHT_GREEN(),
                silver_values=(50, 75),
                star_value=12,
                letter_emoji=DiscordEmoji.RARITY_LETTER_UNCOMMON,
                card_emoji=DiscordEmoji.RARITY_CARD_UNCOMMON,
                weight=WeightData(
                    new_user=20,
                    normal=30,
                    premium=50
                )
            ),
            self.RARE: CardRarityData(
                index=3,
                exclusive=False,
                color=Fancolor.LIGHT_BLUE(),
                silver_values=(100, 350),
                star_value=33,
                letter_emoji=DiscordEmoji.RARITY_LETTER_RARE,
                card_emoji=DiscordEmoji.RARITY_CARD_RARE,
                weight=WeightData(
                    new_user=10,
                    normal=16.1,
                    premium=30
                )
            ),
            self.EPIC: CardRarityData(
                index=4,
                exclusive=False,
                color=Fancolor.LIGHT_PURPLE(),
                silver_values=(500, 750),
                star_value=72,
                letter_emoji=DiscordEmoji.RARITY_LETTER_EPIC,
                card_emoji=DiscordEmoji.RARITY_CARD_EPIC,
                weight=WeightData(
                    new_user=5,
                    normal=6,
                    premium=16.5
                )
            ),
            self.MYTHIC: CardRarityData(
                index=5,
                exclusive=False,
                color=Fancolor.LIGHT_RED(),
                silver_values=(1000, 4750),
                star_value=138,
                letter_emoji=DiscordEmoji.RARITY_LETTER_MYTHIC,
                card_emoji=DiscordEmoji.RARITY_CARD_MYTHIC,
                weight=WeightData(
                    new_user=None,
                    normal=1.25,
                    premium=2.75
                )
            ),
            self.LEGENDARY: CardRarityData(
                index=6,
                exclusive=False,
                color=Fancolor.LIGHT_YELLOW(),
                silver_values=(5000, 9750),
                star_value=228,
                letter_emoji=DiscordEmoji.RARITY_LETTER_LEGENDARY,
                card_emoji=DiscordEmoji.RARITY_CARD_LEGENDARY,
                weight=WeightData(
                    new_user=None,
                    normal=0.15,
                    premium=0.75
                )
            ),
            self.EXOTIC: CardRarityData(
                index=7,
                exclusive=False,
                color=Fancolor.LIGHT_ORANGE(),
                silver_values=None,
                star_value=486,
                letter_emoji=DiscordEmoji.RARITY_LETTER_EXOTIC,
                card_emoji=DiscordEmoji.RARITY_CARD_EXOTIC,
                weight=None
            ),
            self.NIGHTMARE: CardRarityData(
                index=8,
                exclusive=False,
                color=Fancolor.BLACK(),
                silver_values=None,
                star_value=972,
                letter_emoji=DiscordEmoji.RARITY_LETTER_NIGHTMARE,
                card_emoji=DiscordEmoji.RARITY_CARD_NIGHTMARE,
                weight=None
            ),
            self.ICICLE: CardRarityData(
                index=101,
                exclusive=True,
                color=Fancolor.LIGHT_BLUE(),
                silver_values=None,
                star_value=None,
                letter_emoji=DiscordEmoji.RARITY_LETTER_EXCLUSIVE,
                card_emoji=DiscordEmoji.RARITY_CARD_ICICLE,
                weight=None
            )
        }
        return mapping[self]
