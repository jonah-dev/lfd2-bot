from models.Player import Player
from discord.ext import commands
import discord
from datetime import datetime
import random

class Lobby(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.players = []
        self.isStarted = False
        pass

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            colour = discord.Colour.orange()
        )
        embed.set_author(name='Help')
        embed.add_field(name='?join', value='Joins the lobby', inline=False)
        embed.add_field(name='?leave', value='Leaves the lobby', inline=False)
        embed.add_field(name='?lobby', value='Views the lobby', inline=False)
        embed.add_field(name='?order66', value='Executes the order to begin the chaos', inline=False)
        embed.add_field(name='?ready', value='Readies your user', inline=False)
        embed.add_field(name='?unready', value='Unreadies your user', inline=False)
        embed.add_field(name='?shuffle', value='Creates a randomly shuffled set of teams with the given lobby.', inline=False)
        embed.add_field(name='?remove [player]', value='Removes player by tag', inline=False)
        embed.add_field(name='?reset', value='Resets the lobby', inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def join(self, ctx):
        player = Player(ctx.author)
        if self.isFull():
            await ctx.send('Sorry the game is full. Please wait for someone to leave.')
            return
        if self.hasJoined(player):
            await ctx.send('You are already in the game you pepega.')
            return
        self.players.append(player)
        vgChannel = self.bot.get_channel(404134431306285057)
        print(self.readyCount())
        if self.readyCount() == 7:
            await vgChannel.send('@lfd2 Only 1 player until we have a full LFD2 lobby! Join the #lfd2 channel via the #roles')
        await ctx.send(player.getName() + ' has joined the game!')
        return

    @commands.command()
    async def leave(self, ctx):
        player = Player(ctx.author)
        await self.removeFromLobby(ctx, player)
        return

    @commands.command()
    async def lobby(self, ctx):
        if len(self.players):
            await ctx.send(self.getPlayerList())
        else:
            await ctx.send('There are no players in the game')
        return

    @commands.command()
    async def order66(self, ctx):
        if self.isReady():
            message = '@here Game is starting! \n'
            self.isStarted = True
            await ctx.send(message + self.getPlayerList())
        if self.isFull():
            await ctx.send("The game is full but not everyone is ready")
        else:
            await ctx.send('There are not enough players in the game')
        return

    @commands.command()
    async def ready(self, ctx):
        player = Player(ctx.author)
        if not(player in self.players):
            await ctx.send('You cannot ready if you are not in the lobby')
        if player.isReady():
            await ctx.send('Player is already ready.')
        else:
            ind = self.players.index(player)
            if ind > -1:
                self.players[ind].setReady()
                await ctx.send(player.getName() + ' ready!. ' + ':white_check_mark:')
            else:
                await ctx.send('Cannot find player')
        return

    @commands.command()
    async def unready(self, ctx):
        player = Player(ctx.author)
        if not(player in self.players):
            await ctx.send('You cannot unready if you are not in the lobby')
        else:
            ind = self.players.index(player)
            if ind > -1:
                self.players[ind].setUnready()
                await ctx.send(player.getName() + ' unreadied!. ' + ':x:')
            else:
                await ctx.send('Cannot find player')

    @commands.command()
    async def shuffle(self, ctx):
        if (len(self.players) < 2):
            await ctx.send('LFD2 Bot needs at least two players in the lobby to shuffle teams.')
            return
        msg = ''
        # Prepare Random Team
        t = self.players.copy()
        random.shuffle(t)
        t1 = []
        t2 = []
        while(len(t) != 0):
            t1.append(t.pop())
            if len(t) == 0:
                break
            t2.append(t.pop())
        if len(t1) and len(t2):    
            msg += "----- Team 1 -----" + "\n"
            msg += self.getTeamList(t1)
            msg += "----- Team 2 -----" + "\n"
            msg += self.getTeamList(t2)
            await ctx.send(msg)

    # Resets the entire lobby
    @commands.command()
    async def reset(self, ctx):
        self.players = []
        await ctx.send('Lobby has been cleared')

    @commands.command()
    async def remove(self, ctx, member: discord.Member):
        await self.removeFromLobby(ctx, Player(member))
        pass

    # ---- HELPERS ----
    async def removeFromLobby(self, ctx, player):
        if len(self.players) == 0:
            await ctx.send('There are no players in the game')
        if player in self.players:
            try:
                self.players = list(filter(lambda x: x != player, self.players))
            except:
                await ctx.send('Error removing player from lobby: ' + player.getName())
                pass
            else:
                await ctx.send('Succesfully removed: ' + player.getName() + ' from the game. \n There are now ' + str(8 - len(self.players)) + ' spots available')
        else:
            await ctx.send('Player not in lobby: ' + player.getName())

    # Gets string to display team
    def getTeamList(self, team):
        msg = ''
        for t in team:
            msg += t.getName() + "\n"
        return msg

    def getPlayerList(self):
        message = '---- Players ---- \n'
        for p in self.players:
            message = message + p.getName() + (': :white_check_mark:' if p.isReady() else ': :x:') + '\n'
        message = message + 'There are now ' + str(8 - len(self.players)) + ' spots available'
        return message

    def isFull(self):
        return  len(self.players) == 8
    
    def isReady(self):
        return self.isFull() and self.readyCount() == 8

    def hasJoined(self, player):
        return player in self.players

    def readyCount(self):
        count = 0
        for p in self.players:
            print(p)
            if p.isReady():
                count+=1
        return count

def setup(bot):
    print('Setting up Setup cog..')
    bot.add_cog(Lobby(bot))

def teardown(bot):
    print('Unloading Setup cog..')