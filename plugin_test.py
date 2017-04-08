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
            elem = dwrapper.to_send.pop(0)
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
        elem = dwrapper.to_send.pop(0)
        
        cname = elem[0]
        if cname[0] == "#":
            cname = cname[1:]
        
        if elem[0] is None:
            await client.send_message(message.channel, elem[1])
        else:
            channel = dwrapper.get_channel_by_name(cname)
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