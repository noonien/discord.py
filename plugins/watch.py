from cloudbot import hook

counter = 0

@hook.on_start()
def init():
    print("on start")

@hook.periodic(20, initial_interval = 20)
def checker(bot):
    global counter
    print("ctr " + str(counter))
    counter += 1
