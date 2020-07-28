from discord.ext import commands, tasks
import discord
from datetime import datetime
import json
import urllib.request

from models.Lobby import Lobby

def setup(bot):
    print('Setting up Lobby cog..')
    bot.add_cog(LobbyCommands(bot))

def teardown(bot):
    print('Unloading Lobby cog..')

class LobbyCommands(commands.Cog):

    def __init__(self, bot):
        # pylint: disable=no-member
        self.bot = bot
        self.lobbies = {}
        self.janitor.start()
        pass
    
    def cog_unload(self):
        # pylint: disable=no-member
        self.janitor.cancel()
    
    # -------- Helpers --------

    async def getLobbyThen(self, ctx, fn):
        if ctx.channel.id in self.lobbies:
          self.lobbies[ctx.channel.id].channel = ctx.channel
          return await fn(self.lobbies[ctx.channel.id])

        await ctx.send('You haven\'t started a lobby. Use `?start` to open a new lobby.')

    # -------- Commands --------

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(colour = discord.Colour.orange())
        embed.set_author(name='Help')
        embed.add_field(name='?join', value='Joins the lobby', inline=False)
        embed.add_field(name='?leave', value='Leaves the lobby', inline=False)
        embed.add_field(name='?lobby', value='Views the lobby', inline=False)
        embed.add_field(name='?ready', value='Readies your user', inline=False)
        embed.add_field(name='?unready', value='Unreadies your user', inline=False)
        embed.add_field(name='?shuffle', value='Creates a randomly shuffled set of teams with the given lobby.', inline=False)
        embed.add_field(name='?remove [player]', value='Removes player by tag', inline=False)
        embed.add_field(name='?reset', value='Resets the lobby', inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def start(self, ctx):
      if ctx.channel.id in self.lobbies:
        await ctx.send('The lobby has already been started. You can restart the lobby with `?reset`.')
        return

      self.lobbies[ctx.channel.id] = Lobby(self.bot, ctx.channel)
      await ctx.send('The lobby has been started!')

    @commands.command()
    async def join(self, ctx):
        await self.getLobbyThen(ctx, lambda lobby: lobby.add(ctx.author))

    @commands.command()
    async def leave(self, ctx):
        await self.getLobbyThen(ctx, lambda lobby: lobby.remove(ctx.author))

    @commands.command()
    async def remove(self, ctx, member: discord.Member):
        await self.getLobbyThen(ctx, lambda lobby: lobby.remove(member))

    @commands.command()
    async def ready(self, ctx):
        await self.getLobbyThen(ctx, lambda lobby: lobby.ready(ctx.author))

    @commands.command()
    async def unready(self, ctx):
        await self.getLobbyThen(ctx, lambda lobby: lobby.unready(ctx.author))

    @commands.command()
    async def numbers(self, ctx):
        await self.getLobbyThen(ctx, lambda lobby: lobby.showNumbers())

    @commands.command()
    async def lobby(self, ctx):
        await self.getLobbyThen(ctx, lambda lobby: lobby.showLobby())

    @commands.command()
    async def shuffle(self, ctx):
        await self.getLobbyThen(ctx, lambda lobby: lobby.showNewShuffle())

    @commands.command()
    async def reset(self, ctx):
        created = 'reset' if ctx.channel.id in self.lobbies else 'started'
        self.lobbies[ctx.channel.id] = Lobby(self.bot, ctx.channel)
        await ctx.send(f'The lobby has been {created}!')

    # -------- Tasks --------

    @tasks.loop(seconds=60.0)
    async def janitor(self):
        now = datetime.now().time()
        resetRangeStart = datetime.time(13)
        resetRangeEnd = datetime.time(13, 1)
        if resetRangeStart <= now <= resetRangeEnd:
          daily_fact = self.getTodaysUselessFact()
          for lobby in self.lobbies:
            self.lobbies[lobby.channel.id] = Lobby(lobby.channel, self.bot)
            embed = discord.Embed(colour = discord.Colour.orange())
            embed.set_author(name=f'Daily Update - {str(datetime.date.today())}')
            embed.add_field(name='Lobby has been cleared!', value=daily_fact, inline=False)
            await lobby.channel.send(embed=embed)

    def getTodaysUselessFact(self):
        req = urllib.request.urlopen('https://uselessfacts.jsph.pl/today.json?language=en')
        return json.loads(req.read())['text']

