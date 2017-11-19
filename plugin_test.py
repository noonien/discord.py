import os, re
import discord
import asyncio
import time
import logging
import plugin
import json
import traceback
import threading
from plugin import PluginManager
from cloudbot.event import Event, CommandEvent, EventType

class DiscordWrapper():
    def __init__(self, discord_client, plugin_manager):
        self.discord_client = discord_client
        self.plugin_manager = plugin_manager
        self.connections = {}

        self.connections[0] = self

        self.to_send = []
        self.name = "roddit"
        self.data_dir = "data"
        self.logger = logging.getLogger("cloudbot")

        with open('bot_config.json') as data_file:
            self.config = json.load(data_file)

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

    def action(self, target, text):
        print("action (%s) %s" % (target, text))
        self.to_send.append((target, text))

    def get_channel_by_name(self, cname):
        for server in client.servers:
            for channel in server.channels:
                if channel.name == cname:
                    return channel
        return None

    def on_message(self, message):
        event = Event(bot=dwrapper, event_type=EventType.message)
        event.content = message.content
        event.chan = message.channel.name
        event.author = message.author
        event.conn = self
        event.nick = message.author.name #TODO .mention on mentions
        self.nick = client.user.name

        # Raw IRC hook
        for raw_hook in self.plugin_manager.catch_all_triggers:
            self.plugin_manager.launch(raw_hook, Event(hook=raw_hook, base_event=event))
        if event.irc_command in self.plugin_manager.raw_triggers:
            for raw_hook in self.plugin_manager.raw_triggers[event.irc_command]:
                self.plugin_manager.launch(raw_hook, Event(hook=raw_hook, base_event=event))


        command_re = r'(?i)^(?:[{}]|{}[,;:]+\s+)(\w+)(?:$|\s+)(.*)'.format(self.config["command_prefix"], event.nick)
        cmd_match = re.match(command_re, event.content)
        if cmd_match:
            command = cmd_match.group(1).lower()
            if command in self.plugin_manager.commands:
                command_hook = self.plugin_manager.commands[command]
                command_event = CommandEvent(hook=command_hook, text=cmd_match.group(2).strip(),
                                         triggered_command=command, base_event=event)

                # TODO account for these
                thread = threading.Thread(target=self.plugin_manager.launch, args=(command_hook, command_event))
                thread.start()
                #self.plugin_manager.launch(command_hook, command_event)

    def on_periodic(self):
        for name, plugin in self.plugin_manager.plugins.items():
            for periodic in plugin.periodic:
                if time.time() - periodic.last_time > periodic.interval:
                    periodic.last_time = time.time()
                    event = Event(bot=dwrapper, hook=periodic)

                    # TODO account for these
                    thread = threading.Thread(target=self.plugin_manager.launch, args=(periodic, event))
                    thread.start()
                    #self.plugin_manager.launch(periodic, event)


#logger = logging.getLogger('discord')
#logger.setLevel(logging.DEBUG)
#handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
#handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
#logger.addHandler(handler)

client = discord.Client()
dwrapper = DiscordWrapper(client, None)
plugin_manager = PluginManager(dwrapper)
plugin_manager.load_all(os.path.abspath("plugins"))

dwrapper.plugin_manager = plugin_manager

async def polling_task():
    global plugin_manager
    await client.wait_until_ready()

    while not client.is_closed:
        try:
            dwrapper.on_periodic()
        except Exception:
            traceback.print_stack()
            traceback.print_exc()

        while len(dwrapper.to_send) > 0:
            elem = dwrapper.to_send.pop()
            cname = elem[0]
            if cname[0] == "#":
                cname = cname[1:]

            channel = dwrapper.get_channel_by_name(cname)
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

    try:
        dwrapper.on_message(message)
    except Exception:
        traceback.print_stack()
        traceback.print_exc()

    while len(dwrapper.to_send) > 0:
        elem = dwrapper.to_send.pop()

        cname = elem[0]
        if cname[0] == "#":
            cname = cname[1:]

        if elem[0] is None:
            await client.send_message(message.channel, elem[1])
        else:
            channel = dwrapper.get_channel_by_name(elem[0])
            await client.send_message(channel, elem[1])

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    client.connections = {}
    client.connections[0] = client

client.loop.create_task(polling_task())

client.run(dwrapper.config["discord_token"])
