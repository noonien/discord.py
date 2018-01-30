from cloudbot import hook
import os
import json

groups = {}
commands = {}

CMD_JSON = "commands.json"

def load_commands():
    """Load commands config from disk"""
    try:
        global commands
        global groups
        # Get the data from disk
        jsonfile = open(CMD_JSON)
        loaded = json.load(jsonfile)

        commands = loaded['commands']
        groups = loaded['groups']
    except BaseException as e:
        print("Error loading: " + str(e))

def save_commands():
    """Save commands config to disk"""
    json_dict ={}
    json_dict['commands'] = commands
    json_dict['groups'] = groups

    jsonfile = open(CMD_JSON, "w")
    json.dump(json_dict, jsonfile, indent=4)

@hook.on_start()
def init(bot):
    module_funcs = [
        "add_cmd_owner",
        "clr_cmd_owner",
        "list_cmd_owner",
        "list_owned_commands",

        "restrict_cmd_to_group",
        "unrestrict_cmd_to_group",
        "list_restrictions_for_cmd",
        "list_restrictions_by_channel",

        "add_group",
        "add_chan_to_group",
        "del_chan_from_group",
        "del_group",
        "list_group",
        "list_groups",
    ]

    load_commands()

    # Check if json commands are missing
    for cmd in commands:
        if cmd not in bot.plugin_manager.commands and cmd not in module_funcs:
            print("Warning: command %s not in bot commands" % cmd)

    # Add missing bot commands to command list
    for cmd in bot.plugin_manager.commands:
        if cmd not in commands:
            print("Adding new command %s" % cmd)
            commands[cmd] = {"groups":[], "owner":[]}

    # Add module functions
    for cmd in module_funcs:
        if cmd not in commands:
            print("Adding new command %s" % cmd)
            commands[cmd] = {"groups":[], "owner":[]}

    bot.dcommands = commands
    bot.dgroups = groups

def add_group_to_command(cmd, group):
    if group not in commands[cmd]["groups"]:
        commands[cmd]["groups"].append(group)

def get_channels_for_cmd(cmd):
    chan_list = []

    for group in commands[cmd]["groups"]:
        chan_list.extend(groups[group]["channels"])

    return chan_list

@hook.command
def restrict_cmd_to_group(message, text, nick, event):
    """<command, group> - restricts 'command' to be used in channels defined by 'group'"""
    cmd = text.split()[0]
    group = text.split()[1]

    if group not in groups:
        message("%s is not a group" % group)
        return

    if cmd != "*":
        if cmd not in commands:
            message("%s is not a command" % cmd)
            return

        add_group_to_command(cmd, group)
        message("Added group %s to command %s" % (group, cmd))
    else:
        cmd_list = ""
        for pcmd in commands:
            add_group_to_command(pcmd, group)
            cmd_list += " " + pcmd

        message("Added group %s to command %s" % (group, cmd_list))
    save_commands()

@hook.command
def list_restrictions_for_cmd(message, text, nick, event):
    """<command> - Lists the group restrictions for 'command'"""
    cmd = text.split()[0]

    if cmd not in commands:
        message("%s is not a command" % cmd)
        return

    msg = "%s restricted to groups: " % cmd
    for group in commands[cmd]["groups"]:
        msg += " " + group

    message(msg)

@hook.command
def list_restrictions_by_channel(message, text, nick, event):
    """Lists all commands, grouped by restricted channel"""
    chan_list = []
    for group in groups:
        chan_list.extend(groups[group]["channels"])

    cmd_to_chans = {}

    for cmd in commands:
        cmd_to_chans[cmd] = get_channels_for_cmd(cmd)

    msg = ""

    for chan in chan_list:
        msg += "Commands usable in <#%s>: " % chan

        for cmd in cmd_to_chans:
            if chan in cmd_to_chans[cmd]:
                msg += " " + cmd
        msg += "\n"

    msg += "Unrestricted commands:"
    for cmd in commands:
        if len(commands[cmd]["groups"]) == 0:
            msg += " " + cmd

    message(msg)


@hook.command
def unrestrict_cmd_to_group(message, text, nick, event):
    """<command, group> - Removes 'group' from the restriction list for 'command'"""
    cmd = text.split()[0]
    group = text.split()[1]

    if group not in groups:
        message("%s is not a group" % group)
        return

    if cmd not in commands:
        message("%s is not a command" % cmd)
        return

    if group in commands[cmd]["groups"]:
        commands[cmd]["groups"].remove(group)

    message("Removed group %s from command %s" % (group, cmd))
    save_commands()

