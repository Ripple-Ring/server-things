
# poorly thought out code, attack !!

import sys
import shlex
import subprocess
import json
from enum import Enum
from pathlib import Path

# i love copying from stackoverflow
# https://stackoverflow.com/questions/71165431/how-do-i-make-a-working-slash-command-in-discord-py
import discord
from discord import app_commands

config_file = Path("config.cfg")
if not config_file.exists():
    print("Generating config file.")
    config_file.touch()
    with open(config_file, "w", encoding="utf-8") as cfg:
        cfg.write(json.dumps({
            "guild_id": "1234567890",
            "token": "1234567890",
            "servers": {
                "SRB2": "srb2 -dedicated",
                "SRB2: 2": "srb2 -dedicated"
            }
        }, sort_keys=True, indent=4))
    sys.exit()

with open(config_file) as cfg:
    cfg_read = cfg.read()

config = json.loads(cfg_read)

enum_list = {}
processList = {}
for name in config["servers"]:
    enum_list[name] = name # productive

Servers = Enum("Servers", enum_list)

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

GUILD_ID = int(config["guild_id"])

@tree.command(
    name="start",
    description="Starts a server.",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(server="the server you wanna start")
async def start_server(interaction: discord.Interaction, server: Servers):
    server = server.value

    if not processList.get(server):
        processList[server] = subprocess.Popen(config["servers"][server], stdin=subprocess.PIPE, shell=True)
        await interaction.response.send_message("starting server")
    else:
        await interaction.response.send_message("the server is already active")

"""
@tree.command(
    name="stop",
    description="Stops a server.",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(server="the server you wanna stop")
async def stop_server(interaction: discord.Interaction, server: Servers):
    server = server.value

    if client.processList.get(server) \
    and not client.killList.get(client.processList[server]):
        client.killList[client.processList[server]] = True
        await interaction.response.send_message("stopping server")
    else:
        await interaction.response.send_message("the server isn't active")

@tree.command(
    name="restart",
    description="Restarts a server.",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(server="the server you wanna restart")
async def restart_server(interaction: discord.Interaction, server: Servers):
    server = server

    if client.processList.get(server) \
    and not client.processList.get(server)["pls_die"]:
        client.killList[client.processList[server]] = True
        await interaction.response.send_message("stopping server")
    else:
        client.processList[server] = subprocess.Popen(shlex.split(server), stdin=subprocess.PIPE)
        await interaction.response.send_message("starting server")
    
    if not client.processList.get(server):
        client.processList[server] = subprocess.Popen(shlex.split(server), stdin=subprocess.PIPE)
        await interaction.followup.send("starting server")
"""

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("Ready!")

if not config["token"]:
    sys.exit()

client.run(config["token"])
