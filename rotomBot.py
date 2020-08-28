import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from rotom_mod import *

import random
import math

load_dotenv()
#TOKEN = os.getenv('DISCORD_TOKEN')		#Actual bot token
#TOKEN = os.getenv('TEST_TOKEN')		#Test bot token
#guild_id = int(os.getenv('GUILD_ID')) #Actual server
#guild_id = int(os.getenv('TEST_ID')) #Test server

#locked_roles = ["Admin", "fellowship", "dragonforce", "Groovy", "RotomBot", "@everyone", "BOTS"]
#locked_roles = ["CANNOT_ADD", "@everyone"]
base_activity = discord.Game(name="the !help waiting game")

#on_text = "```ACTIVATING ROTOM BOT\nVERSION 2.2 SUCCESSFULLY LOADED```"
#on_text = "```ACTIVATING ROTOM BOT\nTEST VERSION SUCCESSFULLY LOADED```"

bot = commands.Bot(command_prefix="!", status="online", activity=base_activity)

global init_list
global curr_player
global dm
global on_check
on_check = False
global opchapter
opchapter = "One Piece: Chapter 987"

@bot.event							
async def on_ready():					#called at bot startup
	global on_check
	global opchapter
	guild = bot.get_guild(guild_id)
	chan = discord.utils.get(guild.text_channels, name="general")
	await bot.change_presence(activity=base_activity, status="online")
	if on_check == False:
		on_check = True
		await chan.send(on_text)
		#OP Chapter notifier
		first = True
		while True:
			async with aiohttp.ClientSession() as opsession:
 				async with opsession.get('https://www.reddit.com/r/OnePiece/') as opr:
 					res = await opr.text()
 					ind = res.find('<h3 class="_eYtD2XCVieq6emjKBH3m">')
 					res = res[ind+34:ind+56]
 					if first:
 						first = False
 						opchapter = res
 					elif res != opchapter and res.startswith("One Piece: Chapter "):
 						text = "A new chapter has been released!"
 						embed = discord.Embed(title=text, description="@Nakama", color=3447003)
 						embed.add_field(name="Link", value="https://www.reddit.com/r/OnePiece/")
 						guild = bot.get_guild(guild_id)
 						chan = discord.utils.get(guild.text_channels, name="one-piece")
 						await chan.send(embed=embed)
 					await asyncio.sleep(300)

@bot.event
async def on_member_join(mem):			#sends introductory dm to new members
	await mem.send(mem_join_text())