@hook.command
def add_group(message, text, nick, event):
    """<group> - Creates a group"""
    text = text.split()[0]
    groups[text] = {"channels":[]}

    message("Created group: " + text)
    save_commands()

@hook.command
def del_group(message, text, nick, event):
    """<group> - deletes a group"""
    group = text.split()[0]

    if group not in groups:
        message("%s is not a group" % group)
        return
    del groups[group]
    message("Deleted group: " + text)

    cmd_removals = ""
    for cmd in commands:
        if group in cmd["groups"]:
            cmd["groups"].remove(group)
            cmd_removals += " " + cmd

    if cmd_removals != "":
        message("Group removed from: " + cmd_removals)

    save_commands()

@hook.command
def add_chan_to_group(message, text, nick, event):
    """<channel, group> - Add 'channel' to the restriction group 'group'"""
    chan = text.split()[0]
    group = text.split()[1]

    if not chan.startswith("<#"):
        message("Add channel using full name (e.g. #test)")
        return

    chan = chan[2:-1]

    if group not in groups:
        message("%s is not a group" % chan)
        return

    if chan not in groups[group]["channels"]:
        groups[group]["channels"].append(chan)

    message("Added channel <#%s> to group %s" % (chan, group))
    save_commands()

@hook.command
def del_chan_from_group(message, text, nick, event):
    """<channel, group> - Removes 'channel' from the restriction group 'group'"""
    chan = text.split()[0]
    group = text.split()[1]

    if not chan.startswith("<#"):
        message("Add channel using full name (e.g. #test)")
        return

    chan = chan[2:-1]

    if group not in groups:
        message("%s is not a group" % group)
        return

    groups[group]["channels"].remove(chan)
    message("Removed channel <#%s> from group %s" % (chan, group))
    save_commands()

@hook.command
def list_group(message, text, nick, event):
    """<group> - Lists the restriction channels for 'group'"""
    group = text.split()[0]

    if group not in groups:
        message("%s is not a group" % group)
        return

    to_print = "Group %s:\n" % group
    for chan in groups[group]["channels"]:
        to_print += "<#" + chan + "> "

    message(to_print)

@hook.command
def list_groups(message, text, nick, event):
    """Lists all groups"""
    msg = "Groups:"
    for group in groups:
        msg += " " + group

    message(msg)

@hook.command
def add_cmd_owner(message, text, nick, event):
    """<command, owner> - Adds an owner for 'command' - only the list owners will be able to use the command"""
    text = text.split()
    command = text[0]
    owner = text[1].replace("@", "").replace("<", "").replace(">", "")

    if command not in commands:
        message("Could not find %s in command list, you dummy" % command)
        return

    if owner not in commands[command]["owner"]:
        commands[command]["owner"].append(owner)

    save_commands()
    message("Added %s to own %s" % (owner, command))

@hook.command
def clr_cmd_owner(message, text, nick, event):
    """<command, owner> - Remove 'owner' from the command owner list"""
    text = text.split()
    command = text[0]
    owner = text[1].replace("@", "").replace("<", "").replace(">", "")

    if command not in commands:
        message("Could not find %s in command list, you dummy" % command)
        return

    if owner in commands[command]["owner"]:
        commands[command]["owner"].remove(owner)
    else:
        message("%s is not an owner for %s" % (owner, command))
        return

    save_commands()
    message("Removed %s from %s" % (owner, command))

@hook.command
def list_cmd_owner(message, text, nick, event):
    """<command> - List who own 'command'"""
    text = text.split()
    command = text[0]

    if command not in commands:
        message("Could not find %s in command list, you dummy" % command)
        return

    own_list = ""
    for owner in commands[command]['owner']:
        own_list += " <@" + owner + ">"
    message("Owners for %s: %s" % (command, own_list))

@hook.command
def list_owned_commands(message, text, nick, event):
    """List commands with owners"""
    # Get commands that have owners
    to_list = []
    for command in commands:
        if len(commands[command]['owner']) > 0:
            to_list.append(command)

    # Message for each command
    for cmd in to_list:
        own_list = ""
        for owner in commands[cmd]['owner']:
            own_list += " <@" + owner + ">"
        message("Owners for %s: %s" % (cmd, own_list))
