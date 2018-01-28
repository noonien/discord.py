import praw
import time
from cloudbot import hook
from datetime import datetime

USER_AGENT = ""
LAST_CHECK = 0

@hook.on_start()
def init(db):
    global USER_AGENT
    global LAST_CHECK

    USER_AGENT = "/r/Romania scraper by /u/programatorulupeste"
    LAST_CHECK = (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()

def split_list(text, max_len):
    ret = []
    start = 0
    crt = start

    text = text.replace('\n', ' ')

    if len(text) > max_len:
        while crt + max_len < len(text):
            crt_max_len = max_len
            while crt_max_len > 1 and text[crt + crt_max_len] != ' ':
                    crt_max_len -= 1
            if crt_max_len == 1:
                crt_max_len = max_len
            ret.append(text[crt:crt + crt_max_len])
            crt += crt_max_len

    ret.append(text[crt:crt + max_len])
    return ret

def wrap_message(comm):
    msg = "Intrebare noua de la %s: %s -> %s" % (comm.author.name, comm.body, (comm.submission.shortlink).replace("http://redd.it", "http://ssl.reddit.com"))
    return split_list(msg, 400)

@hook.periodic(10, initial_interval = 10)
def checker(bot):
    global USER_AGENT
    global LAST_CHECK

    for conn in bot.connections:
        try:
            r = praw.Reddit("irc_bot", user_agent=USER_AGENT)
            subreddit = r.subreddit('romania')

            submission = subreddit.hot(limit = 2)

            for x in submission:
                if x.stickied == True and "/r/Romania Orice" in x.title:
                    #print("found it", LAST_CHECK)

                    for c in reversed(x.comments):
                        if hasattr(c, 'created_utc') and  c.created_utc > LAST_CHECK:
                            #print(c.body)
                            #print(c.created_utc, LAST_CHECK)
                            LAST_CHECK = c.created_utc

                            msg = list(wrap_message(c))
                            for i in msg:
                                bot.connections[conn].message("#reddit", i)
                            return
        except BaseException as e:
            print(str(e))
