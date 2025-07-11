from enum import Enum
from dataclasses import dataclass

from .discord_emoji import DiscordEmoji


__all__ = ("Currency",)


@dataclass(frozen=True)
class CurrencyData:
    name: str
    emoji: DiscordEmoji


class Currency(Enum):
    SILVER = CurrencyData(
        name="silver",
        emoji=DiscordEmoji.CURRENCY_SILVER
    )
    STAR = CurrencyData(
        name="star",
        emoji=DiscordEmoji.CURRENCY_STAR
    )
    GEM = CurrencyData(
        name="gem",
        emoji=DiscordEmoji.CURRENCY_GEM
    )
    VOUCHER = CurrencyData(
        name="voucher",
        emoji=DiscordEmoji.CURRENCY_VOUCHER
    )

    def __str__(self) -> str:
        return self.value.name
    
    @property
    def emoji(self) -> DiscordEmoji:
        return self.value.emoji

    @property
    def display_name(self) -> str:
        return f"{self.value.emoji} **{self.value.name.title()}**"
    