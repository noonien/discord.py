import discord
import asyncio
import logging
import traceback
import time
from dwrapper import DiscordWrapper

client = discord.Client()
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

dwrapper = DiscordWrapper(client)

async def thread_async(client, channel, elem):
    client.send_message(channel, elem)


async def send_pending_messages():
    while len(dwrapper.to_send) > 0:
        elem = dwrapper.to_send.pop(0)
        cname = elem[0]

        if cname[0] == "#":
            cname = cname[1:]

        channel = dwrapper.get_channel_by_name(cname)

        if channel:
            await client.send_message(channel, elem[1])

    while len(dwrapper.to_delete) > 0:
        elem = dwrapper.to_delete.pop(0)
        await client.delete_message(elem)

    while len(dwrapper.to_add_role) > 0:
        elem = dwrapper.to_add_role.pop(0)
        await client.add_roles(elem[0], elem[1])

    while len(dwrapper.to_rem_role) > 0:
        elem = dwrapper.to_rem_role.pop(0)
        print("Remove role " + str(elem[1]))
        await client.remove_roles(elem[0], elem[1])

async def polling_task():
    global plugin_manager
    await client.wait_until_ready()

    while not client.is_closed:
        try:
            dwrapper.on_periodic()
        except Exception:
            traceback.print_stack()
            traceback.print_exc()

        try:
            await send_pending_messages()
            await asyncio.sleep(1)
        except Exception:
            pass

@client.event
async def on_message_edit(before, after):
    try:
        dwrapper.on_message(after)
    except Exception:
        traceback.print_stack()
        traceback.print_exc()

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    try:
        dwrapper.on_message(message)
    except Exception:
        traceback.print_stack()
        traceback.print_exc()

    await send_pending_messages()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    client.connections = {}
    client.connections[0] = client

    with open("avatar.png", 'rb') as f:
        await client.edit_profile(avatar=f.read())


client.loop.create_task(polling_task())
client.run(dwrapper.config["discord_token"])
