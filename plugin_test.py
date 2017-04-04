import os, re
import discord
import asyncio
import time
import logging
from plugin import PluginManager
from cloudbot.event import Event, CommandEvent, EventType
from bare_loader import plugin

class DiscordWrapper():
    def __init__(self, discord_client, plugin_manager):
        self.discord_client = discord_client
        self.plugin_manager = plugin_manager
        self.connections = {}
        
        self.connections[0] = self
        self.config = {}
        
        self.config["api_keys"] = {}
        self.config["api_keys"]["google_dev_key"] = "AIzaSyCVp4jFP4N3F6iHCMf-402auSA3L-x71sI"
        
        self.config["command_prefix"] = "."
        
        
        self.to_send = []
        
        self.name = "roddit"
        self.logger = logging.getLogger("cloudbot")
        
    def __getattr__(self, name):
        msg = "'{}' object has no attribute '{}'"
        raise AttributeError(msg.format(self.__class__, name))

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        
    def message(self, target, message):
        print("send (%s) %s" % (target, message))
        self.to_send.append((target, message))
    
    def notice(self, target, text):
        print("notice (%s) %s" % (target, text))
        self.to_send.append((target, text))
    
    def on_message(self, message):
        event = Event(bot=dwrapper, event_type=EventType.message)
        event.content = message.content
        event.chan = message.channel
        event.conn = self
        event.nick = message.author.name #TODO .mention on mentions
        self.nick = client.user.name
        
        # Raw IRC hook
        for raw_hook in self.plugin_manager.catch_all_triggers:
            self.plugin_manager.launch(raw_hook, Event(hook=raw_hook, base_event=event))
        if event.irc_command in self.plugin_manager.raw_triggers:
            for raw_hook in self.plugin_manager.raw_triggers[event.irc_command]:
                self.plugin_manager.launch(raw_hook, Event(hook=raw_hook, base_event=event))

        
        command_re = r'(?i)^(?:[{}]|{}[,;:]+\s+)(\w+)(?:$|\s+)(.*)'.format(command_prefix, event.nick)
        cmd_match = re.match(command_re, event.content)
        if cmd_match:
            command = cmd_match.group(1).lower()
            if command in self.plugin_manager.commands:
                command_hook = self.plugin_manager.commands[command]
                command_event = CommandEvent(hook=command_hook, text=cmd_match.group(2).strip(),
                                         triggered_command=command, base_event=event)
                
                self.plugin_manager.launch(command_hook, command_event)
                
    def on_periodic(self):
        for name, plugin in self.plugin_manager.plugins.items():
            for periodic in plugin.periodic:
                if time.time() - periodic.last_time > periodic.interval:
                    periodic.last_time = time.time()
                    event = Event(bot=dwrapper, hook=periodic)
                    self.plugin_manager.launch(periodic, event)

client = discord.Client()
dwrapper = DiscordWrapper(client, None)
plugin_manager = PluginManager(dwrapper)
plugin_manager.load_all(os.path.abspath("plugins"))

dwrapper.plugin_manager = plugin_manager
command_prefix = "."

async def polling_task():
    global plugin_manager
    await client.wait_until_ready()

    channel = discord.Object(id='297483005763780613')
    while not client.is_closed:
        dwrapper.on_periodic()
        
        while len(dwrapper.to_send) > 0:
            elem = dwrapper.to_send.pop()
            await client.send_message(channel, elem[1])

        await asyncio.sleep(1)

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)
    
    dwrapper.on_message(message)

    while len(dwrapper.to_send) > 0:
        elem = dwrapper.to_send.pop()
        await client.send_message(message.channel, elem[1])

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
