import re
from io import BytesIO
from typing import Any

from discord import File
from PIL import Image

from .. import enums


__all__ = (
    "create_progress_bar",
    "save_image_to_discord_file",
    "parse_arguments",
    "get_card_property_text"
)


def create_progress_bar(progress: int, total: int, length: int) -> str:
    """Creates a progress bar using unicodes.

    Progress: ▰▰▰▰▰▰▱▱▱▱▱▱ 50%
    
    Parameters
    ----------
    progress: :class:`int`
        How much the bar is filled.
    total: :class:`int`
        How much until the bar is full (100%).
    length: :class:`int`
        The amount of characters. e.g. 4 is ▱▱▱▱
    
    Returns
    -------
    :class:`str`
        The progress bar
    """
    filled = int(progress / total * length)
    bar = f"{'▰' * filled}{'▱' * (length - filled)} {progress}%"
    return bar


def save_image_to_discord_file(
    image: Image.Image,
    *,
    filename: str = "unknown_image",
    format: str = "png"
) -> tuple[str, File]:
    """Converts a :class:`PIL.Image.Image` and saves it into a :class:`discord.File`.
    
    Parameters
    ----------
    image: :class:`PIL.Image.Image`
        The image to save.
    filename: :class:`str`
        The name of the file.
    format: :class:`str`
        The file extension to use.
    
    Returns
    -------
    tuple[:class:`str`, :class:`discord.File`]
        The url "attachment://unknown_image.png" for :meth:`discord.Embed.set_image(url=)` and the saved image file.
    """
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)

    full_filename = f"{filename}.{format}"
    url = f"attachment://{full_filename}"

    return (url, File(buffer, filename=full_filename))


def parse_arguments(table: dict[str, Any], string: str) -> str:
    """Parses ``string`` and replaces ``$key`` with values from ``table``
    
    Parameters
    ----------
    table: dict[:class:`str`, :class:`Any`]
        The table to take arguments and values from.
    string: :class:`str`
        The string to parse.
    
    Returns
    -------
    :class:`str`
        The string with the replaced values.
    """
    pattern = re.compile(r"(\$\w+)")
    return re.sub(
        pattern,
        lambda match: str(table.get(match.group(1), "")),
        string
    )


def get_card_property_text(
    *,
    card_id: str,
    rarity: enums.CardRarity,
    condition: enums.CardCondition,
    character_name: str,
    is_shiny: bool,
    is_locked: bool = False,
    in_sleeve: bool = False
) -> str:
    lock_icon = enums.DiscordEmoji.ICON_LOCKED if is_locked else enums.DiscordEmoji.ICON_UNLOCKED
    sleeve = f" | {enums.DiscordEmoji.ITEM_CARD_SLEEVE}" if in_sleeve else ""
    rarity_str = f"{rarity.display_emoji(False)} | {enums.DiscordEmoji.RARITY_LETTER_SHINY}" if is_shiny else f"{rarity.display_emoji(False)} |"

    return f"{lock_icon} | **`{card_id}`** | `{condition.unicode}` | {rarity_str} **{character_name}**{sleeve}"
