from enum import Enum

import discord


__all__ = ("Fancolor",)


class Fancolor(Enum):
    LIGHT_BROWN = "df9191"
    BROWN = "bc6578"
    DARK_BROWN = "914d5a"
    LIGHT_PASTEL_BROWN = "fee4e3"
    PASTEL_BROWN = "ffcab8"
    DARK_PASTEL_BROWN = "faaa9f"
    LIGHT_PURPLE = "ab83fe"
    PURPLE = "8567d7"
    DARK_PURPLE = "654da1"
    LIGHT_PINK = "ffb2e6"
    PINK = "ff8dc9"
    DARK_PINK = "e868a5"
    LIGHT_RED = "ff9393"
    RED = "fe4a67"
    DARK_RED = "be304a"
    LIGHT_ORANGE = "ffa279"
    ORANGE = "ff6748"
    DARK_ORANGE = "cc4a3a"
    LIGHT_YELLOW = "ffff6f"
    YELLOW = "fece00"
    DARK_YELLOW = "eaa000"
    LIGHT_GREEN = "aaff63"
    GREEN = "3cbd46"
    DARK_GREEN = "01874a"
    LIGHT_BLUE = "00c0ff"
    BLUE = "0088fe"
    DARK_BLUE = "0065d9"
    WHITE = "ffffff"
    LIGHT_GRAY = "e3e6ef"
    GRAY = "acafc2"
    DARK_GRAY = "606279"
    DARKER_GRAY = "3b3c50"
    BLACK = "1c1c28"

    def __str__(self) -> str:
        return f"#{self.value}"

    def __call__(self) -> discord.Color:
        return discord.Color.from_str(str(self))
