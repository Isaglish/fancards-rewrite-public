from __future__ import annotations

import logging
from logging import Formatter
from pathlib import Path
from typing import TypeVar, Optional, Literal
from configparser import ConfigParser

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands


OWNER_ID = 353774678826811403

Context = commands.Context["Fancards"]
Client = TypeVar("Client", bound="discord.Client")

config = ConfigParser()
config.read("config/config.ini")


class FancardsCommandTree(app_commands.CommandTree[Client]):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # TODO: check for blacklist and maintenance mode
        return True


class Fancards(commands.Bot):
    def __init__(self, command_prefix: str):
        self.command_prefix = command_prefix
        self.uptime = discord.utils.utcnow()

        self.log = logging.getLogger("discord")
        self.log.setLevel(logging.INFO)

        super().__init__(
            command_prefix=command_prefix,
            owner_id=OWNER_ID,
            activity=discord.Activity(type=discord.ActivityType.watching, name="for fishes!"),
            intents=discord.Intents.all(),
            allowed_mentions=discord.AllowedMentions.all(),
            help_command=None
        )

    async def setup_hook(self) -> None:
        cogs = [p.stem for p in Path(".").glob("./src/cogs/*.py")]
        for cog in cogs:
            await self.load_extension(f"src.cogs.{cog}")
            self.log.info(f"Extension '{cog}' has been loaded.")

        self.add_command(sync)

        await self.load_extension("jishaku")
        self.pool = await self.create_pool()

    async def on_connect(self) -> None:
        self.log.info(f"Connected to Client (version: {discord.__version__}).")

    async def on_ready(self) -> None:
        assert self.user
        self.log.info(f"Bot has connected (Guilds: {len(self.guilds)}) (Bot Username: {self.user}) (Bot ID: {self.user.id}).")
        runtime = discord.utils.utcnow() - self.uptime
        self.log.info(f"Connected after {runtime.total_seconds():.2f} seconds.")

    async def on_disconnect(self) -> None:
        self.log.critical("Bot has disconnected!")

    async def init_connection(self, connection: asyncpg.Connection[asyncpg.Record]) -> None:
        with open("fancards/database/schema.sql", "r") as file:
            query = file.read()

        await connection.execute(query)

    async def create_pool(self) -> asyncpg.Pool[asyncpg.Record]:
        dev_mode = config.getboolean("mode", "dev")
        postgres_password = config.get("database", "postgres_pwd")
        postgres_dsn = config.get("database", "postgres_dsn")

        if dev_mode:
            pool = await asyncpg.create_pool(
                host="localhost",
                port=5432,
                user="postgres",
                password=postgres_password,
                database="fancards",
                init=self.init_connection
            )
        else:
            pool = await asyncpg.create_pool(
                dsn=postgres_dsn,
                init=self.init_connection
            )

        assert pool
        return pool


@commands.is_owner()
@commands.command()
async def sync(ctx: Context, option: Optional[Literal["~", "*", "^"]] = None) -> None:
    """Syncs all app commands to the server"""
    assert ctx.guild
    match option:
        case "~":  # sync to current guild
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        case "*":  # copy from global commands and sync to guild
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        case "^":  # clear tree then sync
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        case _:  # sync globally
            synced = await ctx.bot.tree.sync()  

    await ctx.send(f"Synced {len(synced)} commands {'globally' if option is None else 'to the current guild'}.")


def main() -> None:
    dev_mode = config.getboolean("mode", "dev")
    token_discord_api = config.get("token", "discord_api")
    token_discord_api_dev = config.get("token", "discord_api_dev")
    
    bot = Fancards(
        command_prefix="devmode." if dev_mode else "fan?"
    )
    bot.run(
        token=token_discord_api_dev if dev_mode else token_discord_api,
        log_formatter=Formatter(
            fmt="[{asctime}] [{levelname:<8}] {name}: {message}",
            datefmt="%Y-%m-%d %H:%M:%S",
            style="{"
        )
    )


if __name__ == "__main__":
    main()
