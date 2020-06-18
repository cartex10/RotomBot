import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

import random
import math

load_dotenv()
#TOKEN = os.getenv('DISCORD_TOKEN')		#Actual bot token
#TOKEN = os.getenv('TEST_TOKEN')		#Test bot token
#guild_id = os.getenv('GUILD_ID') #Actual server
#guild_id = os.getenv('TEST_ID') #Test server

locked_roles = ["Admin", "fellowship", "dragonforce", "Groovy", "RotomBot", "@everyone"]
#locked_roles = ["CANNOT_ADD", "@everyone"]
base_activity = discord.Game(name="the ~help waiting game")

bot = commands.Bot(command_prefix="~", status="online", activity=base_activity)

@bot.command(help="Repeat any phrase", usage="[input]")
async def repeat(ctx, *, inp):			#test function that repeats the input
	await ctx.message.delete()
	await ctx.send(inp)

@bot.command(help="Roll a d20", usage="d[die size]")
async def roll(ctx, *, inp):			#die roll function
	if inp == None:
		roll = random.randint(1, 20)
	else:
		roll = random.randint(1, int(inp[1:]))
	await ctx.send(ctx.message.author.display_name + " - " + str(roll))

@bot.event							
async def on_ready():					#called at bot startup
	guild = bot.get_guild(guild_id)
	chan = discord.utils.get(guild.text_channels, name="general")
	await bot.change_presence(activity=base_activity, status="online")
	await chan.send("ACTIVATING ROTOM BOT\nVERSION 1.0 SUCCESSFULLY LOADED\n")

@bot.command(help="Shows either full or most recent update changelog", usage="[current or full]")		
async def changelog(ctx, *inp):			#command to view changelog
	if inp[0] == "full":
		chlg = "```"
		chlg += open("changelog.txt").read()
		chlg += " ```"
		await ctx.send(chlg)
	elif inp[0] == "current":
		chlg = "```"
		with open("changelog.txt", 'r') as file:
			line = file.readline()
			while line != "***CURRENT VERSION***\n":
				line = file.readline()
			
			while line != "":
				line = file.readline()
				chlg += line
		chlg += "```"
		await ctx.send(chlg)

@bot.command(help="Shows all non-locked roles", usage= "")
async def roles(ctx, *inp):				#command to show all requestable roles
	guild = bot.get_guild(guild_id)
	rolelist = guild.roles
	toPrint = "```***Requestable roles***\n\n"
	
	for i in locked_roles:
		for j in rolelist:
			if i == j.name:
				rolelist.remove(j)

	for i in rolelist:
		toPrint += i.name
		toPrint += "\n"

	toPrint += "```"
	await ctx.send(toPrint)

@bot.command(help="Request a role (use ~roles first!)", usage="[role]")
async def reqrole(ctx, *, inp):			#command to request a role
	guild = bot.get_guild(guild_id)
	rolelist = guild.roles
	memRoleList = ctx.message.author.roles

	isActualRole = 0
	isLockedRole = 0
	hasRole = 0
	reqRole = discord.Role

	for i in locked_roles:
		if i == inp:
			isLockedRole = 1

	for i in memRoleList:
		if i.name == inp:
			hasRole = 1

	for i in rolelist:
		if i.name == inp:
			isActualRole = 1
			reqRole = i

	if isActualRole != 1:
		await ctx.send("Role not recognized")
	elif hasRole:
		await ctx.send("You already have this role")
	elif isLockedRole:
		await ctx.send("You must ask an admin if you want this role")
	else:
		await ctx.message.author.add_roles(reqRole)
		await ctx.send("One role coming right up!")

@bot.event
async def on_member_join(mem):			#sends introductory dm to new members
	msg = "Hello! Welcome to our lovely server! We hope you enjoy your time here. :smile: \n"
	msg += "Before you do anything, I recommend you mute `#music-control` so you're not bombarded by music notifications."
	msg += "To do this, just click the bell at the top of the window while looking at `#music-control`.\n\n"
	msg += "Also, a bunch of channels are currently hidden behind some roles."
	msg += "This is so that your not bombarded by notifications for games you don't care about."
	msg += "If there are games/hidden channels you want to be a part of, type `~roles` to view all of the roles you can request, "
	msg += "then type `~reqrole [role]` to recieve that role.\n\n"
	msg += "I know that's a lot of information, but you only have to worry about this once.\n"
	msg += "Anyhow, that's all I have to say, so I'll leave you off here!\n"
	msg += "Remember to type `~help` in any channel in the server if you want to know what I can do!"
	await mem.send(msg)

@bot.command(help="Destroyed dimension counter (for fellowship members only)", usage="[add, sub]")
async def ddc(ctx, *, inp):				#destroyed dimension counter
	intcount = int(open("ddc.txt").read())
	memRoleList = ctx.message.author.roles
	hasRole = 0

	for i in memRoleList:
		if i.name == "fellowship":
			hasRole = 1

	if hasRole == 1:
		if inp == "add":
			intcount += 1
			file = open("ddc.txt", "w")
			file.write(str(intcount))
			text = "Another dimension lost...\nThat makes " + str(intcount) + " dimensions lost to darkness."
			await ctx.send(text)
			file.close()

		elif inp == "sub":
			intcount -= 1
			file = open("ddc.txt", "w")
			file.write(str(intcount))
			text = "A dimension rises from the ashes of another...\nNow, " + str(intcount) + " dimensions survive."
			await ctx.send(text)
			file.close()

		elif inp == "view":
			text = "Many dimensions have been lost...\nSo far, " + str(intcount) + " to be exact."
			await ctx.send(text)
		else:
			await ctx.send("Command not recognized")
	else:
		await ctx.send("Sorry, only a fellowship member can use this function")

bot.run(TOKEN)