from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import discord

from .psql import *
from fancards import enums
from fancards.enums.patreon import has_minimum_patreon_role
from fancards.utils import create_progress_bar, create_interaction_embed


if TYPE_CHECKING:
    from asyncpg import Pool, Record
    from bot import Fancards

__all__ = (
    "Player",
    "Balance",
    "Level",
    "Card",
    "Inventory",
    "Config"
)


def _create_xp_bar(current_xp: int, required_xp: int) -> str:
    progress = int(current_xp / required_xp) * 100
    total = 100
    bar_length = 16
    return create_progress_bar(progress, total, bar_length)


class NotificationManager:
    """A helper class for notifications."""
    
    @staticmethod
    async def handle_level_up(
        interaction: Optional[discord.Interaction],
        previous_level: int
    ) -> None:
        """Handles the level up notification.
        
        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            The Discord interaction.
        previous_level: :class:`int`
            The previous level of the player before levelling up.
        """
        if interaction is None:
            return None
        
        bot: Fancards = interaction.client  # type: ignore
        
        guild = interaction.guild
        assert guild
        config_table = await Config(bot.pool, guild.id).get_table()

        toggle_notification_level_up = None
        if config_table is not None:
            toggle_notification_level_up = config_table.toggle_notification_level_up

        level_table = await Level(bot.pool, interaction.user.id).get_table()
        assert level_table
        current_level = level_table.current_level
        current_xp = level_table.current_xp
        required_xp = level_table.required_xp

        notify = (toggle_notification_level_up or toggle_notification_level_up is None)
        if notify:
            xp_bar = _create_xp_bar(current_xp, required_xp)
            embed = create_interaction_embed(
                interaction,
                description=f"{enums.DiscordEmoji.ICON_LEVEL_UP} {interaction.user.mention} You Leveled Up!\n\n{xp_bar}",
                title=f"Level {previous_level} -> Level {current_level}",
                footer=f"XP: {current_xp} / {required_xp}"
            )
            await interaction.followup.send(embed=embed)


class UserData:
    """Base class for tables belonging to the ``user_data`` schema.
    
    Attributes
    ----------
    pool: asyncpg.Pool[:class:`asyncpg.Record`]
        The database pool.
    discord_user_id: :class:`int`
        The ID of the user in Discord.
    """    
    def __init__(self, pool: Pool[Record], discord_user_id: int):
        self.pool = pool
        self.discord_user_id = discord_user_id


