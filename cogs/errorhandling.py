from discord.ext import commands
import discord
import config
from tools.embedtools import embed_builder


class Errorhandling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send(f"Nyt meni joku vituiks:\n `{error}`")
        print(error)


async def setup(bot):
    await bot.add_cog(Errorhandling(bot), guilds=[discord.Object(config.TEST_GUILD)])
