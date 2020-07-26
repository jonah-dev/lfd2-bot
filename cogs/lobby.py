from models.Player import Player
from discord.ext import commands, tasks
from discord import VoiceChannel, Status
import discord
from datetime import datetime
import random
from time import time
from math import ceil
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import numpy
import io
import datetime
import json
import urllib.request
import os


class Lobby(commands.Cog):

    def __init__(self, bot):
        # pylint: disable=no-member
        self.bot = bot
        self.players = []
        self.isStarted = False
        self.resetShuffles()
        self.janitor.start()
        pass
    
    def cog_unload(self):
        # pylint: disable=no-member
        self.janitor.cancel()

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            colour = discord.Colour.orange()
        )
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
        self.resetShuffles()
        return

    @commands.command()
    async def leave(self, ctx):
        player = Player(ctx.author)
        await self.removeFromLobby(ctx, player)
        self.resetShuffles()
        return

    @commands.command()
    async def lobby(self, ctx):
        if len(self.players):
            await ctx.send(self.getPlayerList())
        else:
            await ctx.send('There are no players in the game')
        return

    @commands.command()
    async def numbers(self, ctx):
        lobbyCount = len(self.players)
        if (lobbyCount == 8):
          await ctx.send('I think we got numbers!')
          return

        voiceCount = 0
        for channel in self.bot.get_all_channels():
          if isinstance(channel, VoiceChannel):
            voiceCount += len(channel.members)
                
        onlineCount = 0
        for member in ctx.message.guild.members:
          if (not(member.bot) and member.status == Status.online):
            onlineCount += 1

        if (voiceCount >= 8):
          await ctx.send(f'There\'s {voiceCount} in chat but only {lobbyCount} in the lobby. C\'mon!')
          return
        
        if (onlineCount >= 8):
          await ctx.send(f'There\'s {onlineCount} online and you\'re telling me we only have {lobbyCount} in the lobby???')
          return

        await ctx.send(f'There\'s {onlineCount} online, {voiceCount} in chat, and only {lobbyCount} in the lobby.')
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
        # Prepare Random Team
        t = self.players.copy()
        seed = self.shuffleSeed + self.shuffleNum
        random.Random(seed).shuffle(t)
        teamSize = ceil(len(t)//2)
        t1 = t[:teamSize]
        t2 = t[teamSize:]

        composite = await self.getTeamComposite(t1, t2)
        composite.save('composite.png')
        await ctx.send(file=discord.File('composite.png'))
        self.shuffleNum += 1

    # Resets the entire lobby
    @commands.command()
    async def reset(self, ctx):
        self.players = []
        self.resetShuffles()
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
                self.resetShuffles()
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

    async def getTeamComposite(self, t1, t2):
        survivors = [
            'coach_small.png',
            'ellis_small.jpeg',
            'nick_small.png',
            'rochelle_small.png'
        ]
        im = Image.open("assets/lobby.png")
        infected_image = Image.open('assets/infected_small.png')
        draw = ImageDraw.Draw(im)
        textPos = (255, 180)
        shufflePos = (10, 10)
        textOffset = 42
        teamOffset = (-72, -11)
        profileOffset = (-29, -3)
        font = ImageFont.truetype("assets/AmazMegaGrungeOne.ttf", 16)
        sFont = ImageFont.truetype("assets/AmazMegaGrungeOne.ttf", 36)

        draw.text(shufflePos, "Shuffle " + str(self.shuffleNum), font=sFont, fill=(81, 81, 81, 255))
        for p in t1:
            # Get survivor image and next image positions
            survivor_image = Image.open('assets/' + survivors.pop())
            profile_image = await p.getAvatar()
            nextTeamPos = tuple(numpy.add(textPos, teamOffset))
            nextProfilePos = tuple(numpy.add(textPos, profileOffset))
            # Write Player Data to Image
            draw.text(textPos, p.getName(), font=font, fill=(81, 81, 81, 255))
            im.paste(survivor_image, nextTeamPos)
            im.paste(profile_image.resize((20,20)), nextProfilePos)
            # Increment text position for next iteration
            textPos = (textPos[0], textPos[1] + textOffset)

        for p in t2:
            # Get survivor image and next image positions
            profile_image = await p.getAvatar()
            nextTeamPos = tuple(numpy.add(textPos, teamOffset))
            nextProfilePos = tuple(numpy.add(textPos, profileOffset))
            # Write Player Data to Image
            draw.text(textPos, p.getName(), font=font, fill=(81, 81, 81, 255))
            im.paste(infected_image, nextTeamPos)
            im.paste(profile_image.resize((20,20)), nextProfilePos)
            # Increment text position for next iteration
            textPos = (textPos[0], textPos[1] + textOffset)

        return im

    def getChannelByName(self, channel_name):
        for channel in self.bot.get_all_channels():
            if channel.name == channel_name:
                return channel
        return None

    def resetLobby(self):
        self.players = []
        self.resetShuffles()

    def resetShuffles(self):
        self.shuffleNum = 1
        self.shuffleSeed = time()

    ######## TASKS ########
    @tasks.loop(seconds=60.0)
    async def janitor(self):
        now = datetime.datetime.now().time()
        resetRangeStart = datetime.time(13)
        resetRangeEnd = datetime.time(13, 1)
        daily_fact = ''
        if (resetRangeStart <= now <= resetRangeEnd):
            channel_name = os.environ['CHANNEL_NAME']
            channel = self.getChannelByName(channel_name)
            with urllib.request.urlopen('https://uselessfacts.jsph.pl/today.json?language=en') as f:
                daily_fact = json.loads(f.read())['text']
            self.resetLobby()
            embed = discord.Embed(colour = discord.Colour.orange())
            embed.set_author(name='Daily Update - ' + str(datetime.date.today()))
            embed.add_field(name='Lobby has been cleared!', value=daily_fact, inline=False)
            if channel:
                await channel.send(embed=embed)


def setup(bot):
    print('Setting up Lobby cog..')
    bot.add_cog(Lobby(bot))

def teardown(bot):
    print('Unloading Lobby cog..')