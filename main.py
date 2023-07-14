import subprocess
from bs4 import Tag
import discord
import json
from discord import ActionRow, Option
from discord import Button
from discord import ButtonStyle
import random
import io
import datetime
from datetime import datetime
from datetime import timedelta
from discord.ext import commands, tasks
import asyncio
import os
import sys
import time
import requests
from flask import ctx
import sys
import string
import re
import psutil
from discord import ui
from discord.ui import Select, View, Modal, InputText
import typing
import webcolors

bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())
bot.remove_command('help')
owner_name = "cosney"
prefix = "/"

@bot.event
async def on_ready():
    print('-----------------------------')
    print(f'Connected to {len(bot.guilds)} servers')
    print('-----------------------------')
    print(f'Bot ID: {bot.user.id}')
    print('-----------------------------')
    print(f'Invite: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot')
    print('-----------------------------')
    print(f'Szef: {owner_name}')
    print('-----------------------------')
    print(f'Prefix {prefix}')
    print('-----------------------------')
    print('Bot ruszy³ aok')
    print('-----------------------------')
    while True:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                            name="Dark Gen"))
        await asyncio.sleep(3)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                            name="Start With /help command"))
        await asyncio.sleep(3)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                            name="Use /info"))
        await asyncio.sleep(3)
        if not check_stock.is_running():
                check_stock.start()

def get_channel_ty(ctx):
    config = load_config()
    channel_id = ctx.channel.id

    for channel_name, channel_data in config["channels"].items():
        if channel_id == channel_data["channel_id"]:
            return channel_name

    return None

class Feedback(Modal):
    def __init__(self, *args, bot=None, author=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.author = author

        self.add_item(InputText(label="Message Title", placeholder="Enter a title", min_length=4, max_length=50))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Feedback",
            color=0x2F3136,
            description=f"**Title:** {self.children[0].value}",
        )

        embed.set_author(name=self.author.display_name, icon_url=self.author.avatar.url)

        channel = self.bot.get_channel(1124439116231233567)
        await channel.send(embed=embed)

        await interaction.response.send_message("Thanks For ur Feedback", ephemeral=True)

@bot.slash_command()
async def feedback(ctx: discord.ApplicationContext):
    """Give us Feedback!"""
    channel_id = ctx.channel_id
    if channel_id != 1128543395300786247:
        await ctx.respond("This command can only be used in <#1128543395300786247>", ephemeral=True, delete_after=10)
        return
    modal = Feedback(title="Feedback", bot=ctx.bot, author=ctx.author)
    await ctx.send_modal(modal)

@bot.slash_command(name="performance", description="Shows the bot performance (admin only)")
async def performance(ctx):
    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="Performance", color=0x2F3136)
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%")
        embed.add_field(name="RAM Usage", value=f"{psutil.virtual_memory().percent}%")
        embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)}ms")
    await ctx.respond(embed=embed)

# @bot.slash_command(name="invites", description="Shows the invites leaderboard (working on it)")
# async def invites(ctx):
#     if ctx.author.guild_permissions.administrator:
#         embed = discord.Embed(title="Invites", color=0x2F3136)
#         invites = await ctx.guild.invites()
#         invites = sorted(invites, key=lambda x: x.uses, reverse=True)
#     for invite in invites:
#         embed.add_field(name=invite.inviter, value=f"Uses: {invite.uses}", inline=False)
#     await ctx.send(embed=embed)