class Player(UserData):
    """A helper class for the ``user_data.user`` table."""
    def __init__(self, pool: Pool[Record], discord_user_id: int):
        super().__init__(pool, discord_user_id)
        self.base_backpack_capacity = 500
        self.max_backpack_level = 5
     
    async def register(self) -> Optional[int]:
        """Registers the player into the database with all the default values.
        
        Returns
        -------
        Optional[:class:`int`]
            The primary key ID of ``user_data.user`` table.
        """
        player_table = await self.get_table()
        if player_table is None:
            async with self.pool.acquire() as connection:
                now = discord.utils.utcnow()
                query = """
                INSERT INTO user_data.user (discord_user_id, registered_at) VALUES ($1, $2)
                RETURNING id;
                """
                fk_user_id = await connection.fetchval(query, self.discord_user_id, now)

                await connection.execute("INSERT INTO user_data.balance (fk_user_id) VALUES ($1);", fk_user_id)
                await connection.execute("INSERT INTO user_data.level (fk_user_id) VALUES ($1);", fk_user_id)
                # TODO: register rewards stuff
                # midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
                # await connection.execute("INSERT INTO user_data.rewards_daily (fk_user_id, reset_at) VALUES ($1, $2);", fk_user_id, midnight)
                # await connection.execute("INSERT INTO user_data.rewards_vote (fk_user_id) VALUES ($1);", fk_user_id)
                return fk_user_id
            
        return player_table.id
        
    async def get_table(self) -> Optional[UserTable]:
        async with self.pool.acquire() as connection:
            query = """
            SELECT * FROM user_data.user
            WHERE discord_user_id = $1;
            """
            result = await connection.fetchrow(query, self.discord_user_id)

        if result is not None:
            return UserTable(**dict(result))
    
    async def add_backpack_level(self) -> None:
        query = """
        UPDATE user_data.user
        SET backpack_level = backpack_level + 1
        WHERE discord_user_id = $1;
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query, self.discord_user_id)

    async def get_backpack_capacity(self) -> Optional[int]:
        """Returns the capacity of the player's backpack; ``None`` if the backpack is at maximum level.
        
        Raises
        ------
        ValueError
            The player is not registered.
        
        Returns
        -------
        Optional[:class:`int`]
            The capacity of the player's backpack.
        """
        player_table = await self.get_table()
        if player_table is not None:
            backpack_level = player_table.backpack_level
            return backpack_level * self.base_backpack_capacity if backpack_level < self.max_backpack_level else None
        
        raise ValueError("Player is not registered.")
    
    @property
    async def is_registered(self) -> bool:
        player_table = await self.get_table()
        return False if player_table is None else True

    @property
    def balance(self) -> Balance:
        return Balance(self.pool, self.discord_user_id)
    
    @property
    def level(self) -> Level:
        return Level(self.pool, self.discord_user_id)
    
    @property
    def inventory(self) -> Inventory:
        return Inventory(self.pool, self.discord_user_id)
    
    @property
    def collection(self) -> Card:
        return Card(self.pool, self.discord_user_id)


class Balance(UserData):
    """A helper class for the ``user_data.balance`` table."""  
    async def get_table(self) -> Optional[BalanceTable]:
        query = """
        SELECT balance.* FROM user_data.balance AS balance
        JOIN user_data.user AS player ON balance.fk_user_id = player.id
        WHERE player.discord_user_id = $1;
        """
        async with self.pool.acquire() as connection:
            result = await connection.fetchrow(query, self.discord_user_id)

        if result is None:
            return None
        
        return BalanceTable(**dict(result))
    
    async def _add_currency(self, currency: enums.Currency, amount: int) -> None:
        query = f"""
        UPDATE user_data.balance
        SET {currency.name} = {currency.name} + $1
        WHERE fk_user_id = (
            SELECT id FROM user_data.user
            WHERE discord_user_id = $2
        );
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query, amount, self.discord_user_id)
    
    async def add_silver(self, amount: int) -> None:
        await self._add_currency(enums.Currency.SILVER, amount)
    
    async def add_star(self, amount: int) -> None:
        await self._add_currency(enums.Currency.STAR, amount)
    
    async def add_gem(self, amount: int) -> None:
        await self._add_currency(enums.Currency.GEM, amount)

    async def add_voucher(self, amount: int) -> None:
        await self._add_currency(enums.Currency.VOUCHER, amount)

    async def remove_silver(self, amount: int) -> None:
        await self.add_silver(-amount)
    
    async def remove_star(self, amount: int) -> None:
        await self.add_star(-amount)
    
    async def remove_gem(self, amount: int) -> None:
        await self.add_gem(-amount)

    async def remove_voucher(self, amount: int) -> None:
        await self.add_voucher(-amount)


