from discord.ext import commands, tasks
from discord import app_commands
import discord
from tools.embedtools import embed_builder
import config
import asyncio
import os
import tools.dbtools as db
import tools.uitools as ui
from typing import List, Literal
import datetime


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.job_service.start()

    group = app_commands.Group(name="economy", description="Kaikki economy komennot")

    @tasks.loop(hours=8)  # Change this to the desired interval
    async def job_service(self):
        for i in await db.get_jobs_and_payout():
            await db.update_balance_and_log(i[0], i[1], "paycheck", "+")
            # wallet_balance, bank_balance = await db.balance(i[0])
            # await db.update_balance(i[0], wallet_balance, (bank_balance + i[1]))
            # await db.log_transaction(i[0], i[1], "paycheck", "+")
            # print(f"User {i[0]} received {i[1]} from working ")

    @group.command()
    async def balance(self, interaction: discord.Interaction):
        """Näyttää pankkitilisi saldon"""
        wallet_balance, bank_balance = await db.balance(interaction.user.id)
        em = await embed_builder(
            interaction,
            title="Pankkitilisi saldo",
            description=" ",
            fields=[
                ["Käteinen:", f"{wallet_balance}€", True],
                ["Pankkitilin saldo:", f"{bank_balance}€", True],
            ],
            colour=discord.Colour.green(),
        )
        await interaction.response.send_message(embed=em)

    @group.command()
    async def deposit(self, interaction: discord.Interaction, amount: float):
        """Talleta käteistä rahaa pankkitilillesi"""
        try:
            await db.deposit(interaction.user.id, amount)
            wallet_balance, bank_balance = await db.balance(interaction.user.id)
            em = await embed_builder(
                interaction,
                "Saldo päivitetty",
                description="Saldosi on nyt",
                fields=[
                    ["Käteinen:", f"{wallet_balance}€", True],
                    ["Pankkitilin saldo:", f"{bank_balance}€", True],
                ],
                colour=discord.Colour.green(),
            )
            await interaction.response.send_message(embed=em)
        except ValueError as err:
            em = await embed_builder(
                interaction, str(err), description=" ", colour=discord.Colour.dark_red()
            )
            await interaction.response.send_message(embed=em)

    @group.command()
    async def withdraw(self, interaction: discord.Interaction, amount: float):
        """Nosta käteistä pankkitiltäsi"""
        try:
            await db.withdraw(interaction.user.id, amount)
            wallet_balance, bank_balance = await db.balance(interaction.user.id)
            em = await embed_builder(
                interaction,
                "Saldo päivitetty",
                description="Saldosi on nyt",
                fields=[
                    ["Käteinen:", f"{wallet_balance}€", True],
                    ["Pankkitilin saldo:", f"{bank_balance}€", True],
                ],
                colour=discord.Colour.green(),
            )
            await interaction.response.send_message(embed=em)
        except ValueError as err:
            em = await embed_builder(
                interaction, str(err), description=" ", colour=discord.Colour.dark_red()
            )
            await interaction.response.send_message(embed=em)

    @group.command()
    async def transfer(
        self, interaction: discord.Interaction, amount: float, payee: discord.User
    ):
        """Siirrä rahaa muiden käyttäjien pankkitileille"""
        try:
            await db.transfer(interaction.user.id, amount, payee.id)
            await interaction.response.send_message(
                f"Siirsit rahaa käyttäjälle {payee.display_name} {amount}€"
            )
        except Exception as err:
            await interaction.response.send_message(err)

    @group.command()
    async def transactions(
        self,
        interaction: discord.Interaction,
        type: Literal["transfer", "deposit", "withdraw", "cash", "card", "paycheck"],
    ):
        """Näyttää tilitapahtumat tyypin mukaan, jos jätät tyhjäksi näyttää komento viimeisimmät tapahtumat"""
        try:
            transactions = await db.get_transactions(interaction.user.id, type.lower())
            print(transactions)
            # Construct embed friendly list of transactions with only the necessary info
            fields = []
            for i in transactions:
                timestamp = datetime.datetime.strptime(i[5], "%Y-%m-%d %H:%M:%S.%f")
                print(timestamp)
                fields.append(
                    [
                        f"{i[0]}: {i[2]}:",
                        f"{i[3]}{i[4]}€ \n {timestamp.strftime('%d/%m/%y %H:%M')}",
                        False,
                    ]
                )
            em = await embed_builder(
                interaction,
                "Tilitapahtumat",
                description=" ",
                fields=fields,
                colour=discord.Color.green(),
            )
            await interaction.response.send_message(embed=em)
        except Exception as err:
            print

    @group.command()
    async def job(self, interaction: discord.Interaction):
        """Mene töihin!"""
        job = await db.get_user_job(interaction.user.id)
        if job[0] is not None:
            await interaction.response.send_message(
                "Sinulla on jo työpaikka! Jos kuitenkin haluat vaihtaa työpaikkaa, irtisanoudu nykyisestä työstä"
            )
        else:
            job_fields = []
            available_jobs = await db.get_available_jobs()
            job_dict = {str(i[0]): i[1] for i in available_jobs}
            for i in available_jobs:
                job_fields.append([f"id: {i[0]}: {i[1]}", i[2], False])
            em = await embed_builder(
                interaction,
                "Saatavilla olevat työt",
                "Lähetä työn id johonko haluat liittyä",
                fields=job_fields,
                colour=discord.Colour.green(),
            )
            await interaction.response.send_message(embed=em)
            chosen_job = await self.bot.wait_for(
                "message", check=lambda message: message.author == interaction.user
            )
            if chosen_job.content in job_dict:
                await db.update_user_job(interaction.user.id, int(chosen_job.content))
                await interaction.channel.send(
                    f"Tervetuloa työpaikkaan: {job_dict[chosen_job.content]}!"
                )
            else:
                await interaction.channel.send("Tuota työtä ei olemassa")

    @group.command()
    async def quit(self, interaction: discord.Interaction):
        """Lopeta nykyinen työ"""
        job = await db.get_user_job(interaction.user.id)
        if job[0] is None:
            await interaction.response.send_message(
                "Et voi ottaa lopputiliä jos et ole töissä. Mene töihin!"
            )
        else:
            view = ui.Confirm(interaction)
            await interaction.response.send_message(
                "Oletko varma että haluat irtisanoutua nykyisestä työpaikastasi?",
                view=view,
            )
            await view.wait()
            if view.value == True:
                await db.update_user_job(interaction.user.id, None)
                await interaction.channel.send("Et ole enää töissä. Mene töihin!")
            else:
                pass

    @group.command()
    async def shop(self, interaction: discord.Interaction):
        items = await db.get_available_items()
        item_fields = []
        for i in items:
            item_fields.append([f"{i[0]}: {i[1]}. ({i[2]}€)", i[3], False])
        em = await embed_builder(
            interaction,
            "Saatavilla olevat tavarat kaupassa",
            "Lähetä itemin id jota haluat ostaa",
            fields=item_fields,
            image="https://raw.githubusercontent.com/Nalle-Buhi/Buhi/main/images/shop.png",
            colour=discord.Colour.green(),
        )
        await interaction.response.send_message(embed=em)
        item_id = await self.bot.wait_for(
            "message", check=lambda message: message.author == interaction.user
        )
        await interaction.channel.send("Kuinka monta haluat ostaa?")
        quantity = await self.bot.wait_for(
            "message", check=lambda message: message.author == interaction.user
        )
        try:
            total_price, item_name = await db.shop_transaction(
                interaction.user.id, item_id.content, int(quantity.content)
            )
            await interaction.channel.send(
                f"Ostit {quantity.content} kappaletta {item_name} hintaan {total_price}€!"
            )
        except Exception as err:
            await interaction.channel.send(err)

    @group.command()
    async def inventory(self, interaction: discord.Interaction):
        inv_list = await db.get_user_inventory(interaction.user.id)
        item_fields = []
        for i in inv_list:
            item_fields.append([f"{i[1]}: {i[0]}.", f"{i[2]} Kappaletta", False])
        em = await embed_builder(
            interaction,
            "Tässä ovat tavarasi joita sinulla on inventoryssä",
            " ",
            fields=item_fields,
            colour=discord.Colour.green(),
        )
        await interaction.response.send_message(embed=em)


async def setup(bot):
    await bot.add_cog(Economy(bot), guilds=[discord.Object(config.TEST_GUILD)])
