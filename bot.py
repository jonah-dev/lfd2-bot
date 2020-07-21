import discord
import json
import cogs
from discord.ext import commands
from collections import deque
from datetime import datetime
from models.Player import Player
import random
import os

class LFD2Bot(commands.Bot):
    lobbyStarted = False

    cogs = ['cogs.lobby']

    # Init and setup 
    def __init__(self):
        super().__init__(command_prefix='?', description='Organize your LFD2 Games with ease',
            pm_help=None, help_attrs=dict(hidden=False), fetch_offline_members=False)

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if (message.content == 'disconnect' and self.isAdmin(ctx.author)):
            print("disconnecting")
            await self.close()

        if (message.content == 'reload'):
            self.reload_extension('cogs.lobby')

        if (message.content == '?commands'):
            body = '?start - Initializes the lobby \n' + '?join - Joins the lobby \n' + '?leave - Leaves the lobby \n' + '?lobby - View the lobby \n' + '?order66 - Issues a ping that marks the beginning of the game \n' + '?lag - Calculates your current lag \n' + '?ped - FOOTBALL SZN \n' + '?ready - Ready up! \n' + '?unready - Not R! \n'
            await ctx.send('```' + body +  '```')

        # Need to move this into a "funny commands" cog
        if (message.content == '?lag'):
            now = datetime.now()
            lr = dict()
            lr[19,20] = 20
            lr[20,21] = 40
            lr[21,22] = 60
            lr[22,23] = 80
            lr[23,24] = 100
            lr[0,1] = 120
            lr[1,2] = 140
            lr[2,3] = 200
            lr[4,5] = 220
            lr[5,6] = 320
            lr[6,7] = 420
            current_time = int(now.strftime("%H").strip("0"))
            lagVal = None
            for key, value in lr.items():
                low, high = key
                if int(low) <= current_time <= int(high):
                    lagVal = value * (1 + (random.randint(1,5) * .1))
            if lagVal == None:
                await ctx.send('No lag at this current time')
            else:
                await ctx.send('Current lag for ' + Player(ctx.author).getName() + " is: " + str(lagVal) + 'ms')
            return
        
        # Need to move this into a "funny commands" cog
        if (message.content == "?ped"):
            await ctx.send('Current lag for ' + Player(ctx.author).getName() + " is: " + str(0) + 'ms')

        if (message.content == '?start'):
            if self.lobbyStarted:
                await ctx.send('The lobby has already been started')
            self.lobbyStarted = True
            self.load_extension('cogs.lobby')
            await ctx.send('The lobby has been started!')
            return

        if ctx.command is None:
            return

        try:
            await self.invoke(ctx)
        except Exception as e:
            print(e.args)
    
    async def on_command_error(self, ctx, exception):
        print('Exception logged {0}'.format(exception))
        await ctx.send('There was an error with your input.')

    async def on_ready(self):
        print('Logged on as', self.user)

    async def close(self):
        await super().close()

    def run(self):
        try:
            super().run(os.environ['DISCORD_TOKEN'])
        except:
            print("Unexpected error")
            raise
    
    def isAdmin(self, author):
        return author.id in [147788154831634434]

    # Helpers
    def getToken(self):
        return json.load(open('config.json', 'r'))['token']


print('Booting up the bot')
bot = LFD2Bot()
bot.remove_command('help')
print('Bot Initialized at: ' + str(datetime.now()))
bot.run()