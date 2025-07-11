from enum import Enum
from typing import Self, Optional
from dataclasses import dataclass

from .weight import WeightData


__all__ = ("CardCondition",)


@dataclass(frozen=True)
class CardConditionData:
    index: int
    unicode: str
    star_value: int
    weight: Optional[WeightData]


class CardCondition(Enum):
    """Represents a card condition.
    
    Supports rich comparison.
    """
    DAMAGED = "damaged" 
    POOR = "poor" 
    GOOD = "good" 
    NEAR_MINT = "near mint" 
    MINT = "mint" 
    PRISTINE = "pristine" 
    
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
        return self.value.title()

    @property
    def index(self) -> int:
        return self.get_data().index
    
    @property
    def unicode(self) -> str:
        return self.get_data().unicode
    
    @property
    def star_value(self) -> int:
        return self.get_data().star_value
    
    @property
    def weight(self) -> Optional[WeightData]:
        return self.get_data().weight
    
    def display(self) -> str:
        return f"`{self.display_name.title()} {self.unicode}`"
    
    def get_data(self) -> CardConditionData:
        mapping = {
            self.DAMAGED: CardConditionData(
                index=1,
                unicode="▱▱▱▱▱",
                star_value=3,
                weight=WeightData(
                    new_user=16,
                    normal=10,
                    premium=10
                )
            ),
            self.POOR: CardConditionData(
                index=2,
                unicode="▰▱▱▱▱",
                star_value=12,
                weight=WeightData(
                    new_user=45,
                    normal=20,
                    premium=20
                )
            ),
            self.GOOD: CardConditionData(
                index=3,
                unicode="▰▰▱▱▱",
                star_value=33,
                weight=WeightData(
                    new_user=25,
                    normal=45,
                    premium=45
                )
            ),
            self.NEAR_MINT: CardConditionData(
                index=4,
                unicode="▰▰▰▱▱",
                star_value=72,
                weight=WeightData(
                    new_user=10,
                    normal=19,
                    premium=18.5
                )
            ),
            self.MINT: CardConditionData(
                index=5,
                unicode="▰▰▰▰▱",
                star_value=138,
                weight=WeightData(
                    new_user=3,
                    normal=5,
                    premium=5
                )
            ),
            self.PRISTINE: CardConditionData(
                index=6,
                unicode="▰▰▰▰▰",
                star_value=228,
                weight=WeightData(
                    new_user=1,
                    normal=1,
                    premium=1.5
                )
            )
        }
        return mapping[self]
    

class Texture(Enum):
    """Represents a texture image."""
    DAMAGED = "damaged"
    POOR = "poor"
    GOOD = "good"
    NEAR_MINT = "near_mint"
    MINT = "mint"
    PRISTINE = "pristine"
    SHINY = "shiny"

    def get_image_path(self) -> str:
        if self is self.MINT:
            raise ValueError("Condition 'MINT' does not have a texture.")
        
        return f"assets/condition_textures/{self.value}.png"
