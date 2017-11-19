import asyncio
import os
import codecs
import time

import cloudbot
from cloudbot import hook
from cloudbot.event import EventType


# +---------+
# | Formats |
# +---------+
from cloudbot.util.formatting import strip_colors

base_formats = {
    EventType.message: "[{hour}:{minute}:{second}] <{nick}> {content}",
    EventType.notice: "[{server}:{channel}] -{nick}- {content}",
    EventType.action: "[{server}:{channel}] * {nick} {content}",
    EventType.join: "[{server}:{channel}] -!- {nick} [{user}@{host}] has joined",
    EventType.part: "[{server}:{channel}] -!- {nick} [{user}@{host}] has left ({content})",
    EventType.kick: "[{server}:{channel}] -!- {nick} has kicked {target} ({content})",
}

irc_formats = {
    "MODE": "[{server}:{channel}] -!- mode/{channel} [{param_tail}] by {nick}",
    "TOPIC": "[{server}:{channel}] -!- {nick} has changed the topic to: {content}",
    "QUIT": "[{server}] -!- {nick} has quit ({content})",
    "INVITE": "[{server}] -!- {nick} has invited {target} to {chan}",
    "NICK": "[{server}] {nick} is now known as {content}",
}

irc_default = "[{server}] {irc_raw}"

ctcp_known = "[{server}:{channel}] {nick} [{user}@{host}] has requested CTCP {ctcp_command}"
ctcp_known_with_message = ("[{server}:{channel}] {nick} [{user}@{host}] "
                           "has requested CTCP {ctcp_command}: {ctcp_message}")
ctcp_unknown = "[{server}:{channel}] {nick} [{user}@{host}] has requested unknown CTCP {ctcp_command}"
ctcp_unknown_with_message = ("[{server}:{channel}] {nick} [{user}@{host}] "
                             "has requested unknown CTCP {ctcp_command}: {ctcp_message}")


# +------------+
# | Formatting |
# +------------+

def format_event(event):
    """
    Format an event
    :type event: cloudbot.event.Event
    :rtype: str
    """

    # Setup arguments
    hour, minute, second = time.strftime("%H,%M,%S").split(',')

    args = {
        "server": event.conn.name, "target": event.target, "channel": event.chan, "nick": event.nick + "/" + event.author.display_name + "/" + event.author.id,
        "user": event.user, "host": event.host,
        "hour": hour,
        "minute": minute,
        "second": second
    }

    if event.content is not None:
        # We can't strip colors from None
        args["content"] = strip_colors(event.content)
    else:
        args["content"] = None

    # Try formatting with non-connection-specific formats
    return base_formats[event.type].format(**args)

# +--------------+
# | File logging |
# +--------------+

file_format = "{server}_{chan}_%Y%m%d.log"
raw_file_format = "{server}_%Y%m%d.log"

folder_format = "%Y"

# Stream cache, (server, chan) -> (file_name, stream)
stream_cache = {}
# Raw stream cache, server -> (file_name, stream)
raw_cache = {}


def get_log_filename(server, chan):
    current_time = time.localtime()
    folder_name = time.strftime(folder_format, current_time)
    file_name = time.strftime(file_format.format(chan=chan, server=server), current_time).lower()
    return os.path.join("logs", folder_name, file_name)


def get_log_stream(server, chan):
    new_filename = get_log_filename(server, chan)
    cache_key = (server, chan)
    old_filename, log_stream = stream_cache.get(cache_key, (None, None))

    # If the filename has changed since we opened the stream, we should re-open
    if new_filename != old_filename:
        # If we had a stream open before, we should close it
        if log_stream is not None:
            log_stream.flush()
            log_stream.close()

        logging_dir = os.path.dirname(new_filename)
        os.makedirs(logging_dir, exist_ok=True)

        # a dumb hack to bypass the fact windows does not allow * in file names
        new_filename = new_filename.replace("*", "server")

        log_stream = codecs.open(new_filename, mode="a", encoding="utf-8", buffering=1)
        stream_cache[cache_key] = (new_filename, log_stream)

    return log_stream


def get_raw_log_filename(server):
    current_time = time.localtime()
    folder_name = time.strftime(folder_format, current_time)
    file_name = time.strftime(raw_file_format.format(server=server), current_time).lower()
    return os.path.join(cloudbot.logging_dir, "raw", folder_name, file_name)


def get_raw_log_stream(server):
    new_filename = get_raw_log_filename(server)
    old_filename, log_stream = stream_cache.get(server, (None, None))

    # If the filename has changed since we opened the stream, we should re-open
    if new_filename != old_filename:
        # If we had a stream open before, we should close it
        if log_stream is not None:
            log_stream.flush()
            log_stream.close()

        logging_dir = os.path.dirname(new_filename)
        os.makedirs(logging_dir, exist_ok=True)

        log_stream = codecs.open(new_filename, mode="a", encoding="utf-8", buffering=1)
        stream_cache[server] = (new_filename, log_stream)

    return log_stream


@hook.irc_raw("*", singlethread=True)
def log_raw(event):
    """
    :type event: cloudbot.event.Event
    """
    logging_config = event.bot.config.get("logging", {})
    if not logging_config.get("raw_file_log", False):
        return

    stream = get_raw_log_stream(event.conn.name)
    stream.write(event.irc_raw + os.linesep)
    stream.flush()


@hook.irc_raw("*", singlethread=True)
def log(event):
    """
    :type event: cloudbot.event.Event
    """
    text = format_event(event)

    if text is not None:
        #if event.irc_command in ["PRIVMSG", "PART", "JOIN", "MODE", "TOPIC", "QUIT", "NOTICE"] and event.chan:
        stream = get_log_stream(event.conn.name, event.chan)
        stream.write(text + os.linesep)
        stream.flush()


# Log console separately to prevent lag
@asyncio.coroutine
@hook.irc_raw("*")
def console_log(bot, event):
    """
    :type bot: cloudbot.bot.CloudBot
    :type event: cloudbot.event.Event
    """
    text = format_event(event)
    if text is not None:
        bot.logger.info(text)


# TODO: @hook.onstop() for when unloaded
@hook.command("flushlog", permissions=["botcontrol"])
def flush_log():
    for name, stream in stream_cache.values():
        stream.flush()
    for name, stream in raw_cache.values():
        stream.flush()
