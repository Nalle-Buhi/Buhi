from email.mime import application
import discord
from discord.ext import commands
from discord import app_commands
import config
import os
import asyncio
import tools.dbtools as db


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="?",
            intents=discord.Intents.all(),
            application_id=config.BOT_ID,
        )

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"loaded: {filename}")
        await bot.tree.sync(guild=discord.Object(id=config.TEST_GUILD))

    async def on_ready(self):
        await db.create_tables()
        await db.startup_add_jobs()
        await db.startup_add_items()
        print("Ready")

    async def on_command_error(self, ctx: commands.Context, error):
        print(error)


bot = Bot()
# group = app_commands.Group(name="misc", description="random komentoja jotka ei liity passiin")
# bot.tree.add_command(group, guild=discord.Object(id=config.TEST_GUILD))


async def main():
    # bot.copy_global_to(guild=discord.Object(id=config.TEST_GUILD))
    await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
