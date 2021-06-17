import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from rotom_mod import *

import random
import math
import time

load_dotenv()
#TOKEN = os.getenv('DISCORD_TOKEN')			#Actual bot token
#TOKEN = os.getenv('TEST_TOKEN')			#Test bot token
#guild_id = int(os.getenv('GUILD_ID')) 		#Actual server
#guild_id = int(os.getenv('TEST_ID')) 		#Test server

#on_text = "```ACTIVATING ROTOM BOT\nVERSION 2.4.1 SUCCESSFULLY LOADED```"
#on_text = "```ACTIVATING ROTOM BOT\nTEST VERSION SUCCESSFULLY LOADED```"

base_activity = discord.Activity(type=discord.ActivityType.listening, name="!help")
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", status="online", activity=base_activity, intents=intents)

global init_list
global curr_player
global dm
global on_check
global guild
global con
on_check = False

@bot.event									#called at bot startup
async def on_ready():						
	global on_check
	global guild
	global con
	guild = bot.get_guild(guild_id)
	chan = discord.utils.get(guild.text_channels, name="general")
	await bot.change_presence(activity=base_activity, status="online")
	if on_check == False:
		on_check = True
		con = create_connection("rotom_database.db")
		await chan.send(on_text)

@bot.event									#sends introductory dm to new members
async def on_member_join(mem):				
	await mem.send(mem_join_text())

@bot.listen('on_message')					#checks for new messages in #pick-roles
async def register_reaction(message):
	# #pick-roles channel functionality
	chan = discord.utils.get(guild.text_channels, name="pick-roles")
	if message.channel == chan and not message.author.bot:
		count = 0
		content = message.content
		if not content.endswith(":"):
			thesplit = content.split(", ")
			for i in thesplit:
				tempsplit = i.split(": ")
				role = discord.utils.get(guild.roles, name=tempsplit[0])
				if type(role).__name__ == "NoneType":
					await chan.send("ERROR: Role #" + str(count+1) + " not found")
					return
				role = role.id
				tempsplit = tempsplit[1].split(":")
				reaction = discord.utils.get(guild.emojis, id=int(tempsplit[2][:-1]))
				await message.add_reaction(reaction)
				add_role_to_db(con, message.id, role, int(tempsplit[2][:-1]))
				count += 1
			await chan.send(str(count) + " new roles registered!")
	# #server-suggestions channel functionality
	chan = discord.utils.get(guild.text_channels, name="server-suggestions")
	if message.channel == chan and not message.author.bot:
		admin_mention = False
		admin_role = discord.utils.get(guild.roles, name="Admin")
		for i in message.role_mentions:
			if i == admin_role:
				admin_mention = True
				break
		if admin_mention:
			chan = discord.utils.get(guild.text_channels, name="admin-chat")
			toPrint = message.author.display_name
			if message.author.display_name != message.author.name:
				toPrint += " (" + message.author.name + ")"
			toPrint += ": " + message.content + "\n " + message.jump_url
			await chan.send(toPrint)

@bot.listen('on_raw_message_delete')			#checks for deleted messages
async def remove_reactions(payload):
	# #pick-roles channel functionality
	chan = discord.utils.get(guild.text_channels, name="pick-roles")
	if payload.channel_id == chan.id:
		count = delete_role_from_db(con, payload.message_id)
		await chan.send(str(count) + " roles removed from database!")

@bot.listen('on_raw_message_edit')			#check for editted messages
async def edit_reactions(payload):
	# #pick-roles channel functionality
	chan = discord.utils.get(guild.text_channels, name="pick-roles")
	if payload.channel_id == chan.id:
		msg = await chan.fetch_message(payload.message_id)
		await msg.clear_reactions()
		await register_reaction(msg)

