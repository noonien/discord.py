from cloudbot import hook
import discord

@hook.command
def gamer(message, text, server, event, bot):
    roles = [
            "World of Warcraft",
            "PUBG",
            "Counter-Strike",
            "World of Tanks",
            "Path of Exile",
            "League of Legends",
            "DOTA",
            "Consolist",
            "Fortnite"
            ]

    actions = ["add", "clear"]

    split = text.split()
    action = split[0]
    role = " ".join(split[1:])

    if action not in actions:
        message("The action can only be: %s" % str(actions))
        return

    if role not in roles:
        message("%s is not a role. Available roles: %s" % (role, str(roles)))
        return

    if action == "add":
        role_id = discord.utils.find(lambda m: m.name == role, server.roles)
        bot.to_add_role.append((event.author, role_id))
        message("Done! You've been given the %s role." % role)

    elif action == "clear":
        role_id = discord.utils.find(lambda m: m.name == role, server.roles)
        bot.to_rem_role.append((event.author, role_id))
        message("Removed role %s" % role)
