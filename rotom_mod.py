import aiohttp, asyncio, discord, sqlite3, datetime
from enum import Enum

class Creature:
	name = "None"
	initiative = 0.1
	hasCond = False
	condition = None
	conditionDuration = 0
	isSecret = False
	def __init__(self, arg0, arg1, arg2):
		self.name = arg0
		self.initiative = float(arg1)
		self.isSecret = bool(arg2)
	def update(self):
		if self.conditionDuration != 0:
			self.conditionDuration -= 1
		if self.conditionDuration == 0:
			self.condition = None
			self.hasCond = False
		if self.condition is not None:
			self.hasCond = True
		else:
			self.hasCond = False

##### DATA BASE FUNCTIONS #####
def create_connection(path):				#connect to database
	connection = sqlite3.connect(path)
	try:
		cursor = connection.execute("SELECT id, value, clickDate, user FROM SICK")
	except:
		cursor = connection.execute("CREATE TABLE SICK (id INTEGER PRIMARY KEY NOT NULL, value INT NOT NULL, user INT, clickDate TEXT);")
		connection.execute("INSERT INTO SICK VALUES (0, 0, NULL, NULL)")
	return connection

def ddc_return(connection):					#get ddc from database
	cursor = connection.cursor()
	for row in cursor.execute("SELECT counter FROM ddc WHERE campaign='fotgl'"):
		return row[0]

def ddc_increment(connection):				#increment ddc
	cursor = connection.cursor()
	counter = ddc_return(connection)
	cursor.execute("DELETE FROM ddc WHERE campaign='fotgl'")
	counter += 1
	cursor.execute("INSERT INTO ddc VALUES (?, ?)", ('fotgl', counter))
	connection.commit()
	return counter

def ddc_decrement(connection):				#decrement ddc
	cursor = connection.cursor()
	counter = ddc_return(connection)
	cursor.execute("DELETE FROM ddc WHERE campaign='fotgl'")
	counter -= 1
	cursor.execute("INSERT INTO ddc VALUES (?, ?)", ('fotgl', counter))
	connection.commit()
	return counter

def add_role_to_db(connection, message_id, role, emoji):		#add to database
	cursor = connection.cursor()
	cursor.execute("INSERT INTO rolereactions VALUES (?, ?, ?)", (message_id, role, emoji))
	connection.commit()

def get_role_from_db(connection, message_id, emoji):
	cursor = connection.cursor()
	cursor.execute("SELECT role FROM rolereactions WHERE message_id=? AND emoji=?", (message_id, emoji,))
	return cursor.fetchall()[0][0]

def delete_role_from_db(connection, message_id):
	cursor = connection.cursor()
	count = 0
	for i in cursor.execute("SELECT role FROM rolereactions WHERE message_id=?", (message_id,)):
		count += 1
	cursor.execute("DELETE FROM rolereactions WHERE message_id=?", (message_id,))
	connection.commit()
	return count

def add_item_to_db(connection, party, item, value=None, backpack=None):
	cursor = connection.cursor()
	cursor.execute("INSERT INTO inventories VALUES (?, ?, ?, ?)", (party, item, value, backpack))
	connection.commit()

def get_items_from_db(connection, party):
	cursor = connection.cursor()
	cursor.execute("SELECT item, value FROM inventories WHERE party=? AND item!=?", (party, "BANK"))
	return cursor.fetchall()

def get_parties_from_db(connection):
	cursor = connection.cursor()
	cursor.execute("SELECT DISTINCT party FROM inventories")
	return cursor.fetchall()

def remove_item_from_db(connection, party, item):
	cursor = connection.cursor()
	cursor.execute("DELETE FROM inventories WHERE party=? AND item=?", (party, item))
	connection.commit()

def delete_inventory(connection, party):
	cursor = connection.cursor()
	cursor.execute("DELETE FROM inventories WHERE party=?", (party,))
	connection.commit()

def get_bank_from_db(connection, party):
	cursor = connection.cursor()
	cursor.execute("SELECT value FROM inventories WHERE party=? AND item=?", (party, "BANK"))
	return cursor.fetchall()[0][0]

