import os
import re
import praw
import random
import asyncio
from cloudbot import hook
from datetime import datetime
from sqlalchemy import Table, Column, String, PrimaryKeyConstraint, DateTime
from sqlalchemy.sql import select
from cloudbot.util import database

USER_AGENT = "Image fetcher for Snoonet:#Romania by /u/programatorulupeste"
domains = ['imgur.com', 'gfycat.com', 'redditmedia.com', 'i.redd.it', 'flic.kr', '500px.com']

dont_cache = ['random', 'randnsfw']

g_db = None

links = Table(
    'links',
    database.metadata,
    Column('subreddit', String),
    Column('link', String)
)

subs = Table(
    'subs',
    database.metadata,
    Column('subreddit', String),
    Column('cachetime', DateTime)
)

def get_links_from_sub(r, sub):

    subreddit = r.subreddit(sub)

    new_links = []
    for submission in subreddit.top("month"):
        if not submission.is_self:
            for domain in domains:
                if domain in submission.url:
                    new_links.append(submission.url)
                    break

    return new_links

def refresh_cache(r, el):
    print("Refreshing cache for " + el)
    delete = links.delete(links.c.subreddit == el)
    g_db.execute(delete)
    g_db.commit()

    new_links =  get_links_from_sub(r, el)

    last_fetch = datetime.utcnow()

    # Update db
    for nlink in new_links:
        g_db.execute(links.insert().values(subreddit=el, link=nlink))

    # Update db timestamp
    g_db.execute(subs.update().where(subs.c.subreddit == el).values(cachetime=last_fetch))

    g_db.commit()


def del_sub(sub):
    print("Removing sub %s" % sub)
    g_db.execute(subs.delete().where(subs.c.subreddit == sub))
    g_db.commit()

def get_links_from_subs(sub):
    data = []
    r = praw.Reddit("irc_bot", user_agent=USER_AGENT)

    now = datetime.utcnow()

    db_sub_list = g_db.execute(subs.select())
    sub_list = {}
    for row in db_sub_list:
        sub_list[row['subreddit']] = row['cachetime']

    for el in sub:
        if el in dont_cache:
            print("%s is in no cache list" % el)
            data = get_links_from_sub(r, el)
            continue

        if el not in sub_list:
            g_db.execute(subs.insert().values(subreddit=el, cachetime=datetime.min))
            sub_list[el] = datetime.min
            g_db.commit()

        # Cache older than 2 hours?
        if (now - sub_list[el]).total_seconds() > 7200:
            try:
                refresh_cache(r, el)
            except Exception as e:
                print(e)
                del_sub(el)
                return ["Error :/"]
        else:
            print("Cache for %s is %i" %(el, (now - sub_list[el]).total_seconds()))

        db_links = g_db.execute(select([links.c.link]).where(links.c.subreddit == el))

        for row in db_links:
            data.extend(row)

        if len(data) == 0:
            data = ["Got nothing. Will try harder next time."]
            for el in sub:
                del_sub(el)
    return data

@asyncio.coroutine
@hook.on_start()
def init(db):
    global g_db
    g_db = db
    data = ""
    with open(os.path.realpath(__file__)) as f:
        data = f.read()

    data = data.replace(" ", "")
    data = data.replace("\n","")
    data = data.replace("\'","")
    data = data.replace("\"","")

    start = "get_links_from_subs" + "(["
    end = "])"

    startpos = 0
    endpos = 0
    while True:
        startpos = data.find(start, startpos)
        endpos = data.find(end, startpos)

        if startpos == -1:
            break

        subs = data[startpos + len(start):endpos].split(",")
        get_links_from_subs(subs)

        startpos += len(start)

@hook.periodic(300, initial_interval=300)
def refresh_porn():
    print("Refreshing...")
    db_subs = g_db.execute(select([subs.c.subreddit]))
    for el in db_subs:
        fake_list = [el['subreddit']]
        get_links_from_subs(fake_list)

@hook.command()
def roscate(message, text, nick):
    data = get_links_from_subs(['ginger', 'redheads', 'RedheadGifs'])

    return random.choice(data) + " NSFW!"

@hook.command()
def tatuate(message, text, nick):
    data = get_links_from_subs(['altgonewild'])

    return random.choice(data) + " NSFW!"

@hook.command()
def nsfwfunny(message, text, nick):
    data = get_links_from_subs(['nsfwfunny'])

    return random.choice(data) + " NSFW!"

@hook.command()
def craci(message, text, nick):
    data = get_links_from_subs(['thighhighs', 'stockings'])

    return random.choice(data) + " NSFW!"

@hook.command()
def buci(message, text, nick):
    data = get_links_from_subs(['ass', 'asstastic', 'assinthong', 'pawg'])

    return random.choice(data) + " NSFW!"

@hook.command()
def tzatze(message, text, nick):
    data = get_links_from_subs(['boobs', 'boobies', 'BiggerThanYouThought'])

    return random.choice(data) + " NSFW!"

@hook.command()
def fetish(message, text, nick):
    data = get_links_from_subs(['kinky', 'bdsm', 'bondage', 'collared', 'lesdom'])

    return random.choice(data) + " NSFW!"

@hook.command()
def teen(message, text, nick):
    data = get_links_from_subs(['LegalTeens', 'Just18', 'youngporn', 'barelylegal'])

    return random.choice(data) + " NSFW!"

@hook.command()
def sloboz(message, text, nick):
    data = get_links_from_subs(['cumsluts', 'GirlsFinishingTheJob'])

    return random.choice(data) + " NSFW!"

@hook.command()
def anal(message, text, nick):
    data = get_links_from_subs(['anal', 'painal'])

    return random.choice(data) + " NSFW!"

@hook.command()
def milf(message, text, nick):
    data = get_links_from_subs(['milf'])

    return random.choice(data) + " NSFW!"

@hook.command()
def amateur(message, text, nick):
    data = get_links_from_subs(['RealGirls', 'Amateur', 'GoneWild'])

    return random.choice(data) + " NSFW!"

@hook.command()
def traps(message, text, nick):
    data = get_links_from_subs(['Tgirls', 'traps', 'gonewildtrans', 'tgifs'])

    return random.choice(data) + " NSFW!"

@hook.command()
def aww():
    data = get_links_from_subs(['aww'])

    return random.choice(data) + " aww..."

@hook.command()
def pisi():
    data = get_links_from_subs(['cats'])

    return random.choice(data) + " aww..."

@hook.command()
def capre():
    data = get_links_from_subs(['doggy'])

    return random.choice(data) + " NSFW!"

@hook.command()
def lesbiene():
    data = get_links_from_subs(['dykesgonewild', 'dyke'])

    return random.choice(data) + " NSFW!"

@hook.command()
def thicc():
    data = get_links_from_subs(['pawg', 'thick'])

    return random.choice(data) + " NSFW!"

@hook.command()
def fetch_image(text):
    if text:
        text = text.split()
        data = get_links_from_subs(text)

        return random.choice(data)
    else:
        return "Please specify a sub or a list of subs (e.g.: .fetch_image RomaniaPorn or .fetch_image RomaniaPorn RoGoneWild)"
