from enum import Enum
from dataclasses import dataclass

import discord


__all__ = ("PatreonRole",)


@dataclass(frozen=True)
class PatreonRoleData:
    name: str
    id: int
    tier: int


class PatreonRole(Enum):
    COMMON = PatreonRoleData(
        name="Common Patreon",
        id=1099000179723604068,
        tier=1
    )
    UNCOMMON = PatreonRoleData(
        name="Uncommon Patreon",
        id=1099008980304547962,
        tier=2
    )
    RARE = PatreonRoleData(
        name="Rare Patreon",
        id=1099009546481049600,
        tier=3
    )

    def __str__(self) -> str:
        return self.value.name
    
    @property
    def id(self) -> int:
        return self.value.id
    
    @property
    def tier(self) -> int:
        return self.value.tier

    @classmethod
    def get_role_ids(cls) -> list[int]:
        return [role.id for role in cls]
    
    
def is_patreon(member: discord.Member) -> bool:
    """Returns ``True`` if member has any Patreon roles regardless of the tier."""
    member_role_ids = [role.id for role in member.roles]
    return any([patreon_role_id in member_role_ids for patreon_role_id in PatreonRole.get_role_ids()])


def has_minimum_patreon_role(member: discord.Member, minimum_patreon_role: PatreonRole) -> bool:
    """Returns ``True`` if member has ``minimum_patreon_role`` or higher tier."""
    patreon_role_mapping = {role.id: role for role in PatreonRole}
    patreon_roles: list[PatreonRole] = []

    for role in member.roles:
        if role.id not in PatreonRole.get_role_ids():
            continue

        patreon_role = patreon_role_mapping[role.id]
        patreon_roles.append(patreon_role)
    
    return any([patreon_role.tier >= minimum_patreon_role.tier for patreon_role in patreon_roles])
