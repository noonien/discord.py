import sys
import re
import json
import os
import collections
from cloudbot import hook
from chardet.cli.chardetect import description_of
from apt_pkg import Description

CMD_JSON = "commands.json"
storage = None
OP_GROUP = "ops"

blacklist_types = ["bot", "pics", "emoji"]
permarole_types = ["bulau", "carcera"]

owner_mgr = None
owners_users_mgr = None
chgroups_mgr = None
chroups_channels_mgr = None
commands_mgr = None
commands_owner_mgr = None
commands_groups_mgr = None
blacklist_mgr = None
permaroles_mgr = None

module_funcs = []
module_funcs_doc = collections.OrderedDict()

class data_type():
    def validate(self):
        raise NotImplementedError("validate() not implemented")

class data_type_string(data_type):
    def __init__(self):
        pass

    def validate(self, data):
        return data

class data_type_discord_ref(data_type):
    def __init__(self):
        pass

    def validate(self, data):
        return data.replace("@", "").replace("<", "").replace(">", "").replace("!", "")

class data_type_list(data_type):
    def __init__(self, dlist):
        self.list = dlist

    def validate(self, data):
        if data in self.list:
            return data
        else:
            raise AttributeError("%s not found in data list" % data)

class data_type_dynamic(data_type):
    def __init__(self, parent_object):
        self.parent_object = parent_object

    def validate(self, data):
        if self.parent_object.exist_thing(data):
            return data
        else:
            raise AttributeError("%s could not be found in %s" % (data, self.parent_object.name))

class bot_thing():
    def __init__(self, name, description, data_ref, data_format, data_hierarchy=None, **kwargs):
        self.data = {}
        self.name = name
        self.format = data_format.split()
        self.kwargs = dict(kwargs)
        self.data = data_ref
        self.description = description

        if self.name not in self.data:
            self.data[self.name] = {}

        for key in kwargs:
            if key not in self.format:
                raise ValueError("Type %s not specified in data_format" % key)


        for elem in self.format:
            if elem not in kwargs:
                raise ValueError("Element %s not in kwargs" % elem)

            if not self.findWholeWord(elem)(data_hierarchy):
                raise ValueError("Element %s not in data_hierarchy" % elem)

        self.hierarchy = json.loads(data_hierarchy)

    def findWholeWord(self, w):
        return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

    def get_data(self):
        return self.data[self.name]

    def assign_rec(self, values, validator, output):
        # Go through the validator
        for key, key_type in validator.items():
            # If a key in the validator is part of the 'to assign' values
            if key in values:
#                 print("Key: %s Value: %s" % (key, values[key]))
#                 print(json.dumps(output))

                # Check if a dictionary needs to be created
                if values[key] not in output and isinstance(key_type, dict):
                    output[values[key]] = {}
#                     print(json.dumps(storage))

                if key not in output and type(key_type) not in [dict]:
                    # Check if a list needs to be created
                    if isinstance(key_type, list):
                        output[key] = []
#                         print(json.dumps(storage))
                    else:
                        # If it's not a list or dict, just assign the value
                        output[key] = values[key]