class Level(UserData):
    """A helper class for the ``user_data.level`` table."""  
    def __init__(self, pool: Pool[Record], discord_user_id: int):
        super().__init__(pool, discord_user_id)
        self.max_level = 100

    async def get_table(self) -> Optional[LevelTable]:
        query = """
        SELECT level.* FROM user_data.level AS level
        JOIN user_data.user AS player ON level.fk_user_id = player.id
        WHERE player.discord_user_id = $1;
        """
        async with self.pool.acquire() as connection:
            result = await connection.fetchrow(query, self.discord_user_id)

        if result is not None:
            return LevelTable(**dict(result))

    @staticmethod
    def calculate_required_xp(current_level: int) -> int:
        if current_level < 16:
            required_xp = (current_level**2) + (6*7)
        elif current_level < 31:
            required_xp = int(2.5*(current_level**2) - (40.5*current_level) + 360)
        else:
            required_xp = int(4.5*(current_level**2) - (162.5*current_level) + 2220)

        return required_xp

    async def add_level(self, level: int = 1) -> None:
        level_table = await self.get_table()
        if level_table is None:
            return None
        
        current_level = level_table.current_level
        next_level = current_level + level
        if next_level > self.max_level:
            level = self.max_level - current_level
            next_level = level
        
        query = """
        UPDATE user_data.level
        SET current_level = current_level + $1,
            current_xp = 0,
            required_xp = $2
        WHERE fk_user_id = (
            SELECT id FROM user_data.user
            WHERE discord_user_id = $3
        );
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query, level, self.calculate_required_xp(next_level), self.discord_user_id)

    async def add_xp(self, xp: int, interaction: Optional[discord.Interaction] = None) -> None:
        level_table = await self.get_table()
        if level_table is None:
            return None
        
        current_level = level_table.current_level
        previous_level = current_level
        current_xp = level_table.current_xp
        required_xp = level_table.required_xp

        if interaction is not None and isinstance(interaction.user, discord.Member):
            if has_minimum_patreon_role(interaction.user, enums.PatreonRole.UNCOMMON):
                xp *= 2
        
        current_xp += xp
        while current_xp >= required_xp:
            if current_level < self.max_level:
                current_level += 1

            current_xp -= required_xp
            required_xp = self.calculate_required_xp(current_level)

            if current_level == self.max_level:
                current_xp = required_xp
                break
        
        query = """
        UPDATE user_data.level
        SET current_level = $1,
            current_xp = $2,
            required_xp = $3
        WHERE fk_user_id = (
            SELECT id FROM user_data.user
            WHERE discord_user_id = $4
        );
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query, current_level, current_xp, required_xp, self.discord_user_id)

        if previous_level != current_level:
            await NotificationManager.handle_level_up(interaction, previous_level)