class GiveawayView(discord.ui.View):
    def __init__(self, time: str, winners: int, prize: str):
        super().__init__()
        self.time = self.parse_time(time)
        self.time_str = time
        self.winners = winners
        self.prize = prize
        self.participants = []
        self.message = None
        self.join_giveaway_button = None
        self.leave_giveaway_button = None
        self.giveaway_ended = False
        self.initialize_buttons()

    def initialize_buttons(self):
        self.join_giveaway_button = discord.ui.Button(style=discord.ButtonStyle.secondary, custom_id="giveaway_join")
        self.leave_giveaway_button = discord.ui.Button(style=discord.ButtonStyle.red, custom_id="giveaway_leave", emoji="??")
        self.leave_giveaway_button.disabled = True

    async def toggle_leave_button(self, enabled: bool):
        if self.leave_giveaway_button:
            self.leave_giveaway_button.disabled = not enabled

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.giveaway_ended or (self.join_giveaway_button and interaction.user.id in self.participants):
            return False
        return True

    @discord.ui.button(label="?? Enter", style=discord.ButtonStyle.secondary, custom_id="giveaway_join")
    async def join_giveaway(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.giveaway_ended and interaction.user.id not in self.participants:
            self.participants.append(interaction.user.id)
            button.disabled = True
            user = interaction.user
            await interaction.response.send_message(content=f"{user.mention} joined the giveaway!", ephemeral=True)
            await self.update_participants_button()
            await self.update_time_field()
            self.join_giveaway_button.disabled = True
            self.leave_giveaway_button.disabled = False
        else:
            await interaction.response.send_message(content="You have already entered this giveaway!", ephemeral=True)

    async def leave_giveaway(self, interaction: discord.Interaction):
        if not self.giveaway_ended and interaction.user.id in self.participants:
            self.participants.remove(interaction.user.id)
            user = interaction.user
            await interaction.response.send_message(content=f"{user.mention} left the giveaway!", ephemeral=True)
            await self.update_participants_button()
            self.join_giveaway_button.disabled = False
            self.leave_giveaway_button.disabled = True

    async def start_giveaway(self, channel: discord.TextChannel):
        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.time)
        end_time_str = f"<t:{int(end_time.timestamp())}:R>"
        time_display = f"{end_time_str}"
        embed = discord.Embed(
            title="Giveaway",
            description=f"**Click Button to join!**\n**Time:** {time_display}\n**Hosted by:** {channel.guild.owner.mention}\n**Prize:** {self.prize}",
            color=discord.Color.from_rgb(112, 105, 109)
        )
        self.join_giveaway_button.disabled = True
        self.leave_giveaway_button.disabled = True

        self.message = await channel.send(embed=embed, view=self)

        await asyncio.sleep(self.time)

        winners = random.sample(self.participants, min(self.winners, len(self.participants)))
        random.shuffle(winners)

        winner_mentions = [channel.guild.get_member(winner).mention for winner in winners]

        embed = discord.Embed(
            title="Giveaway Ended",
            description=f"** Hosted by: {channel.guild.owner.mention} **\n ** Prize:** {self.prize} \n **Winners:** {', '.join(winner_mentions)} ",
            color=discord.Color.from_rgb(112, 105, 109)
        )
        embed.set_footer(text="Giveaway Ended")
        await self.message.edit(embed=embed)
        self.giveaway_ended = True

        self.join_giveaway_button.disabled = True
        self.leave_giveaway_button.disabled = True

    async def update_participants_button(self):
        if self.message:
            time_display = f"{self.time_str}"
            embed = self.message.embeds[0]
            participant_count = len(self.participants)
            embed.description = f"**Click Button to join!**\n**Time:** {time_display}\n**Hosted by:** {self.message.channel.guild.owner.mention}\n**Prize:** {self.prize}\n\n**Participants:** {participant_count}"
            await self.message.edit(embed=embed)

    async def update_time_field(self):
        if self.message:
            end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.time)
            end_time_str = f"<t:{int(end_time.timestamp())}:R>"
            time_display = f"{end_time_str}"
            embed = self.message.embeds[0]
            embed.description = embed.description.replace(self.time_str, time_display)
            await self.message.edit(embed=embed)

    def parse_time(self, time: str) -> int:
        match = re.match(r"^(\d+)([hmsy])$", time)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            duration = 0
            if unit == "s":
                duration = value
                self.time_str = f"{value}s"
            elif unit == "m":
                duration = value * 60
                self.time_str = f"{value}m"
            elif unit == "h":
                duration = value * 3600
                self.time_str = f"{value}h"
            elif unit == "d":
                duration = value * 86400
                self.time_str = f"{value}d"
            elif unit == "y":
                duration = value * 31536000
                self.time_str = f"{value}y"
            return duration
        return 0

@bot.slash_command(name="giveaway", description="Create a giveaway (Owner Only)")
async def giveaway(ctx, channel: discord.TextChannel, time: str, winners: int, *, prize: str):
    config = load_config()
    if ctx.author.id == config["owner_id"]:
        view = GiveawayView(time, winners, prize)
        await view.start_giveaway(channel)
    else:
        await ctx.send("You are not the owner of the bot!", hidden=True)

@bot.listen()
async def on_message(message):
    if "http" in message.content or "https" in message.content:
        await message.delete()
        await message.author.send("You can't send links here <@!" + str(message.author.id) + ">")        

@bot.slash_command(name="shop", description="Show list of products")
async def shop(ctx):
    embed = discord.Embed(
        title="Shop",
        description="> Generator\n * Premium Month - 2\n * Premium Lifetime - 5\n * Deluxe MONTH - 6\n * Deluxe LIFETIME - 10\n\n > ACCOUNTS\n * CurioSityStream - 0.25\n * Crunchyroll - 0.25\n * Paramount+ - 0.25\n * Funimation - 0.25\n * CreditCard - 0.25\n * MediaFire - 0.25\n * NordVPN - 0.25\n * Disney+ - 0.25\n * Canal+ - 0.25\n * Ubisoft - 0.25\n * Deezer - 0.25\n * Origin - 0.25\n * Gfuel - 0.25\n * Nba - 0.25\n\n> More Soon",
        color=discord.Color.from_rgb(112, 105, 109)
    )
    await ctx.author.send(embed=embed, delete_after=30)