#                         print(json.dumps(storage))

                # If it's a previously created list, append to it
                if key in output and isinstance(output[key], list):
                    if values[key] not in output[key]:
                        output[key].append(values[key])

                # If it's a dictionary, go deeper
                if isinstance(key_type, dict):
                    self.assign_rec(values, key_type, output[values[key]])

    def remove_rec(self, values, validator, output):
        for key, key_type in validator.items():
            if key in values:
                #print("Key: %s Value: %s" % (key, values[key]))
                #print(json.dumps(output))

                if values[key] in output and isinstance(key_type, dict):
                    if self.remove_rec(values, key_type, output[values[key]]) == False:
                        del output[values[key]]

                    # If the object was emptied, delete it
                    if isinstance(key_type, list) and len(output[values[key]]) == 0:
                        del output[values[key]]
                    #print(json.dumps(storage))

                if key in output and isinstance(key_type, list):
                    output[key].remove(values[key])

                    # If the array was emptied, delete it
                    if (len(output[key]) == 0):
                        del output[key]
                    #print(json.dumps(storage))
                    return True

        return False

    def add_thing(self, text):
        try:
            return self._add_thing(text)
        except Exception as e:
            return str(e)

    def _add_thing(self, text):
        text = text.split()

        if len(text) != len(self.format):
            raise ValueError("Invalid format")

        valid_data = {}
        for order, element in enumerate(text):
            valid_data[self.format[order]] = self.kwargs[self.format[order]].validate(element)

        data_before = json.dumps(self.data[self.name])
        self.assign_rec(valid_data, self.hierarchy, self.data[self.name])
        data_after = json.dumps(self.data[self.name])

        # Check if something was added
        if data_before != data_after:
            save_data()
            return "Added."
        else:
            raise ValueError("Data not added, probably because the input was not correct.")

    def del_thing(self, text):
        try:
            return self._del_thing(text)
        except Exception as e:
            return str(e)

    def _del_thing(self, text):
        text = text.split()

        valid_data = {}
        for order, element in enumerate(text):
            valid_data[self.format[order]] = self.kwargs[self.format[order]].validate(element)
        data_before = json.dumps(self.data[self.name])
        self.remove_rec(valid_data, self.hierarchy, self.data[self.name])
        data_after = json.dumps(self.data[self.name])

        # Check if something was added
        if data_before != data_after:
            save_data()
            return "Deleted. "
        else:
            raise ValueError("Data not deleted, probably because the input was not correct.")

    def get_things(self):
        return self.data[self.name]

    def list_things(self):
        try:
            return self._list_things()
        except Exception as e:
            return str(e)

    def _list_things(self):
        #return " ".join(elem for elem in self.data[self.name])
        return self.data[self.name]

    def list_things_for_thing(self, text, subtype):
        try:
            return self._list_things_for_thing(text, subtype)
        except Exception as e:
            return str(e)

    def _list_things_for_thing(self, text, subtype):
        text = text.split()

        if len(text) > 1:
            raise ValueError("Only one parameter can be given.")

        valid_data = None
        for order, element in enumerate(text):
            valid_data = self.kwargs[self.format[order]].validate(element)

        return self.data[self.name][valid_data][subtype]

    def exist_thing(self, text):
        if text in self.data[self.name]:
            return True
        return False

def save_data():
    jsonfile = open(CMD_JSON, "w")
    json.dump(storage, jsonfile, indent=4)
    print("Saved to disk")

def load_data():
    global storage
    storage = json.load(open(CMD_JSON))
    print("Loaded from disk")
    reload_managers()

# Gather all functions that should be owned by ops by default
def modfunc(*args, **kwargs):
    def _command_hook(func):
        if "doc" in kwargs:
            if kwargs["doc"] not in module_funcs_doc:
                module_funcs_doc[kwargs["doc"]] = []

            module_funcs_doc[kwargs["doc"]].append(func.__name__)

        module_funcs.append(func.__name__)
        return func

    # this decorator is being used directly
    if len(args) == 1 and callable(args[0]):
        module_funcs.append(args[0].__name__)
        return args[0]
    else:  # this decorator is being used indirectly, so return a decorator function
        return lambda func: _command_hook(func)

