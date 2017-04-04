from cloudbot import hook
import socket

I2D_PORT = 17010
D2I_PORT = 17011

irc_to_dsc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
irc_to_dsc.setblocking(0)
irc_to_dsc.bind(('localhost', I2D_PORT))

dsc_to_irc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dsc_to_irc.setblocking(0)

@hook.irc_raw("*")
def discord_to_irc(event):
    global dsc_to_irc
    if event.chan == 'bridge':
        print("Sending " + event.content)
        msg = "<%s> %s" % (event.author, event.content)
        dsc_to_irc.sendto(str.encode(msg), ('localhost', D2I_PORT))

@hook.periodic(1, initial_interval = 1)
def irc_to_discord(bot):
    global irc_to_dsc
    try:
        rcv_data, addr = irc_to_dsc.recvfrom(512)
        for conn in bot.connections:
            bot.connections[conn].message("#bridge", "(IRC:#rodiscord)" + rcv_data.decode('utf-8'))
    except socket.error:
        pass
