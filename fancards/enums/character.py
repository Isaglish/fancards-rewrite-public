import json
import random
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from .card_property import CardRarity


__all__ = ("Character",)

with open("fancards/json/characters.json", "r") as file:
    characters_json = json.load(file)


@dataclass(frozen=True)
class CharacterData:
    display_name: str
    reference_name: str
    creator: str
    origin: str
    rarity: CardRarity


class Character(Enum):
    COMMON = [
        CharacterData(
            **character_data,
            rarity=CardRarity.COMMON
        ) for character_data in characters_json["common"]
    ]
    UNCOMMON = [
        CharacterData(
            **character_data,
            rarity=CardRarity.UNCOMMON
        ) for character_data in characters_json["uncommon"]
    ]
    RARE = [
        CharacterData(
            **character_data,
            rarity=CardRarity.RARE
        ) for character_data in characters_json["rare"]
    ]
    EPIC = [
        CharacterData(
            **character_data,
            rarity=CardRarity.EPIC
        ) for character_data in characters_json["epic"]
    ]
    MYTHIC = [
        CharacterData(
            **character_data,
            rarity=CardRarity.MYTHIC
        ) for character_data in characters_json["mythic"]
    ]
    LEGENDARY = [
        CharacterData(
            **character_data,
            rarity=CardRarity.LEGENDARY
        ) for character_data in characters_json["legendary"]
    ]
    EXOTIC = [
        CharacterData(
            **character_data,
            rarity=CardRarity.EXOTIC
        ) for character_data in characters_json["exotic"]
    ]
    NIGHTMARE = [
        CharacterData(
            **character_data,
            rarity=CardRarity.NIGHTMARE
        ) for character_data in characters_json["nightmare"]
    ]

    @classmethod
    def get_all_characters(cls) -> list[CharacterData]:
        """Gets every single character regardless of their assigned rarity."""        
        characters: list[CharacterData] = []
        for character_rarity in cls:
            characters.extend(character_rarity.value)

        return characters
    
    @classmethod
    def get_character_rarity(cls, name: str) -> CardRarity:
        """Returns the rarity of the character with the provided ``name``."""
        character_mapping = {character.display_name: character.rarity for character in cls.get_all_characters()}
        if name in character_mapping:
            return character_mapping[name]
            
        raise ValueError(f"Character '{name}' does not exist.")
    
    @classmethod
    def get_character_data(cls, name: str) -> CharacterData:
        """Returns the data of the character with the provided ``name``."""
        character_mapping = {character.display_name: character for character in cls.get_all_characters()}
        if name in character_mapping:
            return character_mapping[name]
            
        raise ValueError(f"Character '{name}' does not exist.")
    
    @classmethod
    def get_random_character(cls, rarity: Optional[CardRarity] = None) -> CharacterData:
        """Returns a random character assigned with the ``rarity``.

        Returns a random character regardless of their assigned rarity if ``rarity`` is ``None``
        or if it is exclusive.
        """
        if rarity is None or rarity.exclusive:
            character = random.choice(cls.get_all_characters())  # pick a random character from all rarities
        else:
            character: CharacterData = random.choice(getattr(cls, rarity.name).value)

        return character
    