@bot.listen('on_raw_reaction_add')			#checks for new reactions in #pick-roles
async def reaction_listener(payload):
	sender = discord.utils.get(guild.members, id=payload.user_id)
	# #pick-roles channel functionality
	chan = discord.utils.get(guild.text_channels, name="pick-roles")
	if payload.channel_id == chan.id and not sender.bot:
		hasRole = False
		reqRole = get_role_from_db(con, payload.message_id, payload.emoji.id)
		reqRole = discord.utils.get(guild.roles, id=reqRole)
		memRoleList = sender.roles
		for i in memRoleList:
			if i.id == reqRole.id:
				hasRole = True
				break
		if not hasRole:
			await sender.add_roles(reqRole)
			await sender.send("You now have the '" + reqRole.name + "' role! :smile:")

@bot.listen('on_raw_reaction_remove')		#checks for removal of reactions in #pick-roles
async def reaction_unlistener(payload):
	sender = discord.utils.get(guild.members, id=payload.user_id)
	# #pick-roles channel functionality
	chan = discord.utils.get(guild.text_channels, name="pick-roles")
	if payload.channel_id == chan.id and not sender.bot:
		hasRole = False
		remRole = get_role_from_db(con, payload.message_id, payload.emoji.id)
		remRole = discord.utils.get(guild.roles, id=remRole)
		memRoleList = sender.roles
		for i in memRoleList:
			if i.id == remRole.id:
				hasRole = True
				break
		if hasRole:
			await sender.remove_roles(remRole)
			await sender.send("You no longer have the '" + remRole.name + "' role! :frowning:")


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
		global con
		intcount = ddc_return(con)
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
		global con
		memRoleList = ctx.message.author.roles
		hasRole = 0
		for i in memRoleList:
			if i.name == "fellowship":
				hasRole = 1	
		if hasRole == 1:
			intcount = ddc_increment(con)
			text = "Another dimension lost...\nThat makes " + str(intcount) + " dimensions lost to darkness."
			await ctx.send(text)
		else:
			await ctx.send("Sorry, only a fellowship member can use this function")
	@ddc.command(help="Subtract from the destroyed dimension counter")
	async def sub(self, ctx):
		global con
		memRoleList = ctx.message.author.roles
		hasRole = 0
		for i in memRoleList:
			if i.name == "fellowship":
				hasRole = 1	
		if hasRole == 1:
			intcount = ddc_decrement(con)
			text = "A dimension rises from the ashes of another...\nNow, " + str(intcount) + " dimensions survive."
			await ctx.send(text)
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
	@init.command(help=init_add_help_text(), brief="Add to the initiative order", usage="[name] [initiative roll].[DEX modifier] [visible/hidden]")
	async def add(ctx, name, init_roll, secrecy="visible"):	#idk why tf this doesnt wanna take self anymore but it doesnt
		global init_list
		global dm
		if dm.name != ctx.message.author.name:
			secrecy = 0
		if type(secrecy) is str:
			if secrecy.startswith("h"):
				secrecy = 1
			elif secrecy.startswith("v"):
				secrecy = 0
		temp = Creature(name, init_roll, secrecy)
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
		global dm
		toPrint = "```DM: " + dm.display_name
		if dm.display_name != dm.name:
			toPrint += " (" + dm.name + ")"
		toPrint += "\n\n***Initiative order***\n"
		for i in init_list:
			if not i.isSecret or dm.name == ctx.message.author.name:
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
		global con
		if await bot.is_owner(ctx.message.author):
			con.close()
			await ctx.message.delete()
			await ctx.send("```ROTOM BOT SHUTTING DOWN```")
			await bot.close()


class misc(commands.Cog, name="Miscellanious"):
	def _init_(self, bot):
		self.bot = bot

	@commands.command(help="repeat any phrase")
	async def repeat(self, ctx, *, inp):
		if type(ctx.channel) != discord.DMChannel:
			await ctx.message.delete()
		await ctx.send(inp)


bot.add_cog(server())
bot.add_cog(dnd())
bot.add_cog(misc())

bot.run(TOKEN)