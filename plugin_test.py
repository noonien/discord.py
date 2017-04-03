import os, re
import discord
import asyncio
from plugin import PluginManager
from cloudbot.event import Event, CommandEvent
from bare_loader import plugin

class DiscordWrapper():
    def __init__(self, discord_client, plugin_manager):
        self.discord_client = discord_client
        self.plugin_manager = plugin_manager

client = discord.Client()
plugin_manager = PluginManager(client)
plugin_manager.load_all(os.path.abspath("plugins"))
command_prefix = "."

dwrapper = DiscordWrapper(client, plugin_manager)

async def polling_task():
    global plugin_manager
    await client.wait_until_ready()

    channel = discord.Object(id='297483005763780613')
    while not client.is_closed:
        for name, plugin in plugin_manager.plugins.items():
            for periodic in plugin.periodic:
                event = Event(bot=dwrapper, hook=periodic)
                plugin_manager.launch(periodic, event)

        await asyncio.sleep(1)

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)
        
    tasks = []
    event = Event(bot=dwrapper)
    event.content = message.content
    event.chan = message.channel
    event.conn = client
    event.nick = message.author.mention
    client.nick = client.user.name
    
    command_re = r'(?i)^(?:[{}]|{}[,;:]+\s+)(\w+)(?:$|\s+)(.*)'.format(command_prefix, event.nick)
    cmd_match = re.match(command_re, event.content)
    if cmd_match:
        command = cmd_match.group(1).lower()
        if command in plugin_manager.commands:
            command_hook = plugin_manager.commands[command]
            command_event = CommandEvent(hook=command_hook, text=cmd_match.group(2).strip(),
                                     triggered_command=command, base_event=event)
            tasks.append(plugin_manager.launch(command_hook, command_event))
            await client.send_message(message.channel, event.reply_message)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    client.connections = {}
    client.connections[0] = client

client.loop.create_task(polling_task())

client.run('Mjk3NDgzMTk1NjI3MzM5Nzc3.C8BcvA.VBAA0nMlD3iIPQdOdtPuuMi4kv0')