@bot.listen()
async def on_member_update(before, after):
    if after.premium_since is not None and before.premium_since is None:
        channel = bot.get_channel(load_config()["boost"])
        await channel.send(f'Thank you for boosting {after.mention} ??')
        message = await channel.history(limit=1).flatten()[0]
        await message.add_reaction('??')

#@bot.slash_command(
    #name="feedback",
    #description="Vouch our server"
#)
#async def feedback(ctx, message: str):
    #channel_id = ctx.channel_id
    #if channel_id != 1125193017763037336:
        #await ctx.respond("This command can only be used in <#1125193017763037336>", ephemeral=True, delete_after=10)
        #return

    #user = ctx.author
    #username = user.name
    #avatar_url = str(user.avatar.url)

    #embed = discord.Embed(description=message, color=discord.Color.from_rgb(112, 105, 109))
    #embed.set_author(name=username, icon_url=avatar_url)

    #webhook_url = ''
    #data = {'embeds': [embed.to_dict()]}

    #response = requests.post(webhook_url, json=data)
    #if response.status_code == 204:
        #await ctx.respond('Thank you for vouching our server ??', ephemeral=True)
    #else:
        #await ctx.respond("There was an error while processing your feedback!", ephemeral=True)

# @bot.slash_command(name="restart", description="Restart the bot (Owner Only)")
# async def restart(ctx):
#     config = load_config()  
#     if ctx.author.id == config["owner_id"]:
#         embed = discord.Embed(
#             title="Restarting...",
#             description="> Bot is restarting",
#             color=discord.Color.from_rgb(112, 105, 109)
#         )
#         await ctx.send(embed=embed)
#         await bot.close()
#         await bot.logout()
#         subprocess.Popen(["./restart.sh"])
#         sys.exit(0)
#     else:
#         embed = discord.Embed(
#             title="Restart Error",
#             description="> You are not the owner of the bot",
#             color=discord.Color.from_rgb(112, 105, 109)
#         )
#         await ctx.send(embed=embed, delete_after=10)

def load_config():
    with open('config.json', 'r') as file:
        config = json.load(file)
        return config