def reload_managers():
    global owner_mgr
    global owners_users_mgr
    global chgroups_mgr
    global chroups_channels_mgr
    global commands_mgr
    global commands_owner_mgr
    global commands_groups_mgr
    global blacklist_mgr
    global permaroles_mgr

    # Manages owner groups
    owner_mgr = bot_thing(name="owners",
                          description="Manage user groups. A user group can be set to 'own' a command, \
so that only users of the user group can use that command.",
                          data_ref=storage,
                          data_format="group_name",
                          data_hierarchy='{"group_name":{}}',
                          group_name=data_type_string())

    # Manages the groups
    owners_users_mgr = bot_thing(name="owners",
                                 description="Manage users inside user groups.",
                                 data_ref=storage,
                                 data_format="users group_name",
                                 data_hierarchy='{"group_name":{"users":[]}}',
                                 group_name=data_type_dynamic(owner_mgr),
                                 users=data_type_discord_ref())

    # Manages channel groups
    chgroups_mgr = bot_thing(name="chgroups",
                            description="Manages groups of channels.\
A group of channels can be associated to a command, so that the command can be used only in the channels listed in the group of channels.",
                            data_ref=storage,
                            data_format="group_name",
                            data_hierarchy='{"group_name":{}}',
                            group_name=data_type_string())
    # Manages channels in channel groups
    chroups_channels_mgr = bot_thing(name="chgroups",
                                     description="Manages the channels inside a group of channels.",
                                     data_ref=storage,
                                     data_format="group_name channels",
                                     data_hierarchy='{"group_name":{"channels":[]}}',
                                     channels=data_type_discord_ref(),
                                     group_name=data_type_dynamic(chgroups_mgr))

    # Manages commands
    commands_mgr = bot_thing(name="commands",
                             description="",
                             data_ref=storage,
                             data_format="cmd",
                             data_hierarchy='{"cmd":{}}',
                             cmd=data_type_string())

    # Manages commands owners
    commands_owner_mgr = bot_thing(name="commands",
                                   description="Manage user groups that are associated to a command.",
                                   data_ref=storage,
                                   data_format="cmd owner",
                                   data_hierarchy='{"cmd":{"owner":[]}}',
                                   owner=data_type_dynamic(owner_mgr),
                                   cmd=data_type_dynamic(commands_mgr))

    # Manages commands groups
    commands_groups_mgr = bot_thing(name="commands",
                                    description="Manage channel groups that are associated to a command.",
                                    data_ref=storage,
                                    data_format="cmd groups",
                                    data_hierarchy='{"cmd":{"groups":[]}}',
                                    groups=data_type_dynamic(chroups_channels_mgr),
                                    cmd=data_type_dynamic(commands_mgr))

    # Manages blacklist users
    blacklist_mgr = bot_thing(name="blacklisted_users",
                              description="Manage blacklisted users. A user can be blacklisted from using %s" % blacklist_types,
                              data_ref=storage,
                              data_format="user type",
                              data_hierarchy='{"user":{"type":[]}}',
                              user=data_type_discord_ref(),
                              type=data_type_list(blacklist_types))

    # Manages permaroles users
    permaroles_mgr = bot_thing(name="permaroles",
                               description="Manage permanent roles that can be given to users users. Permanent roles that can be given to users: %s" % permarole_types ,
                               data_ref=storage,
                               data_format="user type",
                               data_hierarchy='{"user":{"type":[]}}',
                               user=data_type_discord_ref(),
                               type=data_type_list(permarole_types))

load_data()

@modfunc(doc=owner_mgr)
@hook.command
def add_user_group(message, text, nick, event):
    """<group name> - Create a user group"""
    message(owner_mgr.add_thing(text))

@modfunc(doc=owner_mgr)
@hook.command
def list_user_groups(message, text, nick, event):
    """List user groups"""
    users = owner_mgr.list_things()

    message(" ".join(var for var in users))

@modfunc(doc=owner_mgr)
@hook.command
def del_user_group(message, text, nick, event):
    """<group name> - Deletes a user group"""
    message(owner_mgr.del_thing(text))

@modfunc(doc=owners_users_mgr)
@hook.command
def add_user_to_ugroup(message, text, nick, event):
    """<user user-group> - Add user to user group"""
    message(owners_users_mgr.add_thing(text))

@modfunc(doc=owners_users_mgr)
@hook.command
def list_users_in_ugroup(message, text, nick, event):
    vals = owners_users_mgr.list_things_for_thing(text, "users")
    message(" ".join("<@%s>" % val for val in vals))

@modfunc(doc=owners_users_mgr)
@hook.command
def del_user_from_ugroup(message, text, nick, event):
    """<user user-group> - Delete user from user group"""
    message(owners_users_mgr.del_thing(text))

@modfunc(doc=chgroups_mgr)
@hook.command
def add_chgroup(message, text, nick, event):
    """<group name> - Create a group of channels"""
    message(chgroups_mgr.add_thing(text))

@modfunc(doc=chgroups_mgr)
@hook.command
def list_chgroups(message, text, nick, event):
    """List available groups of channels"""
    chans = chgroups_mgr.list_things()

    message(" ".join(ch for ch in chans))

@modfunc(doc=chgroups_mgr)
@hook.command
def del_chgroup(message, text, nick, event):
    """<group name> - Delete a group of channels"""
    message(chgroups_mgr.del_thing(text))

