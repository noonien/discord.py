from cloudbot import hook
import markovify
import os
import random

TEXTS_REL_PATH = "plugins/texts/"

MAX_OVERLAP_RATIO = 0.5
MAX_OVERLAP_TOTAL = 10

@hook.command
def shrug(message, text, nick):
    message("¯\_(ツ)_/¯")

@hook.command
def dance(message, text, nick):
    dance = [
            "└@(･◡･)@┐",
            "〈( ^.^)ノ",
            "ヽ(ﾟｰﾟ*ヽ)",
            "ヾ(´〇｀)ﾉ",
            "ヽ(´▽｀)ノ",]
    message(text + ": " + random.choice(dance))

@hook.command
def bitter(message, text, nick):
    message("come play with me, Iazo")

@hook.command
def iazo(message, text, nick):
    message(random.choice(["am treaba", "Ke"]))

@hook.command
def ayy(message, text, nick):
    message("lmao")

@hook.command
def jupi(message, text, nick):
    message("_rs _rs _rs _rs _rs _rs _rssss _rrrss erers Rs ERRES!!!")

@hook.command
def aplauze(message, text, nick):
    message("CLAP CLAP CLAP CLAP CLAP")

@hook.command
def puti(message, text, nick):
    if text != "":
        message(text.split()[0] + ": Puţi!")
    else:
        message(nick + ": Puţi!")

@hook.command
def murmuz():
    with open(TEXTS_REL_PATH + "urmuz.txt", "r") as f:
        content = f.read()

        text_model = markovify.Text(content)
        try:
            return("murmuz: " + text_model.make_sentence(tries=1000,
                max_overlap_total=MAX_OVERLAP_TOTAL,
                max_overlap_ratio=MAX_OVERLAP_RATIO))
        except Exception as e:
            print(e)
            return "pula"

@hook.command
def mtutea():
    with open(TEXTS_REL_PATH + "Tutea.txt", "r", encoding ='ISO-8859-1') as f:
        content = f.read()

        text_model = markovify.Text(content)
        try:
            return("sluțea: " + text_model.make_sentence(tries=1000,
                max_overlap_total = MAX_OVERLAP_TOTAL,
                max_overlap_ratio=MAX_OVERLAP_RATIO))
        except Exception as e:
            print(e)
            return "a murit, mai dă-l in pulă"

@hook.command
def mpuric():
    with open(TEXTS_REL_PATH + "puric.txt", "r") as f:
        content = f.read()

        text_model = markovify.Text(content)
        try:
            return("pulic: " + text_model.make_sentence(tries=1000,
                max_overlap_total=MAX_OVERLAP_TOTAL,
                max_overlap_ratio=MAX_OVERLAP_RATIO))
        except Exception as e:
            print(e)
            return "pula"

@hook.command
def mcioran():
    with open(TEXTS_REL_PATH + "cioran.txt", "r") as f:
        content = f.read()

        text_model = markovify.Text(content)
        try:
            return("ciolan: " + text_model.make_short_sentence(max_chars = 140, tries=10000,
                max_overlap_total=MAX_OVERLAP_TOTAL,
                max_overlap_ratio=MAX_OVERLAP_RATIO))
        except Exception as e:
            return "pula"

@hook.command
def muie(message):
    message("ia muie!")

@hook.command
def cacat(message):
    message("ce cacat")

@hook.command
def cola():
    return "un cola pls!"
