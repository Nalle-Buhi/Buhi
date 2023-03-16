from discord.ext import commands, tasks
from discord import app_commands
import discord
from tools.embedtools import embed_builder
import config


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.uptimeCounter.start()

        self.tsec = 0
        self.tmin = 0
        self.thour = 0
        self.tday = 0

    group = app_commands.Group(name="info", description="Kaikki info komennot")

    @tasks.loop(seconds=2.0)
    async def uptimeCounter(self):
        self.tsec += 2
        if self.tsec == 60:
            self.tsec = 0
            self.tmin += 1
            if self.tmin == 60:
                self.tmin = 0
                self.thour += 1
                if self.thour == 24:
                    self.thour = 0
                    self.tday += 1

    @uptimeCounter.before_loop
    async def beforeUptimeCounter(self):
        await self.bot.wait_until_ready()

    @group.command()
    async def uptime(self, interaction: discord.Interaction):
        """Kuinka pitkään botti on kestänyt hengissä paskomatta alleen"""
        fields = [
            ["Päivät:", self.tday, True],
            ["Tunnit:", self.thour, True],
            ["Minuutit:", self.tmin, True],
            ["Sekunnit:", self.tsec, True],
        ]
        em = await embed_builder(
            interaction,
            "Botin uptime",
            "Kuinka pitkään botti on kestänyt hengissä paskomatta alleen",
            fields=fields,
        )
        await interaction.response.send_message(embed=em)


async def setup(bot):
    await bot.add_cog(Info(bot), guilds=[discord.Object(config.TEST_GUILD)])
