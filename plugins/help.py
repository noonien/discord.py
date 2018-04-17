from operator import attrgetter
import asyncio
import re
import os

from cloudbot import hook
from cloudbot.util import formatting, web


@asyncio.coroutine
@hook.command("help", autohelp=False)
def help_command(text, chan, conn, bot, notice, message):
    """[command] - gives help for [command], or lists all available commands if no command is specified
    :type text: str
    :type conn: cloudbot.client.Client
    :type bot: cloudbot.bot.CloudBot
    """
    if text:
        searching_for = text.lower().strip()
        if not re.match(r'^\w+$', searching_for):
            notice("Invalid command name '{}'".format(text))
            return
    else:
        searching_for = None

    if searching_for:
        if searching_for in bot.plugin_manager.commands:
            doc = bot.plugin_manager.commands[searching_for].doc
            if doc:
                if doc.split()[0].isalpha():
                    # this is using the old format of `name <args> - doc`
                    message = "{}{}".format(conn.config["command_prefix"][0], doc)
                else:
                    # this is using the new format of `<args> - doc`
                    message = "{}{} {}".format(conn.config["command_prefix"][0], searching_for, doc)
                notice(message)
            else:
                notice("Command {} has no additional documentation.".format(searching_for))
        else:
            notice("Unknown command '{}'".format(searching_for))
    else:
        notice("See https://github.com/gc-plp/discord.py/blob/async/docs/user/commands.md for a list of commands that you can use")
        notice("For detailed help, use {}help <command>, without the brackets.".format(conn.config["command_prefix"]))
