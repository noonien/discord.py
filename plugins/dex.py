from cloudbot import hook
import asyncio
import sys
import requests
import os
from bs4 import BeautifulSoup

@hook.command()
def dex(message, text, nick):
    def_nr = 0
    stext = text.split()

    r = requests.get('https://dexonline.ro/definitie/%s/expandat' % stext[0])
    bf = BeautifulSoup(r.content, "html.parser")
    letters = bf.find_all('div', {'class' : 'defWrapper'})

    if len(stext) > 1:
        try:
            def_nr = int(stext[1])
        except:
            return
        if def_nr < 0 or def_nr >= len(letters):
            message("Cifra trebuie sa fie in [0, %d]" % len(letters))
            return

    if len(letters) == 0:
        message("n-am gasit boss")
        return

    msg = letters[def_nr].find_all('span', {'class' : 'def'})[0].text

    message(msg)
    if len(stext) == 1 and len(letters) > 1:
        message("Sau inca %d definitii disponibile. (.dex cuvant nr_definitie)" % (len(letters) - 1))
