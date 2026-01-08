import sys
import os
import datetime
from pathlib import Path

import discord
from discord.ext import commands, tasks

# TODO:
# - make a cfg file
#  - would have a way to config paths, as to make it cross-platform :P

intents = discord.Intents.default()
intents.message_content = True

channel = None
start_time = datetime.datetime.now()

srb2path = Path("~/.srb2").expanduser()

path = srb2path.joinpath(Path("luafiles/client/srb2-chatbot/srb2-messages.txt"))
if path.exists():
    os.remove(path)

@tasks.loop(seconds=0.5)
async def checkMessages(bot):
    global channel
        
    if not channel:
        print("uh oh!")
        return

    path = srb2path.joinpath(Path("luafiles/client/srb2-chatbot/srb2-messages.txt"))
    if path.exists():
        with open(path, "r", encoding="utf-8") as messagelist:
            msglist = messagelist.readlines()
        
        os.remove(path)

        for message in msglist:
            await channel.send(message)

plyr_count = None
@tasks.loop(seconds=0.5)
async def checkPlayerCount(bot):
    global plyr_count

    path = srb2path.joinpath(Path("luafiles/client/srb2-chatbot/player-count.txt"))
    if path.exists():
        with open(path, "r", encoding="utf-8") as pcount:
            cur_count = pcount.read().strip()
        
        os.remove(path)

        if cur_count != plyr_count:
            global start_time

            plyr_count = cur_count
            await bot.change_presence(activity=discord.Game(name=f'with {cur_count} players!', start=start_time))

class srb2Bot(commands.Bot):
    async def setup_hook(self):  # setup_hook is called before the bot starts
        checkMessages.start(self)
        checkPlayerCount.start(self)

    async def on_ready(self):
        global channel

        with open("channel.txt", "r", encoding="utf-8") as input_file:
            channelid = input_file.read().strip()
        channel = self.get_channel(int(channelid))

        if not channel:
            sys.exit()

bot = srb2Bot(command_prefix="!", intents=intents)

@checkMessages.before_loop
async def msg_check_ready():
    await bot.wait_until_ready()  # wait until the bot is ready

@checkPlayerCount.before_loop
async def count_check_ready():
    await bot.wait_until_ready()  # wait until the bot is ready

@bot.event
async def on_message(message):
    global channel

    if message.author == bot.user:
        return

    if message.channel != channel \
    or not channel:
        return

    os.makedirs(srb2path.joinpath(Path("luafiles/client/srb2-chatbot")), exist_ok=True)
    if message.content.startswith("!"):
        cmd = message.content[1:] + "\n"
        print(cmd)

        filepath = srb2path.joinpath(Path("luafiles/client/srb2-chatbot/commands.txt"))
        filepath.touch(exist_ok=True)
        with open(srb2path.joinpath("luafiles/client/srb2-chatbot/commands.txt"), "a", encoding="utf-8") as output:
            output.write(cmd)
    else:
        username = message.author.nick or message.author.global_name or message.author.name
        filepath = srb2path.joinpath(Path("luafiles/client/srb2-chatbot/discord-messages.txt"))
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
