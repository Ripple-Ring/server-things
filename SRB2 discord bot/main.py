import sys
import os
import datetime
from pathlib import Path
from modules.config import BotConfig

import discord
from discord.ext import commands, tasks

config = BotConfig(Path("config.cfg"))

if not config.srb2_path.exists():
    sys.exit("Oops! You've supplied an invalid path for SRB2!")

# TODO:
# - make a cfg file
#  - would have a way to config paths, as to make it cross-platform :P

intents = discord.Intents.default()
intents.message_content = True

channel = None
start_time = datetime.datetime.now()

srb2path = config.srb2_path

path = srb2path.joinpath(Path("luafiles/client/srb2-chatbot/srb2-messages.txt"))
if path.exists():
    os.remove(path)

@tasks.loop(seconds=0.5)
async def checkMessages(self):
    path = srb2path.joinpath(Path("luafiles/client/srb2-chatbot/srb2-messages.txt"))
    if path.exists():
        with open(path, "r", encoding="utf-8") as messagelist:
            msglist = messagelist.readlines()
        
        os.remove(path)

        for message in msglist:
            for channel in self.channelList:
                await channel.send(message)
    
"""    latestlog = srb2path.joinpath(Path("latest-log.txt"))
    if latestlog.exists() \
    and len(self.log_channelList) > 0:
        with open(latestlog, "r", encoding="utf-8") as logs:
            loglines: list = logs.readlines()
        
        start_line = self.log_startLine or 0
        for i in range(start_line, len(loglines)):
            if not loglines[i] \
            or not len(loglines[i].strip()):
                continue

            self.log_startLine = i+1
            for channel in self.log_channelList:
                await channel.send(loglines[i])"""


plyr_count = None
@tasks.loop(seconds=0.5)
async def checkPlayerCount(self):
    global plyr_count

    path = srb2path.joinpath(Path("luafiles/client/srb2-chatbot/player-count.txt"))
    if path.exists():
        with open(path, "r", encoding="utf-8") as pcount:
            cur_count = pcount.read().strip()
        
        os.remove(path)

        if cur_count != plyr_count:
            global start_time

            plyr_count = cur_count
            await self.change_presence(activity=discord.Game(name=f'with {cur_count} players!', start=start_time))

class srb2Bot(commands.Bot):
    log_startLine = 0
    channelList: list = []
    log_channelList: list = []

    async def setup_hook(self):  # setup_hook is called before the bot starts
        checkMessages.start(self)
        checkPlayerCount.start(self)

    async def on_ready(self):
        self.channelList = []
        self.log_channelList = []

        foundChannel = False
        for channelid in config.channel_ids:
            channel: discord.GuildChannel = self.get_channel(int(channelid))
            if channel:
                self.channelList.append(self.get_channel(int(channelid)))
                foundChannel = True
        
        for channelid in config.log_channel_ids:
            channel: discord.GuildChannel = self.get_channel(int(channelid))
            if channel:
                self.log_channelList.append(self.get_channel(int(channelid)))

        if not foundChannel:
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
    if message.content.startswith("!") \
    and message.author.guild_permissions.administrator:
        cmd = message.content[1:] + "\n"

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

if not config.token:
    sys.exit()

bot.run(config.token)
