from enum import Enum


__all__ = ("Fanrole",)

DEVELOPERS = {
    "ISAGLISH": 353774678826811403
}
MODS = {
    "ANGRY_RUBBER_DUCKY": 154674594874261504
}


class Fanrole(Enum):
    DEV = [user_id for user_id in DEVELOPERS.values()]
    MOD = [user_id for user_id in MODS.values()]

    @classmethod
    def get_fanrole(cls, user_id: int) -> str:
        roles = [role for role in cls]
        for role in roles:
            if user_id in role.value:
                return role.name.replace("_", " ").title()
        return "Player"
