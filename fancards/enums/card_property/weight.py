from typing import Optional
from enum import Enum
from dataclasses import dataclass


__all__ = (
    "WeightData",
    "Weight"
)


@dataclass(frozen=True)
class WeightData:
    new_user: Optional[float]
    normal: Optional[float]
    premium: Optional[float]


class Weight(Enum):
    """Represents a weight used by :class:`CardRarity` and
        :class:`CardCondition` to mimic drop chances or loot distribution.
    """
    NEW_USER = 1
    NORMAL = 2
    PREMIUM = 3
