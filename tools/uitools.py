import discord
from discord.ext import commands
from discord import app_commands


class Confirm(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label="Hyväksy", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            print(self.ctx)
            if self.ctx.user == interaction.user:
                embed = discord.Embed(title="Hyväksytty!", color=0x00FF00)
                await self.ctx.edit_original_response(
                    content="", embed=embed, view=None
                )
                self.value = True
                self.stop()
        except Exception as err:
            print(err)

    @discord.ui.button(label="Peruuta", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.user == interaction.user:
            embed = discord.Embed(title="Peruutettu.", color=0xFF0000)
            await self.ctx.edit_original_response(content="", embed=embed, view=None)
            self.value = False
            self.stop()
