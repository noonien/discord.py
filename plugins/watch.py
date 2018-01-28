from cloudbot import hook
import asyncio
import praw
import calendar, datetime
import re
from sqlalchemy import Table, Column, String, PrimaryKeyConstraint, DateTime
from sqlalchemy.sql import select
from cloudbot.util import database


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
g_db = None

subs = Table(
        'wsubs',
        database.metadata,
        Column('sub', String),
        Column('timestamp', DateTime)
        )

def set_crt_timestamps():
    global tstamps

    crt_utc = datetime.datetime.utcnow()

    g_db.execute(subs.update(values={subs.c.timestamp: crt_utc}))
    g_db.commit()

@hook.on_start()
def init(db):
    global reddit_inst
    global g_db

    g_db = db
    reddit_inst = praw.Reddit("irc_bot", user_agent='IRC subreddit watcher by /u/programatorulupeste')

    set_crt_timestamps()

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
    message = '"%s" posted in /r/%s by %s. %s' % (
        thread.title,
        sub,
        thread.author,
        (thread.shortlink).replace("http://redd.it", "http://ssl.reddit.com")
    )

    return prefix + " " + message

@hook.periodic(60, initial_interval = 60)
def checker(bot):
    global watching
    global reddit_inst

    if not watching:
        print("watching disabled")
        return

    db_subs = g_db.execute(subs.select())
    tstamps = {}
    for row in db_subs:
        tstamps[row['sub']] = row['timestamp']
    print("Checking")
    for conn in bot.connections:
        for csub in tstamps:
            try:
                subreddit = reddit_inst.subreddit(csub)
                newest = tstamps[csub]
                for submission in subreddit.new():
                    subtime = datetime.datetime.utcfromtimestamp(submission.created_utc)
                    if subtime > tstamps[csub]:
                        if subtime > newest:
                            newest = subtime
                        bot.connections[conn].message("#reddit", do_it(submission))

                g_db.execute(subs.update().where(subs.c.sub == csub).values(timestamp=newest))
                g_db.commit()
            except BaseException as e:
                print(str(e))
                print("Exception generated for sub: " + csub)
    print("Done.")

@hook.command("swlist")
def list_logs(text):
    msg = 'Watching: '
    db_subs = g_db.execute(subs.select())
    for i in db_subs:
        msg += i['sub'] + ' '
    return msg

@hook.command("swadd")
def swadd(text):
    text = text.split()[0]
    g_db.execute(subs.insert().values(sub=text, timestamp=datetime.datetime.now()))
    g_db.commit()

@hook.command("swdel")
def swdel(text):
    text = text.split()[0]
    g_db.execute(subs.delete(subs.c.sub == text))
    g_db.commit()

@hook.command("startwatch", permissions=["permissions_users"])
def start_watch():
    global watching
    watching = True
    set_crt_timestamps()
    return "Started watching"

@hook.command("stopwatch", permissions=["permissions_users"])
def stop_watch():
    global watching
    watching = False
    return "Stopped watching"