class Card(UserData):
    """A helper class for the ``user_data.card`` table."""
    async def get_card(self, card_id: str) -> Optional[CardTable]:
        query = """
        SELECT * FROM user_data.card
        WHERE card_id = $1;
        """
        async with self.pool.acquire() as connection:
            result = await connection.fetchrow(query, card_id)

        if result is not None:
            return CardTable.record_to_table(result)
        
        return None
    
    async def get_cards(self) -> list[CardTable]:
        query = """
        SELECT card.* FROM user_data.card AS card
        JOIN user_data.user AS player ON card.fk_user_id = player.id
        WHERE player.discord_user_id = $1;
        """
        async with self.pool.acquire() as connection:
            results = await connection.fetch(query, self.discord_user_id)

        if results:
            return [CardTable.record_to_table(result) for result in results]
        
        return []
    
    async def get_cards_by_card_id(self, card_ids: list[str]) -> list[CardTable]:
        query = """
        SELECT * FROM user_data.card
        WHERE card_id = ANY($1::TEXT[]);
        """
        async with self.pool.acquire() as connection:
            results = await connection.fetch(query, card_ids)

        if results:
            return [CardTable.record_to_table(result) for result in results]
        
        return []
    
    async def get_most_recently_obtained_card(self) -> Optional[CardTable]:
        query = """
        SELECT card.* FROM user_data.card AS card
        JOIN user_data.user AS player ON card.fk_user_id = player.id
        WHERE player.discord_user_id = $1
        ORDER BY card.created_at DESC
        LIMIT 1;
        """
        async with self.pool.acquire() as connection:
            result = await connection.fetchrow(query, self.discord_user_id)

        if result is not None:
            return CardTable.record_to_table(result)
        
    async def get_close_matches_by_card_id(self, card_id: str) -> list[CardTable]:
        """Returns a list of cards whose card_id closely matches the given ``card_id``."""
        query = """
        SELECT * FROM user_data.card
        WHERE card_id LIKE ($1 || '%') AND fk_user_id = (
            SELECT id FROM user_data.user
            WHERE discord_user_id = $2
        );
        """
        async with self.pool.acquire() as connection:
            results = await connection.fetch(query, card_id, self.discord_user_id)

        if results:
            return [CardTable.record_to_table(result) for result in results]
        
        return []
    
    async def get_card_owner_user_id(self, card_id: str) -> Optional[int]:
        """Returns the Discord User ID of the card owner."""
        query = """
        SELECT player.discord_user_id FROM user_data.card AS card
        JOIN user_data.user AS player ON card.fk_user_id = player.id
        WHERE card.card_id = $1;
        """
        async with self.pool.acquire() as connection:
            result = await connection.fetchval(query, card_id)

        if result is not None:
            return result
        
        return None
        
    async def add_card(self, card_table: CardTable) -> None:
        query = """
        INSERT INTO user_data.card (card_id, fk_user_id, rarity, condition, character_name, created_at, is_shiny)
            VALUES ($1, $2, $3, $4, $5, $6, $7);
        """
        async with self.pool.acquire() as connection:
            await connection.execute(
                query,
                card_table.card_id,
                card_table.fk_user_id,
                str(card_table.rarity),
                str(card_table.condition),
                card_table.character_name,
                card_table.created_at,
                card_table.is_shiny
            )

    async def delete_card(self, card_id: str) -> None:
        query = """
        DELETE FROM user_data.card
        WHERE card_id = $1;
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query, card_id)

    async def delete_cards_by_card_id(self, card_ids: list[str]) -> None:
        query = """
        DELETE FROM user_data.card
        WHERE card_id = ANY($1::TEXT[]);
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query, card_ids)


class Inventory(UserData):
    """A helper class for the ``user_data.item`` table."""  
    async def get_item(self, item: enums.Item) -> Optional[ItemTable]:
        query = """
        SELECT item.* FROM user_data.item AS item
        JOIN user_data.user AS player ON item.fk_user_id = player.id
        WHERE player.discord_user_id = $1 AND item.item_name = $2;
        """
        async with self.pool.acquire() as connection:
            result = await connection.fetchrow(query, self.discord_user_id, item.display_name)

        if result is not None:
            return ItemTable.record_to_table(result)
        
    async def add_item(self, item: enums.Item, quantity: int = 1) -> None:
        query = """
        INSERT INTO user_data.item AS item (fk_user_id, item_name, item_quantity)
        VALUES ((
            SELECT id FROM user_data.user
            WHERE discord_user_id = $1
        ), $2, $3)
        ON CONFLICT (item_name, fk_user_id)
        DO UPDATE SET item_quantity = item.item_quantity + $3;
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query, self.discord_user_id, item.display_name, quantity)


class RewardsDaily(UserData):
    """A helper class for the ``user_data.rewards_daily`` table."""  
    pass


class RewardsVote(UserData):
    """A helper class for the ``user_data.rewards_vote`` table."""  
    pass


class Config:
    """A helper class for the ``guild_data.config`` table."""  
    def __init__(self, pool: Pool[Record], discord_guild_id: int):
        self.pool = pool
        self.discord_guild_id = discord_guild_id

    async def get_table(self) -> Optional[ConfigTable]:
        async with self.pool.acquire() as connection:
            query = """
            SELECT * FROM guild_data.config
            WHERE discord_guild_id = $1;
            """
            result = await connection.fetchrow(query, self.discord_guild_id)

        if result is not None:
            return ConfigTable(**dict(result))


class Blacklist:
    """A helper class for the ``bot_data.blacklist`` table."""  
    pass