@bot.slash_command(name="premium", description="Account Generator", description_localizations={"pl": "Generator kont"})
async def premium(ctx, category: Option(str, name="category", description="What account do you want to generate?", choices=list(load_config()["stock_sections"]["premium"]), required=True)):
    
    config = load_config()
    channel_type = get_channel_ty(ctx)
    if not channel_type:
        embed = discord.Embed(
            title="Account Generator Error",
            description="You cannot use this command in this channel.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, delete_after=40, ephemeral=True)
        return

    if channel_type != "premium":
        embed = discord.Embed(
            title="Account Generator Error",
            description="This command is only available for the premium category.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, delete_after=40, ephemeral=True)
        return

    channel_data = config["channels"][channel_type]

    if category not in channel_data["categories"]:
        embed = discord.Embed(
            title="Account Generator Error",
            description="You cannot use this command for this category.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, delete_after=40, ephemeral=True)
        return

    filenames = config["categories"][category]
    lines = []

    for filename in filenames:
        lines.extend(load_text(filename))

    if not lines:
        embed = discord.Embed(
            title="Account Generator Error",
            description="There are no accounts available for this category.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, delete_after=40, ephemeral=True)
        return

    random_line = random.choice(lines)

    try:
        embed_color = discord.Color.from_rgb(255, 255, 255)
        channel_text = "choices categories premium"

        embed_dm = discord.Embed(
            title="Premium Account Generated",
            description=f"> `` Account: {category} ``\n\n * This is your Premium Generated Account \n\n > `` {random_line}``",
            color=embed_color
        )

        current_time = datetime.datetime.now().strftime("%H:%M")
        embed_dm.set_footer(text=f"{current_time} | Join us at discord.gg/aha")

        await ctx.respond(embed=embed_dm, delete_after=40, ephemeral=True)

        embed_channel = discord.Embed(
            title="Thanks for using Dark Gen generator!",
            description="Here is your account generated ?",
            color=embed_color
        )
        await ctx.respond(embed=embed_channel, delete_after=40)

    except discord.Forbidden:
        embed = discord.Embed(
            title="Account Generation Error",
            description="I can't send you a private message. Check the privacy settings on the server.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, delete_after=40, ephemeral=True)

@bot.slash_command(name="free", description="Account Generator", description_localizations={"pl": "Generator kont"})
async def free(ctx, category: Option(str, name="category", description="What account do you want to generate?", choices=list(load_config()["stock_sections"]["free"]))):

    config = load_config()
    channel_type = get_channel_ty(ctx)
    if not channel_type:
        embed = discord.Embed(
            title="Account Generator Error",
            description="You cannot use this command in this channel.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, delete_after=40, ephemeral=True)
        return

    if channel_type != "free":
        embed = discord.Embed(
            title="Account Generator Error",
            description="This command is only available for the free category.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, delete_after=40, ephemeral=True)
        return

    channel_data = config["channels"][channel_type]

    if category not in channel_data["categories"]:
        embed = discord.Embed(
            title="Account Generator Error",
            description="You cannot use this command for this category.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, delete_after=40, ephemeral=True)
        return

    filenames = config["categories"][category]
    lines = []

    for filename in filenames:
        lines.extend(load_text(filename))

    if not lines:
        embed = discord.Embed(
            title="Account Generator Error",
            description="There are no accounts available for this category.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, delete_after=40, ephemeral=True)
        return

    random_line = random.choice(lines)

    try:
        embed_color = discord.Color.from_rgb(255, 255, 255)
        channel_text = "choices categories free"

        embed_dm = discord.Embed(
            title="Free Account Generated",
            description=f"> `` Account: {category} ``\n\n * This is your Free Generated Account \n\n > `` {random_line}``",
            color=embed_color
        )

        current_time = datetime.datetime.now().strftime("%H:%M")
        embed_dm.set_footer(text=f"{current_time} | Join us at discord.gg/aha")

        await ctx.respond(embed=embed_dm, delete_after=40, ephemeral=True)

        embed_channel = discord.Embed(
            title="Thanks for using Dark Gen generator!",
            description="Here is your generated account ?",
            color=embed_color
        )
        await ctx.respond(embed=embed_channel, delete_after=40)        
    except discord.Forbidden:
        embed = discord.Embed(
            title="Account Generation Error",
            description="I can't send you a private message. Check the privacy settings on the server.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, delete_after=40, ephemeral=True)

@bot.slash_command(name="format", description="Show the format of the command (Admin Only)")
async def format(ctx):
    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(
            title="Format",
            description="> <prefix> nadaj @osoba @rola \n> i czas: 1m, 1h, 1d, 1w, 1y",
            color=discord.Color.from_rgb(112, 105, 109)
        )
        await ctx.send(embed=embed, delete_after=60)

@bot.slash_command(name="gen", description="Generate a key (Admin Only)")
async def generate_key(ctx, role: discord.Role, duration: str):
    if ctx.author.guild_permissions.administrator:
        duration = duration.lower()
        duration_unit = duration[-1]
        if duration_unit.isdigit():
            duration_amount = int(duration[:-1])
        else:
            duration_amount = int(duration[:-1])

        if duration_unit == "m":
            duration_s = duration_amount * 60
        elif duration_unit == "h":
            duration_s = duration_amount * 3600
        elif duration_unit == "d":
            duration_s = duration_amount * 86400
        elif duration_unit == "w":
            duration_s = duration_amount * 604800
        elif duration_unit == "y":
            duration_s = duration_amount * 31536000
        else:
            await ctx.send("invalid format (m, h, d, w, y)", delete_after=120)
            return

        key = "DarkGen-" + ''.join(random.choices(string.digits, k=6))

        try:
            with open("roles.json", "r") as file:
                roles = json.load(file)
        except FileNotFoundError:
            roles = {}

        guild_id = str(ctx.guild.id)
        if guild_id not in roles:
            roles[guild_id] = {}

        roles[guild_id][key] = {
            "role_id": str(role.id),
            "duration": duration_s,
            "redeemed": False
        }

        with open("roles.json", "w") as file:
            json.dump(roles, file, indent=4)

        embed = discord.Embed(
            title="License Key Generated",
            description=f"The generated license key is: {key}",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)

@bot.slash_command(name="redeem", description="Redeem a license key")
async def redeem_key(ctx, key: str):
    try:
        with open("roles.json", "r") as file:
            roles = json.load(file)
    except FileNotFoundError:
        roles = {}

    guild_id = str(ctx.guild.id)

    if guild_id in roles and key in roles[guild_id]:
        if not roles[guild_id][key]["redeemed"]:
            role_id = roles[guild_id][key]["role_id"]
            duration_s = roles[guild_id][key]["duration"]

            user = ctx.author
            role = discord.utils.get(ctx.guild.roles, id=int(role_id))

            if role is not None:
                expiration_time = int(time.time()) + duration_s

                roles[guild_id][key]["redeemed"] = True
                roles[guild_id][key]["user_id"] = str(user.id)
                roles[guild_id][key]["username"] = user.name

                with open("roles.json", "w") as file:
                    json.dump(roles, file, indent=4)

                await user.add_roles(role)
                embed = discord.Embed(
                    title="License Key Redeemed",
                    description="The license key has been successfully redeemed.",
                    color=discord.Color.green()
                )
                await ctx.respond(embed=embed, ephemeral=True, delete_after=120)

                await asyncio.sleep(duration_s)
                await user.remove_roles(role)
                embed = discord.Embed(
                    title="License Key Expired",
                    description="The license has expired.",
                    color=discord.Color.red()
                )
                await ctx.author.send(embed=embed, delete_after=120)
                try:
                    with open("roles.json", "r") as file:
                        roles = json.load(file)
                except FileNotFoundError:
                    return

                if guild_id in roles and key in roles[guild_id]:
                    del roles[guild_id][key]

                    with open("roles.json", "w") as file:
                        json.dump(roles, file, indent=4)
                if guild_id in roles and key in roles[guild_id]:
                    del roles[guild_id][key]

                    with open("roles.json", "w") as file:
                        json.dump(roles, file, indent=4)
        else:
            embed = discord.Embed(
                title="Error",
                description="The key has already been redeemed.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
        return
    else:
        embed = discord.Embed(
            title="Error",
            description="The key is invalid.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
        return
    
@bot.slash_command(name="unredeem", description="Unredeem a license key (Admin Only)")
async def unredeem_key(ctx, key: str):
    if ctx.author.guild_permissions.administrator:
        try:
            with open("roles.json", "r") as file:
                roles = json.load(file)
        except FileNotFoundError:
            roles = {}

        guild_id = str(ctx.guild.id)

        if guild_id in roles and key in roles[guild_id]:
            if roles[guild_id][key]["redeemed"]:
                user_id = roles[guild_id][key]["user_id"]
                if user_id:
                    guild = ctx.guild
                    user = guild.get_member(int(user_id))
                    if user:
                        role_id = roles[guild_id][key]["role_id"]
                        role = guild.get_role(int(role_id))
                        if role:
                            await user.remove_roles(role)
                roles[guild_id][key]["redeemed"] = False
                del roles[guild_id][key]["user_id"]
                del roles[guild_id][key]["username"]

                with open("roles.json", "w") as file:
                    json.dump(roles, file, indent=4)

                embed = discord.Embed(
                    title="License Key Unredeemed",
                    description="The license key has been successfully unredeemed.",
                    color=discord.Color.green()
                )
                await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="The key has not been redeemed.",
                    color=discord.Color.red()
                )
                await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
        else:
            embed = discord.Embed(
                title="Error",
                description="The key is invalid.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
    else:
        embed = discord.Embed(
            title="Error",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)

@bot.slash_command(name="check", description="Check if a license key is valid")
async def check_key(ctx, key: str):
    try:
        with open("roles.json", "r") as file:
            roles = json.load(file)
    except FileNotFoundError:
        roles = {}

    guild_id = str(ctx.guild.id)

    if guild_id in roles and key in roles[guild_id]:
        if roles[guild_id][key]["redeemed"]:
            embed = discord.Embed(
                title="License Key Valid",
                description="The license key is valid.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
        else:
            embed = discord.Embed(
                title="Error",
                description="The key has not been redeemed.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
    else:
        embed = discord.Embed(
            title="Error",
            description="The key is invalid.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)

@bot.slash_command(name="list", description="List all license keys (Admin Only)")
async def list_keys(ctx):
    if ctx.author.guild_permissions.administrator:
        try:
            with open("roles.json", "r") as file:
                roles = json.load(file)
        except FileNotFoundError:
            roles = {}

        guild_id = str(ctx.guild.id)

        if guild_id in roles:
            embed = discord.Embed(
                title="License Keys",
                description="",
                color=discord.Color.green()
            )

            for key in roles[guild_id]:
                if roles[guild_id][key]["redeemed"]:
                    embed.description += f"{key} - Redeemed\n"
                else:
                    embed.description += f"{key} - Not Redeemed\n"

            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
        else:
            embed = discord.Embed(
                title="Error",
                description="There are no license keys.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
    else:
        embed = discord.Embed(
            title="Error",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)

@bot.slash_command(name="delete", description="Delete a license key (Admin Only)")
async def delete_key(ctx, key: str):
    if ctx.author.guild_permissions.administrator:
        try:
            with open("roles.json", "r") as file:
                roles = json.load(file)
        except FileNotFoundError:
            roles = {}

        guild_id = str(ctx.guild.id)

        if guild_id in roles and key in roles[guild_id]:
            del roles[guild_id][key]

            with open("roles.json", "w") as file:
                json.dump(roles, file, indent=4)

            embed = discord.Embed(
                title="License Key Deleted",
                description="The license key has been successfully deleted.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
        else:
            embed = discord.Embed(
                title="Error",
                description="The key is invalid.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
    else:
        embed = discord.Embed(
            title="Error",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)

def load_ticket_channel():
    try:
        with open("ticket_channels.json", "r") as file:
            data = json.load(file)
            return set(data["channels"])
    except FileNotFoundError:
        return set()

def save_ticket(channels):
    data = {"channels": list(channels)}
    with open("ticket_channels.json", "w") as file:
        json.dump(data, file)

@bot.slash_command(name="ticket", description="Open a ticket")
async def ticket(ctx):
    embed = discord.Embed(
        title="Ticket",
        description="Click the button below to open a ticket",
        color = discord.Color.from_rgb(112, 105, 109)
    )

    await ctx.respond(embed=embed, view=TicketView())

class TicketView(discord.ui.View): 
    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, emoji="??") 
    async def open_ticket(self, button, interaction):
        await interaction.response.send_message("Ticket Opened", ephemeral=True)

        guild = interaction.guild
        category_id = 1128091259609817170
        category = guild.get_channel(category_id)

        ticket_channel = await category.create_text_channel(f"ticket-{interaction.user.id}")
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)

        close_embed = discord.Embed(
            title="Ticket",
            description="Click the button below to close the ticket",
            color=discord.Color.red()
        )
        close_view = CloseTicket()
        await ticket_channel.send(embed=close_embed, view=close_view)

        ticket_channels.add(ticket_channel.id)
        save_ticket(ticket_channels)

class CloseTicket(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger)
    async def close(self, button, interaction):
        ticket_channel = interaction.channel
        await ticket_channel.delete()

ticket_channels = load_ticket_channel()

@bot.slash_command(name="close", description="Close a ticket (Admin Only)")
async def close(ctx, channel: discord.TextChannel):
    if ctx.author.guild_permissions.administrator:
        if channel.id in ticket_channels:
            await channel.delete()
            ticket_channels.remove(channel.id)
            save_ticket(ticket_channels)

            embed = discord.Embed(
                title="Ticket Closed",
                description="The ticket has been successfully closed.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
        else:
            embed = discord.Embed(
                title="Error",
                description="The channel is not a ticket.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
    else:
        embed = discord.Embed(
            title="Error",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)

@bot.slash_command(name="add", description="Add a role to a user (Admin Only)")
async def add_role(ctx, username: discord.Member, role: discord.Role):
    if ctx.author.guild_permissions.administrator:
        try:
            with open("roles.json", "r") as file:
                roles = json.load(file)
        except FileNotFoundError:
            roles = {}

        guild_id = str(ctx.guild.id)
        member_username = username.name

        if guild_id in roles:
            roles[guild_id][role.name] = {
                "username": member_username
            }
        else:
            roles[guild_id] = {
                role.name: {
                    "username": member_username
                }
            }

        with open("roles.json", "w") as file:
            json.dump(roles, file, indent=4)

        await username.add_roles(role)

        embed = discord.Embed(
            title="Role Added",
            description=f"The role {role.mention} has been successfully added to {username.mention}.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
    else:
        embed = discord.Embed(
            title="Error",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)

@bot.slash_command(name="remove", description="Remove a role from a user (Admin Only)")
async def remove_role(ctx, username: discord.Member, role: discord.Role):
    if ctx.author.guild_permissions.administrator:
        try:
            with open("roles.json", "r") as file:
                roles = json.load(file)
        except FileNotFoundError:
            roles = {}

        guild_id = str(ctx.guild.id)
        member_username = username.name

        if guild_id in roles:
            if role.name in roles[guild_id]:
                del roles[guild_id][role.name]
            else:
                embed = discord.Embed(
                    title="Error",
                    description=f"The user {username.mention} doesn't have the role {role.mention}.",
                    color=discord.Color.red()
                )
                await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
                return
        else:
            embed = discord.Embed(
                title="Error",
                description=f"The user {username.mention} doesn't have the role {role.mention}.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
            return

        with open("roles.json", "w") as file:
            json.dump(roles, file, indent=4)

        await username.remove_roles(role)

        embed = discord.Embed(
            title="Role Removed",
            description=f"The role {role.mention} has been successfully removed from {username.mention}.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
    else:
        embed = discord.Embed(
            title="Error",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)

colors = {
    "red": "#FF0000",
    "green": "#00FF00",
    "blue": "#0000FF",
    "white": "#FFFFFF",
    "black": "#000000"
}

@bot.slash_command(name="embed", description="Create Custom Embed (Admin Only)")
async def send_embed(ctx, title, description, color: str = None, channel: discord.TextChannel = None):
    if ctx.author.guild_permissions.administrator:
        color_values = []

        if color is not None:
            colors = color.split()
            for c in colors:
                if c.lower() in colors:
                    color_values.append(colors[c.lower()])
                else:
                    try:
                        color_values.append(webcolors.name_to_hex(c))
                    except ValueError:
                        embed = discord.Embed(
                            title="Error",
                            description=f"Invalid color name: {c}.",
                            color=discord.Color.red()
                        )
                        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
                        return

        if len(color_values) == 0:
            color_values.append(colors["blue"])

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color(int(color_values[0][1:], 16))
        )
        await ctx.respond("Embed sent!", ephemeral=True, delete_after=30)
        if channel is not None:
            await channel.send(embed=embed)
        else:
            await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
    else:
        embed = discord.Embed(
            title="Error",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=120)
    
@bot.slash_command(name="role_check", description="Show the role of a user (Only for Admins)")
async def role_admin(ctx, username: discord.Member):
    if not any(role.name == 'xd' for role in ctx.author.roles):
        embed = discord.Embed(
            title="Error",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=50)
        return

    try:
        with open("roles.json", "r") as file:
            roles = json.load(file)
    except FileNotFoundError:
        roles = {}

    guild_id = str(ctx.guild.id)
    member_username = username.name

    if guild_id in roles:
        for key, value in roles[guild_id].items():
            if value["username"] == member_username:
                role_id = int(value["role_id"])
                role = discord.utils.get(ctx.guild.roles, id=role_id)

                if role is not None:
                    expiration_time = value["duration"]
                    redeemed = value["redeemed"]
                    user_id = value["user_id"]

                    if redeemed:
                        embed = discord.Embed(
                            title="Role Info",
                            description=f"User: {member_username}\nRole: {role.name}\nExpiration: {expiration_time} seconds\nRedeemed by: <@{user_id}>",
                            color=discord.Color.from_rgb(112, 105, 109)
                        )
                    else:
                        embed = discord.Embed(
                            title="Role Info",
                            description=f"User: {member_username}\nRole: {role.name}\nExpiration: {expiration_time} seconds\nNot yet redeemed",
                            color=discord.Color.from_rgb(112, 105, 109)
                        )

                    await ctx.respond(embed=embed, ephemeral=True, delete_after=50)
                    return

        embed = discord.Embed(
            title="Error",
            description="The user currently doesn't have any roles.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True, delete_after=50)

@bot.slash_command(name="ban", description="Ban someone (Admins Only)")
async def ban(ctx, member: discord.Member, *, reason=None):
    if ctx.author.guild_permissions.administrator:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="Banned",
            description=f"Banned {member.mention}",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        await ctx.respond("you don't have permission to use this command", ephemeral=True)

@bot.event
async def on_guild_join(guild):
    roles = {}
    with open("roles.json", "w") as file:
        json.dump(roles, file, indent=4)

@bot.event
async def on_member_join(member):
    config = load_config()
    channel_id = config["join"]

    channel = bot.get_channel(channel_id)

    embed = discord.Embed(
        title="Welcome to the server!",
        description=f"Welcome to the server, {member.mention}! Use /help to check the commands!",
        color = discord.Color.from_rgb(112, 105, 109)
    )

    await channel.send(embed=embed)

@tasks.loop(seconds=10)
async def check_stock():
    config = load_config()
    stock_channel_id = config["stock_channel_id"]
    notification_channel_id = config["notification_channel_id"]

    await send_stock_message(stock_channel_id, notification_channel_id)

def count_lines(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        return len(lines)

def load_text(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines if line.strip()]
        return lines
    
def load_config():
    with open('config.json', 'r') as file:
        config = json.load(file)
        return config

def save_config(config):
    with open('config.json', 'w') as file:
        json.dump(config, file, indent=4)

@bot.listen()
async def on_message(message):
    if message.author.bot:
        return

    if message.content == '+rep':
        await message.add_reaction('?')
        await message.channel.send('Thanks for the feedback ?')

    await bot.process_commands(message)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    komendy = ["zjeb", "peda³", "pedal", "cwel"]
    
    if message.content.lower() in komendy:
        await message.channel.send("<@!406941383434174464>")

    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        if 'restart' in ctx.message.content:
            return
        embed = discord.Embed(
            title="Command Error",
            description="> This command does not exist check /help for all commands!",
            color=discord.Color.red()
        )
    await ctx.send(embed=embed, delete_after=50)

@bot.slash_command(name="help", description="Show all commands")
async def help(ctx):
    embed = discord.Embed(
        title="All Commands",
    )
    embed.add_field(name="```/stock```", value="> ```All available accounts```", inline=False)
    embed.add_field(name="```/info```", value="> ```Show how to use all```", inline=False)
    embed.add_field(name="```/gen```", value="> ```[SERVICE]```\n", inline=False)
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="info", description="Show Info")
async def info(ctx):

    embed = discord.Embed(
        title="GEN COMMANDS",
        description="```/gen        [SERVICE]             10 Minutes » Cooldown```\n\n"
                    "```\n"
                    "                     COMMANDS\n"
                    "```\n\n"
                    "```/stock                           All available accounts```\n\n"
                    "```/help                                     Help Command```",
    )
    embed.set_footer(text="Dark Gen" + " | " + "discord.gg/8JFK3Cmt")
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="clear", description="Clear all messages (Owner Only))")
async def clear(ctx, channel: discord.TextChannel = None):
    config = load_config()
    if ctx.author.id == config["owner_id"]:
        channel = channel or ctx.channel
        await ctx.channel.purge()
        await ctx.respond('Cleared', ephemeral=True)
        embed = discord.Embed(
            title="Clear",
            description="Cleared all messages",
            color=discord.Color.from_rgb(112, 105, 109)
        )
        print(f'{ctx.author} cleared all messages')
        await ctx.send(embed=embed, delete_after=10)

@bot.slash_command(name="stock", description="Show all accounts available")
async def stock(ctx):
    config = load_config()
    stock_embed = generate_stock_embed(config)

    stock_embed.description = f"{stock_embed.description}"
    await ctx.respond(embed=stock_embed, ephemeral=True)

def generate_stock_embed(config):
    embed = discord.Embed(
        title="Stock",
        description=f"> __***Total services:***__ ``{len(config['categories'])}``",
            color = discord.Color.from_rgb(112, 105, 109)
    )

    stock_sections = config.get("stock_sections", {})

    for section, categories in stock_sections.items():
        categories = [category.capitalize() for category in categories]

        category_counts = []

        for category in categories:
            filenames = config["categories"].get(category.lower(), [])
            count = sum(count_lines(filename) for filename in filenames)
            category_counts.append(f"> **__{category}__**: ``{count}``")

        embed.add_field(name=section.capitalize(), value="\n".join(category_counts), inline=True)
        embed.set_footer(text="Dark Gen" + " | " + "discord.gg/8JFK3Cmt")

    return embed

async def send_stock_message(stock_channel_id, notification_channel_id):
    config = load_config()
    stock_embed = generate_stock_embed(config)

    stock_channel = bot.get_channel(stock_channel_id)
    message_id = config.get("stock_message_id")

    if message_id:
        try:
            message = await stock_channel.fetch_message(message_id)
            await message.edit(embed=stock_embed)
        except discord.NotFound:
            message = await stock_channel.send(embed=stock_embed)
            config["stock_message_id"] = message.id
            save_config(config)
    else:
        message = await stock_channel.send(embed=stock_embed)
        config["stock_message_id"] = message.id
        save_config(config)

    restocked_accounts = check_restock(config)

    if restocked_accounts:
        notification_channel = bot.get_channel(notification_channel_id)

        notification_message = await notification_channel.send("@everyone")
        await notification_message.delete()

        embed = discord.Embed(
            color = discord.Color.from_rgb(112, 105, 109)
        )

    for category, filename, account_type, added_count, total_accounts in restocked_accounts:
        embed.add_field(
            name=f"Restock {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            value=f"> {category.capitalize()} Added to Stock \n > ``{added_count}`` Accounts Have been added to stock", 
            inline=False
        )

        await notification_channel.send(embed=embed)

def check_restock(config):
    restocked_accounts = []

    stock_sections = config.get("stock_sections", {})

    for section, categories in stock_sections.items():
        previous_accounts = config.get(section, {})

        for category in categories:
            filenames = config["categories"].get(category, [])

            for filename in filenames:
                total_accounts = sum(count_lines(filename) for filename in filenames)
                account_type = "Free" if "free" in category else "Premium"

                previous_count = previous_accounts.get(filename.split(".")[0], 0)
                added_count = total_accounts - previous_count

                if added_count > 0:
                    restocked_accounts.append((category.capitalize(), filename, account_type, added_count, total_accounts))
                    previous_accounts[filename.split(".")[0]] = total_accounts

            config[section] = previous_accounts

    if restocked_accounts:
        save_config(config)

    return restocked_accounts

bot.run(load_config()["token"])
