import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

import random
import math

load_dotenv()
#TOKEN = os.getenv('DISCORD_TOKEN')
#guild_id = os.getenv('GUILD_ID') #Actual server
#guild_id = os.getenv('TEST_ID') #Test server

bot = commands.Bot(command_prefix="~", status="dnd")

@bot.command()
async def repeat(ctx, *, inp):		#test function that repeats the input 
	await ctx.send(inp)

@bot.command()
async def roll(ctx, *inp):			#d20 roll function
	roll = random.random() % 20 + 1
	await ctx.send(roll)

@bot.event							#called at bot startup
async def on_ready():
	guild = bot.get_guild(guild_id)
	chan = discord.utils.get(guild.text_channels, name="general")
	await chan.send("ACTIVATING ROTOM BOT FOR TESTING")
	await chan.send("HOPEFULLY THIS WORKS")
	await chan.send("VERSION a1.0 LOADED")

bot.run(TOKEN)