# TO DO: fix calling init functions but dm is not defined
#		 error handling on !inventory party for invalid names, return similar parties in db?
#		 have create_connection create tables if they don't exist
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from rotom_mod import *

import random
import math
import datetime

print("Starting bot with discord.py v" + discord.__version__)
load_dotenv()
TOKEN = os.getenv('TOKEN')				#Bot token
guild_id = int(os.getenv('GUILD')) 		#Guild ID

on_text = "```ACTIVATING ROTOM BOT\nVERSION 3.1 SUCCESSFULLY LOADED```"
#on_text = "```ACTIVATING ROTOM BOT\nTEST VERSION SUCCESSFULLY LOADED```"

base_activity = discord.Activity(type=discord.ActivityType.listening, name="your commands!")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", status="online", activity=base_activity, intents=intents)

global on_check
global init_list
global curr_player
global dm
global guild
global con
on_check = False
#
#	Events and Listeners
#
@bot.event									#called at bot startup
async def on_ready():
	global on_check
	global guild
	global con
	guild = bot.get_guild(guild_id)
	chan = discord.utils.get(guild.text_channels, name="general")
	await bot.change_presence(activity=base_activity, status="online")
	if not on_check:
		on_check = True
		con = create_connection("rotom_database.db")
		await bot.tree.sync()
		#await chan.send(on_text)

@bot.event									#sends introductory dm to new members
async def on_member_join(mem):				
	await mem.send(mem_join_text())

@bot.listen('on_message')					#checks for new messages in #pick-roles
async def register_reaction(message):
	global con
	global guild
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
	# #sick channel functionality
	chan = discord.utils.get(guild.text_channels, name="sick")
	if message.channel == chan and not message.author.bot:
		role = discord.utils.get(guild.roles, name="SICK")
		#await chan.send(message.attachments[0].url)
		if get_SICK_num(con) == 0 and role in message.role_mentions:
			if check_entry(con, message.author.id):
				add_entry(con, message.author.id, message.id)
			else:
				text = "You have already submitted an entry this SICK, only the newest entry will be considered,"
				text += "please delete the previous entry if you haven't already so it doesn't get voted"
				await message.author.send(text)
				update_entry(con, message.author.id, message.id)

@bot.listen('on_raw_message_delete')		#checks for deleted messages
async def remove_reactions(payload):
	# #pick-roles channel functionality
	chan = discord.utils.get(guild.text_channels, name="pick-roles")
	if payload.channel_id == chan.id:
		count = delete_role_from_db(con, payload.message_id)
		if count > 0:
			await chan.send(str(count) + " roles removed from database!")

@bot.listen('on_raw_message_edit')			#check for editted messages
async def edit_reactions(payload):
	# #pick-roles channel functionality
	chan = discord.utils.get(guild.text_channels, name="pick-roles")
	if payload.channel_id == chan.id:
		msg = await chan.fetch_message(payload.message_id)
		await remove_reactions(payload)
		await register_reaction(msg)

@bot.listen('on_raw_reaction_add')			#checks for new reactions in #pick-roles
async def reaction_listener(payload):
	global guild
	sender = discord.utils.get(guild.members, id=payload.user_id)
	# #pick-roles channel functionality
	chan = discord.utils.get(guild.text_channels, name="pick-roles")
	if payload.channel_id == chan.id and not sender.bot:
		hasRole = False
		reqRole = get_role_from_db(con, payload.message_id, payload.emoji.id)
		reqRole = discord.utils.get(guild.roles, id=int(reqRole))
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
		remRole = discord.utils.get(guild.roles, id=int(remRole))
		memRoleList = sender.roles
		for i in memRoleList:
			if i.id == remRole.id:
				hasRole = True
				break
		if hasRole:
			await sender.remove_roles(remRole)
			await sender.send("You no longer have the '" + remRole.name + "' role! :frowning:")

#
#	DND Commands
#
# Roll Command
@bot.hybrid_command(help=roll_help_text(), brief="Roll any amount of die with an optional modifier")
async def roll(ctx, quantity=None, size=None, modifier=None):
	content = "Rolling "
	if quantity != None:
		content += quantity
		quantity = int(quantity)
	else:
		quantity = 1
	content += "d"
	if size != None:
		content += size
		size = int(size)
	else:
		content += "20"
		size = 20
	if modifier == None:
		modifier = 0
	elif modifier.startswith("-"):
		content += " - " + modifier[1:]
		modifier = int(modifier[1:]) * -1
	else:
		content += " + " + modifier
		modifier = int(modifier)
	content += "\n" + ctx.message.author.display_name + " - "
	roll = 0
	for i in range(0, quantity):
		roll += random.randint(1, size)
	content += str(roll + modifier)
	await ctx.send(content=content)

# Destroyed Dimension Counter Command
@bot.hybrid_group(help="Destroyed dimension counter (for fellowship members only)", usage="[add, sub]")
async def ddc(ctx):
	if ctx.invoked_subcommand is None:
		await ctx.send("Need further instruction. Use `!help ddc` for further help.")
