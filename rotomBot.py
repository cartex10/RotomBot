import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

import random
import math

load_dotenv()
#TOKEN = os.getenv('DISCORD_TOKEN')		#Actual token
#TOKEN = os.getenv('TEST_TOKEN')		#Test token
#guild_id = os.getenv('GUILD_ID') #Actual server
#guild_id = os.getenv('TEST_ID') #Test server

base_activity = discord.Game(name="the ~help waiting game")

bot = commands.Bot(command_prefix="~", status="dnd", activity=base_activity)

@bot.command(help="Repeat any phrase", usage="[input]")
async def repeat(ctx, *, inp):			#test function that repeats the input
	await ctx.send(inp)

@bot.command(help="Roll a d20", usage="[n/a (for now ;) )]")
async def roll(ctx, *inp):				#d20 roll function
	roll = random.randint(1, 20)
	await ctx.send(roll)

@bot.event							
async def on_ready():					#called at bot startup
	guild = bot.get_guild(guild_id)
	chan = discord.utils.get(guild.text_channels, name="general")
	await bot.change_presence(activity=base_activity, status="dnd")
	await chan.send("ACTIVATING ROTOM BOT FOR TESTING\nHOPEFULLY THIS WORKS\nVERSION a1.1 LOADED")

@bot.command(help="View full changelog", usage=" ")		
async def changelog(ctx, *, inp):		#command to view full changelog
	chlg = "```"
	chlg += open("changelog.txt").read()
	chlg += " ```"
	await ctx.send(chlg)

bot.run(TOKEN)