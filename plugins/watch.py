from cloudbot import hook
import asyncio
import praw
import calendar, datetime
import re

BOLD = '\x02'
COLOR = '\x03'
NORMAL = '\x0F'
REVERSED = '\x16'
UNDERLINE = '\x1F'

BLACK = '1'
NAVY_BLUE = '2'
GREEN = '3'
RED = '4'
BROWN = '5'
PURPLE = '6'
OLIVE = '7'
YELLOW = '8'
LIME_GREEN = '9'
TEAL = '10'
AQUA = '11'
BLUE = '12'
PINK = '13'
DARK_GRAY = '14'
LIGHT_GRAY = '15'
WHITE = '16'

tstamps = {}
reddit_inst = None
watching = True

subs_list = [
    'romania',
    'rogonewild',
    'rocringe',
    'rocirclejerk',
    'prsh',
    'roaww',
    'askro',
    'romania_ss',
    'rolistentothis',
    'romanialibera'
]

@hook.on_start()
def init(db):
    #TODO db
    global tstamps
    global reddit_inst

    reddit_inst = praw.Reddit('IRC subreddit watcher by /u/programatorulupeste')

    crt_utc = calendar.timegm(datetime.datetime.utcnow().utctimetuple())

    for sub in subs_list:
        tstamps[sub] = crt_utc

def remove(text):
    return re.sub('(\x02|\x1F|\x16|\x0F|(\x03(\d+(,\d+)?)?)?)', '', text)

def bold(text):
    return BOLD + text + BOLD

def color(text, foreground, background=None):
    color_code = COLOR
    if foreground: color_code += foreground
    if background: color_code += ',%s' % background
    return color_code + text + (COLOR * 3)

def normal(text):
    return NORMAL + text + NORMAL

def reversed(text):
    return REVERSED + text + REVERSED

def underline(text):
    return UNDERLINE + text + UNDERLINE

def do_it(thread):
    sub = thread.subreddit.display_name
    prefix = 'Self post:' if thread.is_self else 'Link post:'
    message = '%s "%s" posted in /r/%s by %s. %s%s' % (
        prefix,
        thread.title,
        sub,
        thread.author,
        (thread.short_link).replace("http://redd.it", "http://ssl.reddit.com"),
        #'' if thread.is_self else (' [ %s ]' % thread.url),
        color(' NSFW', RED) if thread.over_18 else ''
    )

    return message

@hook.periodic(30, initial_interval = 30)
def checker(bot):
    global watching
    global tstamps
    global reddit_inst

    if not watching:
        print("watching disabled")
        return

    print("Checking")
    for conn in bot.connections:
        for csub, tstmp in tstamps.items():

            subreddit = reddit_inst.get_subreddit(csub)
            newest = tstamps[csub]
            for submission in subreddit.get_new(limit=10):

                #print(csub, submission, submission.created_utc, tstamps[csub])
                if int(submission.created_utc) > tstamps[csub]:
                    #print(submission.created_utc, tstamps[csub])

                    if int(submission.created_utc) > newest:
                        newest = int(submission.created_utc)
                    bot.connections[conn].message("#roddit-announcer", do_it(submission))

            tstamps[csub] = newest

@hook.command("swlist")
def list_logs(text):
    msg = 'Watching: '
    for i in subs_list:
        msg += i + ' '
    return msg

@hook.command("startwatch", permissions=["permissions_users"])
def start_watch():
    global watching
    watching = True
    return "Started watching"

@hook.command("stopwatch", permissions=["permissions_users"])
def stop_watch():
    global watching
    watching = False
    return "Stopped watching"
