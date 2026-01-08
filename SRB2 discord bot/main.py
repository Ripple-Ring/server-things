import sys
import os
from pathlib import Path

import discord
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True

channel = None

path = Path("~/.srb2/luafiles/client/srb2-chatbot/srb2-messages.txt").expanduser()
if path.exists():
    os.remove(path)

@tasks.loop(seconds=0.5)
async def checkMessages(bot):
    global channel
        
    if not channel:
        print("uh oh!")
        return

    path = Path("~/.srb2/luafiles/client/srb2-chatbot/srb2-messages.txt").expanduser()
    if path.exists():
        with open(path, "r", encoding="utf-8") as messagelist:
            msglist = messagelist.readlines()
        
        os.remove(path)

        for message in msglist:
            await channel.send(message)

class srb2Bot(commands.Bot):
    async def setup_hook(self):  # setup_hook is called before the bot starts
        checkMessages.start(self)

    async def on_ready(self):
        global channel

        with open("channel.txt", "r", encoding="utf-8") as input_file:
            channelid = input_file.read().strip()
        channel = self.get_channel(int(channelid))

        if not channel:
            sys.exit()

bot = srb2Bot(command_prefix="!", intents=intents)

@checkMessages.before_loop
async def before_my_task():
    await bot.wait_until_ready()  # wait until the bot is ready

@bot.listen('on_message')
async def handle_discordToSRB2(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        print("send to srb2 l8r")
    else:
        username = message.author.nick or message.author.global_name or message.author.name
        os.makedirs(Path("~/.srb2/luafiles/client/srb2-chatbot").expanduser(), exist_ok=True)
        
        filepath = Path("~/.srb2/luafiles/client/srb2-chatbot/discord-messages.txt").expanduser()
        filepath.touch(exist_ok=True)
        with open(filepath, "a", encoding="utf-8") as output:
            output.write("{{" + str(username) + "}} = {{" + str(message.content) + "}}\n")

"""
@bot.command()
async def read_file(ctx):
    await ctx.send("hi")
"""

with open("token.txt", "r", encoding="utf-8") as input_file:
    token = input_file.read()

bot.run(token)
