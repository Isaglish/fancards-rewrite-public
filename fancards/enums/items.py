import json
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Self

from .currency import Currency
from .discord_emoji import DiscordEmoji


__all__ = ("Item",)

with open("fancards/json/items.json", "r") as file:
    item_json = json.load(file)


@dataclass(frozen=True)
class ItemShopData:
    price: int
    currency: Currency


@dataclass(frozen=True)
class ItemData:
    display_name: str
    description: str
    shop_data: Optional[ItemShopData]
    emoji_enum_name: str
    visible: bool
    usable: bool

    @property
    def emoji(self) -> str:
        mapping = {discord_emoji.name: discord_emoji.value for discord_emoji in DiscordEmoji}
        return mapping[self.emoji_enum_name]


class Item(Enum):
    GLISTENING_GEM = "glistening gem"
    FUSION_CRYSTAL = "fusion crystal"
    PREMIUM_DROP = "premium drop"
    CROWN = "crown"
    BACKPACK_UPGRADE = "backpack upgrade"
    CARD_PACK_RARE = "rare card pack"
    CARD_PACK_EPIC = "epic card pack"
    CARD_PACK_MYTHIC = "mythic card pack"
    CARD_PACK_LEGENDARY = "legendary card pack"
    CARD_PACK_EXOTIC = "exotic card pack"

    @property
    def display_name(self):
        return self.value
    
    @staticmethod
    def get_item_data_list() -> list[ItemData]:
        return [ItemData(**data) for data in item_json["items"]]

    @classmethod
    def get_item_data(cls, item: Self) -> ItemData:
        for item_data in cls.get_item_data_list():
            if item_data.display_name == item.display_name:
                return item_data

        raise ValueError("This item does not exist.")
    
    def display(self) -> str:
        item_data = self.get_item_data(self)
        return f"{item_data.emoji} **{self.display_name.title()}**"