def set_value_from_db(connection, party, item, value):
	cursor = connection.cursor()
	cursor.execute("UPDATE inventories SET value=? WHERE party=? AND item=?", (value, party, item))
	connection.commit()

def get_SICK_num(connection):
	cursor = connection.cursor()
	cursor.execute("SELECT value FROM SICK WHERE value!=-1")
	return int(cursor.fetchall()[0][0])

def get_SICK_clicks(connection):
	cursor = connection.cursor()
	cursor.execute("SELECT user, clickDate FROM SICK WHERE value=-1")
	return (cursor.fetchall())

def update_SICK(connection, newVal):
	cursor = connection.cursor()
	cursor.execute("UPDATE SICK SET value=? WHERE value!=-1", (newVal,))
	connection.commit()

def add_click(connection, user, clickDate):
	params = (-1, user, clickDate)
	cursor = connection.cursor()
	cursor.execute("INSERT INTO SICK VALUES (NULL, ?, ?, ?)", params)
	connection.commit()

def clear_clicks(connection):
	cursor = connection.cursor()
	cursor.execute("DELETE FROM SICK WHERE value=-1")
	connection.commit()

##### VIEWS #####
class InventoryView(discord.ui.View):
	def __init__(self, bot, ctx, msg, con):
		super().__init__()
		self.timeout = 300
		self.value = None
		self.ctx = ctx
		self.msg = msg
		self.selected = 0
		self.con = con
		self.bot = bot
		self.inventories = get_parties_from_db(self.con)
	async def on_timeout(self):
		await self.msg.delete()
		self.stop()
	async def update(self, sysMsg=None):
		msg_str = "```SAVED INVENTORIES\n\n"
		for i in self.inventories:
			if self.selected == self.inventories.index(i):
				msg_str += ">>" + i[0] + "<<\n"
			else:
				msg_str += i[0] + "\n"
		msg_str += "```"
		if sysMsg != None:
			msg_str += sysMsg
		await self.msg.edit(content=msg_str)
	@discord.ui.button(label='ᐱ', style=discord.ButtonStyle.secondary)
	async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		if self.selected == 0:
			self.selected = len(self.inventories)
		self.selected -= 1
		await self.update()
	@discord.ui.button(label='Select', style=discord.ButtonStyle.green, row=0)
	async def select(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=None)
		msg = await self.ctx.send(content="One second please...")
		view = Inventory2View(self.bot, self.ctx, msg, self.con, str(self.inventories[self.selected][0]))
		await msg.edit(view=view)
		await view.update()
		await self.msg.delete()
	@discord.ui.button(label='Create New', style=discord.ButtonStyle.green, row=0)
	async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Respond with the name of the new inventory\n"
		text += "Send 'CANCEL' to create nothing"
		await self.update(text)
		def check(m):
			return m.channel == self.ctx.channel and m.author == self.ctx.author
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to create the inventory, try again")
		else:
			content = msg.content
			await msg.delete()
			if content != "CANCEL":
				add_item_to_db(self.con, msg.content, "BANK", value="0,0,0")
				self.inventories = get_parties_from_db(self.con)
				await self.update(msg.content+" created")
			else:
				await self.update("Cancelling...")
	@discord.ui.button(label='ᐯ', style=discord.ButtonStyle.secondary, row=1)
	async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		if self.selected == len(self.inventories)-1:
			self.selected = -1
		self.selected += 1
		await self.update()
	@discord.ui.button(label='Delete', style=discord.ButtonStyle.red, row=1)
	async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Are you sure you want to delete this inventory and all of its contents?\n"
		text += "Send 'YES' to delete, or anything else to cancel"
		await self.update(text)
		def check(m):
			return m.channel == self.ctx.channel and m.author == self.ctx.author
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update()
			await self.msg.edit(self.msg.content + "You ran out of time to decide, try again")
		else:
			content = msg.content
			await msg.delete()
			if content == "YES":
				toDelete = self.inventories[self.selected][0]
				delete_inventory(self.con, toDelete)
				self.inventories = get_parties_from_db(self.con)
				if self.selected == len(self.inventories):
					self.selected -= 1
				await self.update(toDelete + " deleted")
			else:
				await self.update("Cancelling...")
	@discord.ui.button(label='Exit', style=discord.ButtonStyle.red, row=1)
	async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.msg.delete()
		self.stop()