class dnd(commands.Cog, name="DND related"):
	def _init_(self, bot):
		self.bot = bot

	@commands.command(help=roll_help_text(), brief="Roll a die with or without a modifier", usage="d[die size] +/- [modifier]")
	async def roll(self, ctx, *, inp=None):
		test = "Rolling "
		if inp == None:
			test += "d20"
			roll = random.randint(1, 20)
		else:
			if "+" in inp:
				temp = inp.split('+')
				die = temp[0].strip()
				mod = int(temp[1].strip())
				hold = " + " + str(mod)
			elif "-" in inp:
				temp = inp.split('-')
				die = temp[0].strip()
				mod = int(temp[1].strip()) * -1
				hold = " - " + str(mod * -1)
			else:
				die = inp.strip()
				mod = 0
				hold = ""
			if die.startswith('d') or die.startswith('D'):
				die = die[1:]
			test += "d" + die + hold
			die = int(die)
			roll = random.randint(1, die) + mod
		await ctx.send(test + "\n" + ctx.message.author.display_name + " - " + str(roll))

	@commands.group(help="Destroyed dimension counter (for fellowship members only)", usage="[add, sub]")
	async def ddc(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("Need further instruction. Use `!help ddc` for further help.")			
	@ddc.command(help="View the current destroyed dimension counter")
	async def view(ctx):
		intcount = int(open("ddc.txt").read())
		memRoleList = ctx.message.author.roles
		hasRole = 0
		for i in memRoleList:
			if i.name == "fellowship":
				hasRole = 1

		if hasRole == 1:
			text = "Many dimensions have been lost...\nSo far, " + str(intcount) + " to be exact."
			await ctx.send(text)
		else:
			await ctx.send("Sorry, only a fellowship member can use this function")
	@ddc.command(help="Add to the destroyed dimension counter")
	async def add(ctx):
		intcount = int(open("ddc.txt").read())
		memRoleList = ctx.message.author.roles
		hasRole = 0
		for i in memRoleList:
			if i.name == "fellowship":
				hasRole = 1	
		if hasRole == 1:
			intcount += 1
			file = open("ddc.txt", "w")
			file.write(str(intcount))
			text = "Another dimension lost...\nThat makes " + str(intcount) + " dimensions lost to darkness."
			await ctx.send(text)
			file.close()
		else:
			await ctx.send("Sorry, only a fellowship member can use this function")
	@ddc.command(help="Subtract from the destroyed dimension counter")
	async def sub(ctx):
		intcount = int(open("ddc.txt").read())
		memRoleList = ctx.message.author.roles
		hasRole = 0
		for i in memRoleList:
			if i.name == "fellowship":
				hasRole = 1	
		if hasRole == 1:
			intcount -= 1
			file = open("ddc.txt", "w")
			file.write(str(intcount))
			text = "A dimension rises from the ashes of another...\nNow, " + str(intcount) + " dimensions survive."
			await ctx.send(text)
			file.close()
		else:
			await ctx.send("Sorry, only a fellowship member can use this function")

	@commands.group(help=init_help_text(), brief="Initiative tracker", usage="[start, add, remove, view, next]")
	async def init(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("Need further instruction. Use `!help init` for further help.")
	@init.command(help=init_start_help_text(), brief="Initiates a new initiative")
	async def start(self, ctx):
		global init_list
		global curr_player
		global dm
		init_list = []
		curr_player = 0
		dm = ctx.message.author
		await ctx.send("New initiative has been started.\nUse `!init add` to add players or other creatures into it")
	@init.command(help=init_add_help_text(), brief="Add to the initiative order", usage="[name] [initiative roll].[DEX modifier]")
	async def add(ctx, name, init_roll):								#idk why tf this doesnt wanna take self anymore but it doesnt
		global init_list
		temp = Creature(name, init_roll)
		init_list.append(temp)
		init_list.sort(key=lambda varname:varname.initiative, reverse=True)
		toPrint = name + " has been added to the initiative."
		await ctx.send(toPrint)
	@init.command(help="Remove from the initiative order", usage="[name]")
	async def remove(ctx, name): #no want self
		global init_list
		canRemove = False
		index = None
		for i in init_list:
			if i.name == name and canRemove == False:
				canRemove = True
				index = init_list.index(i)
		if canRemove:
			del init_list[index]
			toPrint = "```" + name + " has been removed from the initiative.```"
		else:
			toPrint = "```" + name + " not in initiative order.```"
		await ctx.send(toPrint)
	@init.command(help="View the full initiative order")
	async def view(self, ctx):
		global init_list
		global curr_player
		toPrint = "```***Initiative order***\n"
		for i in init_list:
			if curr_player == init_list.index(i):
				toPrint += "⬐ Taking their turn\n"
			toPrint += i.name + " - " + str(i.initiative)[:-2]
			if i.hasCond:
				toPrint += " - " + i.condition.upper()
			toPrint += "\n"
			if curr_player == init_list.index(i):
				toPrint += "⬑ Taking their turn\n"
		toPrint += "```"
		await ctx.send(toPrint)
	@init.command(help=init_next_help_text(), brief="Continue the initiative order")
	async def next(self, ctx):
		global init_list
		global curr_player
		init_list[curr_player].update()
		curr_player += 1
		if curr_player >= len(init_list)-1:
			curr_player = 0
		toPrint = "```" + init_list[curr_player].name + " is now taking their turn. "
		if init_list[curr_player].hasCond:
			toPrint += init_list[curr_player].name + " is currently " + init_list[curr_player].condition + "."
		toPrint +="```"
		await ctx.send(toPrint)

	@commands.group(help=condition_help_text(), brief="Condition tracker (Must be used alongside the initiative tracker)", usage="[add, remove]")
	async def condition(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("Need further instruction. Use `!help condition` for further help.")
	@condition.command(help=condition_add_help_text(), brief="Add a condition to a creature", usage="[name] [condition] [turns]")
	async def add(self, ctx, name, cond, turns=-1):
		global init_list
		checker = False
		for i in init_list:
			if i.name == name:
				checker = True
				i.condition = cond
				i.conditionDuration = int(turns)
				i.hasCond = True
				if turns == -1:
					await ctx.send(name + " has been " + cond + " indefinitely!")
				else:
					await ctx.send(name + " has been " + cond + " for the next " + str(turns) + " turns!")
		if not checker:
			await ctx.send("Creature was not found.")
	@condition.command(help="Removes a creature's condition", usage="[name]")
	async def remove(self, ctx, name):			#also doesnt want self ig
		global init_list
		doesExist = False
		index = None
		for i in init_list:
			if i.name == name:
				doesExist = True
				index = init_list.index(i)
		if not doesExist:
			await ctx.send(name + " is not in the initiaive order.")
		elif init_list[index].hasCond == False:
			await ctx.send(name + " does not have a condition.")
		else:
			init_list[index].hasCond = False
			init_list[index].condition = None
			init_list[index].conditionDuration = 0
			await ctx.send(name + "'s condition has been removed.")

	@commands.command(help="Sends message to help keep track of who's keeping watch")
	async def keepwatch(self, ctx):
		text = "Night approaches...\nWho will take each watch?"
		msg = await ctx.send(text)
		nums = ["1⃣", "2⃣", "3⃣", "4⃣"]
		for i in nums:
			await msg.add_reaction(i)


class server(commands.Cog, name="Server/Bot Related"):
	def _init_(self, bot):
		self.bot = bot

	@commands.group(help="Role commands", usage="[view, request]")
	async def role(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("Need further instruction. Use `!help role` for further help.")
	@role.command(help="View unlocked roles")
	async def view(self, ctx):
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
	@role.command(help="Request a role")
	async def request(self, ctx, inp):
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
	@role.command(help="Remove a role from yourself")
	async def remove(self, ctx, inp):
		hasRole = False
		memRoleList = ctx.message.author.roles
		remRole = discord.Role
		for i in memRoleList:
			if i.name == inp:
				hasRole = True
				remRole = i
		if not hasRole:
			await ctx.send("You do not have the requested role.")
		else:
			await ctx.message.author.remove_roles(remRole)
			await ctx.send("Role removed. Sorry to see you go :pensive:")

	@commands.command(help="Prints the current version's changelog")
	async def changelog(self, ctx):
		chlg = "```"
		with open("changelog.txt", 'r') as file:
			line = file.readline()
			while line != "***CURRENT VERSION***\n":
				line = file.readline()
			while line != "":
				line = file.readline()
				if len(line) + len(chlg) >= 1990:
					await ctx.send(chlg + "```")
					chlg = "```" + line
				else:
					chlg += line
			await ctx.send(chlg + "```")

	@commands.command(hidden=True)
	async def shutdown(self, ctx):
		if await bot.is_owner(ctx.message.author):
			await ctx.message.delete()
			await ctx.send("```ROTOM BOT SHUTTING DOWN```")
			await bot.logout()


class misc(commands.Cog, name="Miscellanious"):
	def _init_(self, bot):
		self.bot = bot

	@commands.command(help="repeat any phrase")
	async def repeat(self, ctx, *, inp):
		await ctx.message.delete()
		await ctx.send(inp)


bot.add_cog(server())
bot.add_cog(dnd())
bot.add_cog(misc())

bot.run(TOKEN)