def get_chgroups():
    return chgroups_mgr.list_things()

@modfunc(doc=chroups_channels_mgr)
@hook.command
def add_chan_to_chgroup(message, text, nick, event):
    """<channel channel-group> - Add channel to channel group"""
    message(chroups_channels_mgr.add_thing(text))

@modfunc(doc=chroups_channels_mgr)
@hook.command
def list_chans_in_chgroup(message, text, nick, event):
    """<channel-group> - List channels in channel-group"""
    vals = chroups_channels_mgr.list_things_for_thing(text, "channels")
    message(" ".join("<#%s>" % val for val in vals))

@modfunc(doc=chroups_channels_mgr)
@hook.command
def del_chan_from_chgroup(message, text, nick, event):
    """<channel channel-group> - Delete channel from channel group"""
    message(chroups_channels_mgr.del_thing(text))

def add_command(text):
    commands_mgr.add_thing(text)

def list_commands():
    return commands_mgr.list_things()

def del_command(text):
    commands_mgr.del_thing(text)

@modfunc(doc=commands_owner_mgr)
@hook.command
def add_owner_to_cmd(message, text, nick, event):
    """<command user-group> - Add a user-group to own a command"""
    message(commands_owner_mgr.add_thing(text))

@modfunc(doc=commands_owner_mgr)
@hook.command
def list_owners_for_cmd(message, text, nick, event):
    """<command> - List what user-groups own a command"""
    vals = commands_owner_mgr.list_things_for_thing(text, "owner")
    message(" ".join(val for val in vals))

@modfunc(doc=commands_owner_mgr)
@hook.command
def del_owners_from_cmd(message, text, nick, event):
    """<command user-group> - Delete user-group from command ownership list"""
    message(commands_owner_mgr.del_thing(text))

def get_owners_for_cmd(cmd):
    return commands_owner_mgr.list_things_for_thing(cmd, "owner")

@modfunc(doc=commands_groups_mgr)
@hook.command
def add_chgroup_to_cmd(message, text, nick, event):
    """<command channel-group> - Add a channel-group to command"""
    message(commands_groups_mgr.add_thing(text))

@modfunc(doc=commands_groups_mgr)
@hook.command
def list_chgroups_for_cmd(message, text, nick, event):
    """<command> - List in what channel-groups command is usable"""
    vals = commands_groups_mgr.list_things_for_thing(text, "groups")
    message(" ".join(val for val in vals))

@modfunc(doc=commands_groups_mgr)
@hook.command
def del_chgroup_from_cmd(message, text, nick, event):
    """<command channel-group> - Delete a user-group from a command's ownership"""
    message(commands_groups_mgr.del_thing(text))

def get_chgroups_for_cmd(cmd):
    return commands_groups_mgr.list_things_for_thing(cmd, "groups")

@modfunc(doc=blacklist_mgr)
@hook.command
def add_blacklist_user(message, text, nick, event):
    """<user, type> - Restrict user from using type ('bot', 'pics' or 'emoji')"""
    message(blacklist_mgr.add_thing(text))

@modfunc(doc=blacklist_mgr)
@hook.command
def list_blacklisted_users(message, text, nick, event):
    """List users with any type of blacklist"""
    vals = blacklist_mgr.list_things()
    message(" ".join("<@%s>" % val for val in vals))

@modfunc(doc=blacklist_mgr)
@hook.command
def list_blacklist_for_user(message, text, nick, event):
    """<user> - List blacklist types for user"""
    vals = blacklist_mgr.list_things_for_thing(text, "type")
    message(" ".join(val for val in vals))

@modfunc(doc=blacklist_mgr)
@hook.command
def del_blacklist_user(message, text, nick, event):
    """<user, type> - Remove restriction type for user"""
    message(blacklist_mgr.del_thing(text))

@modfunc(doc=permaroles_mgr)
@hook.command
def add_permarole_for_user(message, text, nick, event):
    """<user, type> - Add permarole ('bulau', 'carcera') to user"""
    message(permaroles_mgr.add_thing(text))

@modfunc(doc=permaroles_mgr)
@hook.command
def list_users_with_permaroles(message, text, nick, event):
    """List users that have permaroles assigned"""
    vals = permaroles_mgr.list_things()
    message(" ".join("<@%s>" % val for val in vals))