class Inventory2View(discord.ui.View):
	def __init__(self, bot, ctx, msg, con, party):
		super().__init__()
		self.timeout = 300
		self.value = None
		self.ctx = ctx
		self.msg = msg
		self.selected = 0
		self.con = con
		self.party = party
		self.bot = bot
		self.contents = get_items_from_db(self.con, self.party)
	async def on_timeout(self):
		await self.msg.delete()
		self.stop()
	async def update(self, sysMsg=None):
		msg_str = "```INVENTORY CONTENTS\n\n"
		count = 1
		for i in self.contents:
			if self.selected == self.contents.index(i):
				msg_str += str(count) + ". " + ">> " + i[0] + " <<"
			else:
				msg_str += str(count) + ". " + i[0]
			if i[1] != None:
				msg_str += " - " + i[1]
			msg_str += "\n"
			count += 1
		msg_str += "```"
		if sysMsg != None:
			msg_str += sysMsg
		await self.msg.edit(content=msg_str)
	@discord.ui.button(label='Bank', style=discord.ButtonStyle.primary, row=0)
	async def bank(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=None)
		msg = await self.ctx.send("One moment...")
		view = BankView(self.bot, self.ctx, msg, self.con, self.party)
		await msg.edit(view=view)
		await view.update()
		await self.msg.delete()
	@discord.ui.button(label='ᐱ', style=discord.ButtonStyle.secondary, row=1)
	async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
		if self.selected == 0:
			self.selected = len(self.contents)
		self.selected -= 1
		await self.update()
		await interaction.response.edit_message(view=self)
	@discord.ui.button(label='ᐯ', style=discord.ButtonStyle.secondary, row=1)
	async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
		if self.selected == len(self.contents)-1:
			self.selected = -1
		self.selected += 1
		await self.update()
		await interaction.response.edit_message(view=self)
	@discord.ui.button(label='Change Value', style=discord.ButtonStyle.green, row=1)
	async def edit_value(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Enter what you would like to set the new value of the item to\n"
		text += "Enter 'NONE' if you would like the item to have no value\n"
		text += "Enter 'CANCEL' if you would like to cancel any input"
		await self.update(text)
		def check(m):
			return m.channel == self.ctx.channel and m.author == self.ctx.author
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to set the currency, try again")
		else:
			content = msg.content
			await msg.delete()
			if content == "CANCEL":
				await self.update("Cancelling...")
			elif content == "NONE":
				item_name = self.contents[self.selected][0]
				set_value_from_db(self.con, self.party, item_name, None)
				self.contents = get_items_from_db(self.con, self.party)
				await self.update(item_name + "'s value removed")
			else:
				if not content.isnumeric():
					await self.update("ERROR: That is not a number")
				else:
					item_name = self.contents[self.selected][0]
					set_value_from_db(self.con, self.party, item_name, content)
					self.contents = get_items_from_db(self.con, self.party)
					await self.update(item_name + "'s value set to " + content)
	@discord.ui.button(label='Add Item', style=discord.ButtonStyle.green, row=1)
	async def add_item(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Respond with which item you would like to add\n"
		text += "If it has a numerical value, add a comma and a space(', ') after with only the value\n"
		text += "Send 'CANCEL' to add nothing"
		await self.update(text)
		def check(m):
			return m.channel == self.ctx.channel and m.author == self.ctx.author and m.author == self.ctx.author
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to add the item, try again")
		else:
			content = msg.content
			await msg.delete()
			if content != "CANCEL":
				splitMSG = msg.content.split(", ")
				if len(splitMSG) == 1:
					add_item_to_db(self.con, self.party, splitMSG[0])
					self.contents = get_items_from_db(self.con, self.party)
					msg_str = await self.update()
					await self.update(splitMSG[0] + " added to the inventory")
				else:
					add_item_to_db(self.con, self.party, splitMSG[0], splitMSG[1])
					self.contents = get_items_from_db(self.con, self.party)
					await self.update(splitMSG[1] + " " + splitMSG[0] + " added to the inventory")
			else:
				await self.update("Cancelling...")
	@discord.ui.button(label='ᐱ5', style=discord.ButtonStyle.secondary, row=2)
	async def upfive(self, interaction: discord.Interaction, button: discord.ui.Button):
		if self.selected <= 4:
			self.selected = 0
		else:
			self.selected -= 5
		await self.update()
		await interaction.response.edit_message(view=self)
	@discord.ui.button(label='ᐯ5', style=discord.ButtonStyle.secondary, row=2)
	async def downfive(self, interaction: discord.Interaction, button: discord.ui.Button):
		if self.selected >= len(self.contents)-6:
			self.selected = len(self.contents)-1
		else:
			self.selected += 5
		await self.update()
		await interaction.response.edit_message(view=self)
	@discord.ui.button(label='Remove', style=discord.ButtonStyle.red, row=2)
	async def delete_item(self, interaction: discord.Interaction, button: discord.ui.Button):
		remove_item_from_db(self.con, self.party, self.contents[self.selected][0])
		self.contents = get_items_from_db(self.con, self.party)
		if self.selected == 0:
			self.selected = 1
		self.selected -= 1
		await self.update()
		await interaction.response.edit_message(view=self)			
	@discord.ui.button(label='Exit', style=discord.ButtonStyle.red, row=2)
	async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.msg.delete()
		self.stop()

class BankView(discord.ui.View):
	def __init__(self, bot, ctx, msg, con, party):
		super().__init__()
		self.timeout = 300
		self.value = None
		self.ctx = ctx
		self.msg = msg
		self.selected = 0
		self.con = con
		self.party = party
		self.bot = bot
		self.vault = get_bank_from_db(self.con, self.party).split(",")
	async def on_timeout(self):
		await self.msg.delete()
		self.stop()
	async def update(self, sysMsg=None):
		msg_str = "```Bank Contents\n\n"
		temp = [" c", " s", " g"]
		count = 0
		for i in self.vault:
			msg_str += i + temp[count] + "\n"
			count += 1
		msg_str += "```"
		if sysMsg != None:
			msg_str += sysMsg
		await self.msg.edit(content=msg_str)
	@discord.ui.button(label='Add Ⓒ', style=discord.ButtonStyle.secondary, row=1)
	async def addC(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Enter what you would like to add to the Copper storage"
		await self.update(text)
		def check(m):
			return m.channel == self.ctx.channel and m.author == self.ctx.author
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to add the currency, try again")
		else:
			content = msg.content
			await msg.delete()
			if content == "CANCEL":
				await self.update("Cancelling...")
			else:
				if not content.isnumeric():
					await self.update("ERROR: That is not a number")
				else:
					temp = int(self.vault[0]) + int(content)
					self.vault[0] = str(temp)
					temp_vault = ""
					for i in self.vault:
						temp_vault += i + ","
					temp = temp_vault.rstrip(',')
					set_value_from_db(self.con, self.party, "BANK", temp)
					msg_str = await self.update(content + " Copper added to the bank")
	@discord.ui.button(label='Set Ⓒ', style=discord.ButtonStyle.secondary, row=2)
	async def setC(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Enter what you would like to set the new value of the Copper storage to"
		await self.update(text)
		def check(m):
			return m.channel == self.ctx.channel and m.author == self.ctx.author
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to set the currency, try again")
		else:
			content = msg.content
			await msg.delete()
			if content == "CANCEL":
				await self.update("Cancelling...")
			else:
				if not content.isnumeric():
					await self.update("ERROR: That is not a number")
				else:
					self.vault[0] = content
					temp_vault = ""
					for i in self.vault:
						temp_vault += i + ","
					temp = temp_vault.rstrip(',')
					set_value_from_db(self.con, self.party, "BANK", temp)
					await self.update(content + " Copper in the bank")
	@discord.ui.button(label='Add Ⓢ', style=discord.ButtonStyle.secondary, row=1)
	async def addS(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Enter what you would like to add to the Silver storage"
		await self.update(text)
		def check(m):
			return m.channel == self.ctx.channel and m.author == self.ctx.author
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to add the currency, try again")
		else:
			content = msg.content
			await msg.delete()
			if content == "CANCEL":
				await self.update("Cancelling...")
			else:
				if not content.isnumeric():
					await self.update("ERROR: That is not a number")
				else:
					temp = int(self.vault[1]) + int(content)
					self.vault[1] = str(temp)
					temp_vault = ""
					for i in self.vault:
						temp_vault += i + ","
					temp = temp_vault.rstrip(',')
					set_value_from_db(self.con, self.party, "BANK", temp)
					await self.update(content + " Silver added to the bank")
	@discord.ui.button(label='Set Ⓢ', style=discord.ButtonStyle.secondary, row=2)
	async def setS(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Enter what you would like to set the new value of the Silver storage to"
		await self.update(text)
		def check(m):
			return m.channel == self.ctx.channel and m.author == self.ctx.author
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to set the currency, try again")
		else:
			content = msg.content
			await msg.delete()
			if content == "CANCEL":
				await self.update("Cancelling...")
			else:
				if not content.isnumeric():
					await self.update("ERROR: That is not a number")
				else:
					self.vault[1] = content
					temp_vault = ""
					for i in self.vault:
						temp_vault += i + ","
					temp = temp_vault.rstrip(',')
					set_value_from_db(self.con, self.party, "BANK", temp)
					await self.update(content + " Silver in the bank")
	@discord.ui.button(label='Add Ⓖ', style=discord.ButtonStyle.secondary, row=1)
	async def addG(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Enter what you would like to add to the Gold storage"
		await self.update(text)
		def check(m):
			return m.channel == self.ctx.channel and m.author == self.ctx.author
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update()
			await self.msg.edit(self.msg.content + "You ran out of time to add the currency, try again")
		else:
			content = msg.content
			await msg.delete()
			if content == "CANCEL":
				await self.update("Cancelling...")
			else:
				if not content.isnumeric():
					await self.update("ERROR: That is not a number")
				else:
					temp = int(self.vault[2]) + int(content)
					self.vault[2] = str(temp)
					temp_vault = ""
					for i in self.vault:
						temp_vault += i + ","
					temp = temp_vault.rstrip(',')
					set_value_from_db(self.con, self.party, "BANK", temp)
					await self.update(content + " Gold added to the bank")
	@discord.ui.button(label='Set Ⓖ', style=discord.ButtonStyle.secondary, row=2)
	async def setG(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Enter what you would like to set the new value of the Gold storage to"
		await self.update(text)
		def check(m):
			return m.channel == self.ctx.channel and m.author == self.ctx.author
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to set the currency, try again")
		else:
			content = msg.content
			await msg.delete()
			if content == "CANCEL":
				await self.update("Cancelling...")
			else:
				if not content.isnumeric():
					await self.update("ERROR: That is not a number")
				else:
					self.vault[2] = content
					temp_vault = ""
					for i in self.vault:
						temp_vault += i + ","
					temp = temp_vault.rstrip(',')
					set_value_from_db(self.con, self.party, "BANK", temp)
					await self.update(" Gold in the bank")
	@discord.ui.button(label='Back', style=discord.ButtonStyle.primary, row=1)
	async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=None)
		msg = await self.ctx.send("Wait one moment...")
		view = Inventory2View(self.bot, self.ctx, msg, self.con, str(self.party))
		await msg.edit(view=view)
		await view.update()
		await self.msg.delete()
	@discord.ui.button(label='Exit', style=discord.ButtonStyle.red, row=2)
	async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.msg.delete()
		self.stop()

class SickView(discord.ui.View):
	def __init__(self, bot, ctx, msg, maxim, con, arr):
		super().__init__()
		self.timeout = 0
		self.bot = bot
		self.ctx = ctx
		self.msg = msg
		self.con = con
		self.arr = arr
		self.num = 0
		self.maxim = maxim
	@discord.ui.button(label="SICK", style=discord.ButtonStyle.green)
	async def butt(self, interaction:discord.Interaction, button:discord.ui.Button):
		inFlag = False
		for i in self.arr:
			if i == interaction.user.id:
				inFlag = True
		if not inFlag:
			self.num += 1
			if self.num == self.maxim:
				# If maximum amount of people have "voted"
				self.butt.style = discord.ButtonStyle.red
				self.butt.label = "IT'S TIME"
				text = "@everyone Calling all server members! It is time to decide on the future appearance of the server, you have one week!"
				await interaction.response.send_message(content=text, allowed_mentions=discord.AllowedMentions(everyone=True))
				clear_clicks(self.con)
				update_SICK(self.con, 0)
				self.stop()
			else:
				self.arr.append(interaction.user.id)
				text = "Thank you for participating ❤️️ \n"
				text += str(self.maxim - self.num)
				text += " people need to press the button to trigger SICK"
				await interaction.user.send(text)
				add_click(self.con, interaction.user.id, datetime.datetime.now().strftime("%m/%d/%y @ %I:%M %p"))
				update_SICK(self.con, self.maxim - self.num)
				await interaction.response.edit_message(view=self)
		else:
			text = "You have already pressed the button!\n"
			await interaction.user.send(text)
			await interaction.response.edit_message(view=self)


##### HELP TEXT #####
def mem_join_text():
	msg = "Hello! Welcome to our lovely server! We hope you enjoy your time here. :smile: \n"
	msg += "I just wanted to give you a heads up about `#pick-roles` channel, "
	msg += "where using the reactions, you can assign yourself a few roles to access different channels/pings.\n"
	msg += "One role you should grab is `InWoburn`, which we use to ping people to hang out if they're in town\n\n"
	msg += "Anyhow, there's a lot more I can do, but I don't want to bombard you with info.\n"
	msg += "Remember to use `/help` if you want to know what I can do!"
	return msg

def init_help_text():
	text = "The initiative tracker. Everytime a new one needs to be started, make sure to use `!init start`, "
	text += "but be careful since this deletes the previous one.\n"
	text += "If you want to check the current initiative being tracked, use `!init view`.\n"
	text += "To add or remove, a creature to the initiative, use `!init add` and `!init remove`.\n"
	text += "Make sure to use `!help init` on any of those if you have further questions."
	return text

def init_start_help_text():
	text = "This resets/starts the initiative tracker and needs to be run whenever a new initiative needs to be started.\n"
	text += "Be careful, this command deletes the previous initiative, so make sure no one is using it first.\n"
	return text

def init_add_help_text():
	text = "This command adds a creature to the currently tracked initiative.\n"
	text = "In order to use this command, type the name of the creature then their initiative roll.\n"
	text = "It's recommended to add the creature's DEX modifier as a decimal to the roll in case there is a tie."
	text = "If you want for this roll to stay hidden to the players, add another argument, 'hidden'"
	return text

def init_next_help_text():
	text = "Updates any condition on the creature ending their turn and continues onto the next."
	return text

def roll_help_text():
	text = "Roll a die of any size. To specify the size, type the number with or without 'd'.\n"
	text += "You can also add a modifier that is either positive or negative by specifying using '+' or '-'"
	return text

def condition_help_text():
	text = "The condition tracker. Works as a part of the initiative tracker. If no initiative is being tracked, or the creature is not in the initiative"
	text = ", then the condition tracker will not work.\n"
	text = "The amount of turns remaining on a condition are updated at the end of the creature's turn (whenever `!init next` is called).\n"
	text = "Any text can be added as a condition for any duration."
	return text

def condition_add_help_text():
	text = "Adds a condition to any creature in the initiative order.\n"
	text = "Can only store one condition currently, adding another will overwrite the other.\n"
	text = "If you want to add an initiative indefinitely, omit the [turns] part of the command.\n"
	text = "Turns decrease at the end of a creature's turn, if you want the condition to end at the start, make it last one turn less."
	return text
