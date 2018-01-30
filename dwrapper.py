import traceback
import os
import logging
import time
import threading
import re
import plugin
import json
import asyncio
import pdb
from plugin import PluginManager
from cloudbot.event import Event, CommandEvent, EventType

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import MetaData
from sqlalchemy.pool import StaticPool

from cloudbot.util import database

class DiscordWrapper():
    def __init__(self, discord_client):
        self.discord_client = discord_client
        self.plugin_manager = PluginManager(self)

        self.connections = {}
        self.to_send = []
        self.name = "roddit"
        self.data_dir = "data"
        self.logger = logging.getLogger("cloudbot")

        self.connections[self.name] = self
        self.ready = True

        with open('bot_config.json') as data_file:
            self.config = json.load(data_file)

        self.loop = asyncio.get_event_loop()

        db_path = self.config.get('database', 'sqlite:///cloudbot.db')
        self.db_engine = create_engine(db_path, connect_args={'check_same_thread':False}, poolclass=StaticPool)
        self.db_factory = sessionmaker(bind=self.db_engine)
        self.db_session = scoped_session(self.db_factory)
        self.db_metadata = MetaData()
        self.db_base = declarative_base(metadata=self.db_metadata, bind=self.db_engine)

        database.metadata = self.db_metadata
        database.base = self.db_base

        self.plugin_manager.load_all(os.path.abspath("plugins"))
        self.plugin_manager.load_all(os.path.abspath("post-plugins"))

    def __getattr__(self, name):
        msg = "'{}' object has no attribute '{}'"
        raise AttributeError(msg.format(self.__class__, name))

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

    def message(self, target, message):
        print("send (%s) %s" % (target, message))
        if len(message) > 400:
            i = 0
            while len(message) > 400:
                self.to_send.append((target, message[i:i + 400]))
                message = message[i + 400:]
        self.to_send.append((target, message))

    def notice(self, target, text):
        print("notice (%s) %s" % (target, text))
        self.to_send.append((target, text))

    def action(self, target, text):
        print("action (%s) %s" % (target, text))
        self.to_send.append((target, text))

    def get_channel_by_name(self, cname):
        for server in self.discord_client.servers:
            for channel in server.channels:
                if channel.name == cname:
                    return channel
        return None

    def on_message(self, message):
        event = Event(bot=self, event_type=EventType.message)
        event.content = message.content
        event.chan = message.channel.name
        event.author = message.author
        event.conn = self
        event.nick = message.author.name #TODO .mention on mentions
        self.nick = self.discord_client.user.name

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

                # This should never fail - all commands are registered
                cmd_desc = self.dcommands[command]
                if len(cmd_desc['owner']) > 0 and message.author.id not in cmd_desc['owner']:
                    self.message(message.channel.name, "You don't own %s" % command)
                    return
                if len(cmd_desc['groups']) > 0:
                    allowed_chans = []
                    for group in cmd_desc['groups']:
                        allowed_chans.extend(self.dgroups[group]["channels"])
                    if message.channel.id not in allowed_chans:
                        self.message(message.channel.name, "%s can only be used in: %s" % (command, " ".join(["<#%s>" % chan for chan in allowed_chans])))
                        return

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
                    event = Event(bot=self, hook=periodic)

                    # TODO account for these
                    thread = threading.Thread(target=self.plugin_manager.launch, args=(periodic, event))
                    thread.start()
                    #self.plugin_manager.launch(periodic, event)