@modfunc(doc=permaroles_mgr)
@hook.command
def list_permaroles_for_user(message, text, nick, event):
    """<user> - List permarole types for user"""
    vals = permaroles_mgr.list_things_for_thing(text, "type")
    message(" ".join(val for val in vals))

@modfunc(doc=permaroles_mgr)
@hook.command
def del_permarole_user(message, text, nick, event):
    """<user, type> - Delete permarole type for user"""
    message(permaroles_mgr.del_thing(text))


def doc_cmd(bot, command):
    message = ""

    doc = bot.plugin_manager.commands[command].doc
    if doc:
        doc = doc.replace("<","&lt;").replace(">","&gt;") \
            .replace("[", "&lt;").replace("]","&gt;")
        message = "**{}**: {}\n\n".format(command, doc)
    else:
        message = "**{}**: Command has no documentation.\n\n".format(command)

    return message

@modfunc
@hook.command
def genhelp(conn, bot):
    message = "{} Command list\n".format(conn.nick)
    message += "------\n"

    chgroups = get_chgroups()
    commands = list_commands()

    for group in sorted(chgroups):
        message += "## [%s commands](#%s)\n" % (group, group)

    message += "## [Unrestricted commands](#unrestricted-commands-1)\n"
    message += "## [Special commands](#special-commands-1)\n"

    message += "\n\n"

    for group in sorted(chgroups):
        message += "### %s\n\n" % group
        message += "------\n"
        for cmd in sorted(commands.keys()):
            # If command has no owners print it now
            try:
                if group in commands[cmd]["groups"] and len(commands[cmd]["owner"]) == 0:
                    message += doc_cmd(bot, cmd)
            except:
                pass

    message += "### Unrestricted commands\n\n"
    message += "------\n"
    # TODO less iterations
    for cmd in sorted(commands.keys()):
        try:
            if len(commands[cmd]["groups"]) == 0 and len(commands[cmd]["owner"]) == 0:
                message += doc_cmd(bot, cmd)
        except:
            pass


    grouped_cmds = []

    for group, group_list in module_funcs_doc.items():
        grouped_cmds.extend(group_list)

    message += "### Special commands\n\n"
    message += "------\n"
    # Go over the commands AGAIN
    for cmd in sorted(commands.keys()):
        if len(commands[cmd]["owner"]) > 0 and not cmd in grouped_cmds:
            message += doc_cmd(bot, cmd)

    for group, group_list in module_funcs_doc.items():
        message += "###### " + group.description + "\n"

        for el in group_list:
            message += doc_cmd(bot, el)

    docs = os.path.join(os.path.abspath(os.path.curdir), "docs")
    docs = os.path.join(docs, "user")
    f = open(os.path.join(docs, "commands.md"), 'w')
    f.write(message)
    f.close()

@hook.on_start()
def init(bot):
    to_delete = []
    # Check if json commands are missing
    for cmd in list_commands():
        if cmd not in bot.plugin_manager.commands and cmd not in module_funcs:
            print("Removing %s because it's missing" % cmd)
            to_delete.append(str(cmd))

    for cmd in to_delete:
        del_command(cmd)

    # Add missing bot commands to command list
    for cmd in bot.plugin_manager.commands:
        if cmd not in list_commands():
            print("Adding new command %s" % cmd)
            add_command(str(cmd))

    # Add module functions
    for cmd in module_funcs:
        if cmd not in list_commands():
            print("Adding new command %s" % cmd)
            add_command(str(cmd))
        if OP_GROUP not in commands_owner_mgr.list_things_for_thing(str(cmd), "owner"):
            print("Adding ops owners " + cmd)
            commands_owner_mgr.add_thing("%s %s" % (cmd, OP_GROUP))

    load_data()

    bot.dcommands = commands_mgr.get_data()
    bot.dgroups = chroups_channels_mgr.get_data()
    bot.dugroups = owner_mgr.get_data()
    bot.dblacklist = blacklist_mgr.get_data()
    bot.dpermaroles = permaroles_mgr.get_data()
    bot.OP_GROUP = OP_GROUP

    save_data()
