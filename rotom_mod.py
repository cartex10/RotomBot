import aiohttp, asyncio, bs4

class Creature:
	name = "None"
	initiative = 0.1
	hasCond = False
	condition = None
	conditionDuration = 0
	def __init__(self, arg0, arg1):
		self.name = arg0
		self.initiative = float(arg1)
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

def mem_join_text():
	msg = "Hello! Welcome to our lovely server! We hope you enjoy your time here. :smile: \n"
	msg += "Before you do anything, I recommend you mute `#music-control` so you're not bombarded by music notifications."
	msg += "To do this, just click the bell at the top of the window while looking at `#music-control`.\n\n"
	msg += "Also, a bunch of channels are currently hidden behind some roles."
	msg += "This is so that your not bombarded by notifications for games you don't care about."
	msg += "If there are games/hidden channels you want to be a part of, type `!role view` to view all of the roles you can request, "
	msg += "then type `!role request [role]` to recieve that role.\n\n"
	msg += "I know that's a lot of information, but you only have to worry about this once.\n"
	msg += "Anyhow, that's all I have to say, so I'll leave you off here!\n"
	msg += "Remember to type `!help` in any channel in the server if you want to know what I can do!"
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

async def opupdater():
	while True:
		async with aiohttp.ClientSession() as opsession:
 			async with opsession.get('https://www.reddit.com/r/OnePiece/') as opr:
 				res = await opr.text()
 				ingredients = res.select('._eYtD2XCVieq6emjKBH3m')
 				print(str(ingredients[0].getText()))
 				#print(goodstuff)
 				await asyncio.sleep(100000000)