@ddc.command(help="View the current destroyed dimension counter")	
async def view(ctx):
	global con
	intcount = ddc_return(con)
	memRoleList = ctx.message.author.roles
	hasRole = False
	for i in memRoleList:
		if i.name == "fellowship":
			hasRole = True
	if hasRole == True:
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
async def sub(ctx):
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

# Initiative Tracker Command
@bot.hybrid_group(help=init_help_text(), brief="Initiative tracker")
async def init(ctx):
	if ctx.invoked_subcommand is None:
		await ctx.send("Need further instruction. Use `!help init` for further help.")
@init.command(help=init_start_help_text(), brief="Initiates a new initiative")
async def start(ctx):
	global init_list
	global curr_player
	global dm
	init_list = []
	curr_player = 0
	dm = ctx.message.author
	await ctx.send("New initiative has been started.\nUse `/init add` to add players or other creatures into it")
@init.command(help=init_add_help_text(), brief="Add to the initiative order (DMs can set secrecy to `hidden` to change visibility)")
async def add(ctx, name, init_roll, secrecy="visible"):
	global init_list
	global dm
	if dm.name != ctx.message.author.name:
		secrecy = False
	if type(secrecy) is str:
		if secrecy.startswith("h"):
			secrecy = True
		elif secrecy.startswith("v"):
			secrecy = False
	temp = Creature(name, init_roll, secrecy)
	init_list.append(temp)
	init_list.sort(key=lambda varname:varname.initiative, reverse=True)
	toPrint = name + " has been added to the initiative."
	await ctx.send(toPrint)
@init.command(help="Remove from the initiative order")
async def remove(ctx, name):
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
async def view(ctx):
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
async def next(ctx):
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

# Condition Tracker Command
@bot.hybrid_group(help=condition_help_text(), brief="Condition tracker (Must be used alongside the initiative tracker)")
async def condition(ctx):
	if ctx.invoked_subcommand is None:
		await ctx.send("Need further instruction. Use `!help condition` for further help.")
@condition.command(help=condition_add_help_text(), brief="Add a condition to a creature")
async def add(ctx, name, cond, turns=-1):
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
@condition.command(help="Removes a creature's condition")
async def remove(ctx, name):
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

# Watch Keeper Command
@bot.hybrid_command(help="Sends message to help keep track of who's keeping watch")
async def keepwatch(ctx):
	text = "Night approaches...\nWho will take each watch?"
	msg = await ctx.send(text)
	nums = ["1⃣", "2⃣", "3⃣", "4⃣"]
	for i in nums:
		await msg.add_reaction(i)

# Inventory Command
@bot.hybrid_command(help="Check a party's inventory or bank. Include the name of the party to skip the selection menu")
async def inventory(ctx, party=None):
	if(party == None):
		msg = await ctx.send("```One moment please...```")
		view = InventoryView(bot, ctx, msg, con)
		await msg.edit(content=msg.content, view=view)
		await view.update()
	else:
		msg = await ctx.send("```One moment please...```")
		view = Inventory2View(bot, ctx, msg, con, party)
		await msg.edit(content=msg.content, view=view)
		await view.update()

#
#	Server Commands
#
# Changelog Command
@bot.hybrid_command(help="Prints the current version's changelog")
async def changelog(ctx):
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

# Shutdown Command
@bot.hybrid_command(hidden=True)
async def shutdown(ctx):
	global con
	if await bot.is_owner(ctx.message.author):
		con.close()
		await ctx.send("```ROTOM BOT SHUTTING DOWN```")
		await bot.close()

# Sync Command
@bot.hybrid_command(hidden=True)
async def sync(ctx):
	await bot.tree.sync()
	await ctx.send(content="Commands Synced")

# SICK Command
@bot.hybrid_command(hidden=True)
async def sick(ctx, sicknum):
	global con
	global guild
	arr = []
	if sicknum == "load":
		num = get_SICK_num(con)
		clicks = get_SICK_clicks(con)
		if num == 0:
			await ctx.send("```No SICK in database to load from```")
			return
		else:
			sicknum = int(num)
			for pair in clicks:
				arr.append(pair[0])
	elif sicknum == "log" and await bot.is_owner(ctx.message.author):
		num = get_SICK_num(con)
		clicks = get_SICK_clicks(con)
		toPrint = str(num) + " button click(s) are required\n"
		toPrint += str(len(clicks)) + " user(s) have clicked the button\n"
		if len(clicks) != 0:
			toPrint += "```USER\t\t\t\t\tDATETIME\n"
			for pair in clicks:
				username = guild.get_member(pair[0]).name
				toPrint += username + "\t\t\t" + pair[1] + "\n"
			toPrint += "```"
		await guild.owner.send(toPrint)
		return
	elif sicknum == "skip":
		await PicEnd(args={"chan":ctx.channel, "con":con})
		return
	update_SICK(con, int(sicknum))
	msg = await ctx.send(content = "Click the button below to put your vote in to start SICK!")
	view = SickView(bot, ctx, msg, int(sicknum), con, arr)
	await msg.edit(view=view)
#
#	Misc Commands
#
# Repeat Command
@bot.hybrid_command(help="repeat any phrase")
async def repeat(ctx, inp):
	await ctx.send(inp)

bot.run(TOKEN)