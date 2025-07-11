from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union, Optional, Self

from fancards.enums import CardRarity, CardCondition, Item


if TYPE_CHECKING:
    from asyncpg import Record

__all__ = (
    "DataTable",
    "UserData",
    "GuildData",
    "BotData",
    "UserTable",
    "BalanceTable",
    "LevelTable",
    "CardTable",
    "ItemTable",
    "RewardsDailyTable",
    "RewardsVoteTable",
    "ConfigTable",
    "BlacklistTable"
)

DataTable = Union["UserData", "GuildData", "BotData"]


class Schema:
    pass


class UserData(Schema):
    """Represents the ``user_data`` schema."""
    pass


class GuildData(Schema):
    """Represents the ``guild_data`` schema."""
    pass


class BotData(Schema):
    """Represents the ``bot_data`` schema."""
    pass


@dataclass(frozen=True)
class UserTable(UserData):
    """Represents the ``user_data.user`` table."""
    id: int
    discord_user_id: int
    registered_at: datetime.datetime
    backpack_level: int = 1


@dataclass(frozen=True)
class BalanceTable(UserData):
    """Represents the ``user_data.balance`` table."""
    fk_user_id: int
    silver: int = 0
    star: int = 0
    gem: int = 0
    voucher: int = 0


@dataclass(frozen=True)
class LevelTable(UserData):
    """Represents the ``user_data.level`` table."""
    fk_user_id: int
    current_level: int = 1
    current_xp: int = 0
    required_xp: int = 42


@dataclass(frozen=True)
class CardTable(UserData):
    """Represents the ``user_data.card`` table."""
    card_id: str
    fk_user_id: int
    rarity: CardRarity
    condition: CardCondition
    character_name: str
    created_at: datetime.datetime
    is_shiny: bool = False
    is_locked: bool = False
    in_sleeve: bool = False

    @classmethod
    def record_to_table(cls, record: Record) -> Self:
        return cls(
            card_id=record["card_id"],
            fk_user_id=record["fk_user_id"],
            rarity=CardRarity(record["rarity"]),
            condition=CardCondition(record["condition"]),
            character_name=record["character_name"],
            created_at=record["created_at"],
            is_shiny=record["is_shiny"],
            is_locked=record["is_locked"],
            in_sleeve=record["in_sleeve"]
        )


@dataclass(frozen=True)
class ItemTable(UserData):
    """Represents the ``user_data.item`` table."""
    fk_user_id: int
    item: Item
    item_quantity: int

    @classmethod
    def record_to_table(cls, record: Record) -> Self:
        return cls(
            fk_user_id=record["fk_user_id"],
            item=Item(record["item_name"]),
            item_quantity=record["item_quantity"]
        )


@dataclass(frozen=True)
class RewardsDailyTable(UserData):
    """Represents the ``user_data.rewards_daily`` table."""
    fk_user_id: int
    streak: int = 0
    claimed_at: Optional[datetime.datetime] = None
    reset_at: Optional[datetime.datetime] = None


@dataclass(frozen=True)
class RewardsVoteTable(UserData):
    """Represents the ``user_data.rewards_vote`` table."""
    fk_user_id: int
    streak: int = 0
    voted_at: Optional[datetime.datetime] = None


@dataclass(frozen=True)
class ConfigTable(GuildData):
    """Represents the ``guild_data.config`` table."""
    discord_guild_id: int
    toggle_notification_level_up: bool = True


@dataclass(frozen=True)
class BlacklistTable(BotData):
    """Represents the ``bot_data.blacklist`` table."""
    discord_user_id: int
    reason: str
