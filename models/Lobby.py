from discord import VoiceChannel, TextChannel, Status
import discord
import random
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import numpy
import re
import asyncio
from math import ceil

from models.Player import Player

class Lobby:

    def __init__(self, bot, channel):
        # pylint: disable=no-member
        self.bot = bot
        self.channel = channel
        self.players = []
        self.shuffleNum = 1
        pass

    async def add(self, user):
        if self.isFull():
          await self.channel.send('Sorry the game is full. Please wait for someone to leave.')
          return

        player = Player(user)
        if self.hasJoined(player):
          await self.channel.send('You are already in the game you pepega.')
          return

        self.players.append(player)

        if self.readyCount() == 7:
          await self.broadcastGameAlmostFull()
        
        await self.channel.send(f'{player.getName()} has joined the game!')

    async def remove(self, user):
        if len(self.players) == 0:
          await self.channel.send('There are no players in the game')
          return

        player = Player(user)
        if player not in self.players:
          await self.channel.send(f'Player not in lobby: {player.getName()}')
          return

        self.players.remove(player)
        await self.channel.send(
          f'Succesfully removed: {player.getName()} from the game.'
          + f'\n There are now {str(8 - len(self.players))} spots available'
        )

    async def showLobby(self):
        if len(self.players):
          await self.channel.send(self.getPlayerList())
          return

        await self.channel.send('There are no players in the game')

    async def showNumbers(self):
        lobbyCount = len(self.players)
        if (lobbyCount == 8):
          await self.channel.send('I think we got numbers!')
          return

        voiceCount = 0
        for channel in self.bot.get_all_channels():
          if isinstance(channel, VoiceChannel):
            voiceCount += len(channel.members)

        onlineCount = 0
        for member in self.channel.message.guild.members:
          if (not(member.bot) and member.status == Status.online):
            onlineCount += 1

        if (voiceCount >= 8):
          await self.channel.send(f'There\'s {voiceCount} in chat but only {lobbyCount} in the lobby. C\'mon!')
          return

        if (onlineCount >= 8):
          await self.channel.send(f'There\'s {onlineCount} online and you\'re telling me we only have {lobbyCount} in the lobby???')
          return

        await self.channel.send(f'There\'s {onlineCount} online, {voiceCount} in chat, and only {lobbyCount} in the lobby.')

    async def ready(self, user):
        player = Player(user)
        if not(player in self.players):
          await self.channel.send('You cannot ready if you are not in the lobby')
          return
        
        if player.isReady():
          await self.channel.send('You\'re already marked as ready. I can tell you\'re really excited.')
          return
        
        ind = self.players.index(player)
        if ind < 0:
          await self.channel.send('Cannot find player')
          return

        self.players[ind].setReady()
        await self.channel.send(f'{player.getName()} ready!. :white_check_mark:')

    async def unready(self, user):
        player = Player(user)
        if not(player in self.players):
          await self.channel.send('You cannot unready if you are not in the lobby')
          return
        
        ind = self.players.index(player)
        if ind < 0:
          await self.channel.send('Cannot find player')

        self.players[ind].setUnready()
        await self.channel.send(f'{player.getName()} unreadied!. :x:')

    async def showNewShuffle(self):
        if (len(self.players) < 2):
          await self.channel.send('LFD2 Bot needs at least two players in the lobby to shuffle teams.')
          return

        (t1, t2) = self.makeNewShuffle()
        composite = await self.getTeamComposite(t1, t2)
        composite.save('composite.png')
        await self.channel.send(file=discord.File('composite.png'))
        self.shuffleNum += 1

    def getPlayerList(self):
        message = '---- Players ---- \n'
        for p in self.players:
          ready = ':white_check_mark:' if p.isReady() else ':x:'
          message += f'{p.getName()} {ready}\n'
        message += f'There are now {str(8 - len(self.players))} spots available'
        return message

    def isFull(self):
        return len(self.players) == 8

    def hasJoined(self, player):
        return player in self.players

    def readyCount(self):
        return reduce(lambda a, p: a+1 if p.isReady() else a, self.players, 0)

    def makeNewShuffle(self):
        t = self.players.copy()
        random.shuffle(t)
        teamSize = ceil(len(t) // 2)
        return t[:teamSize], t[teamSize:]

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

    async def broadcastGameAlmostFull(self):
        destinations = self.getBroadcastChannels()
        message = self.getBroadcastMessage()
        broadcasts = []
        for channel in self.bot.get_all_channels():
          if isinstance(channel, TextChannel) and channel.name in destinations:
            broadcasts.append(channel.send(embed=message))

        if len(broadcasts) > 0:
          await asyncio.wait(broadcasts)
    
    def getBroadcastChannels(self):
        if self.channel.topic is None:
          return []

        return re.findall(r"^\?broadcast #([^\s]+)", self.channel.topic, re.M)

    def getBroadcastMessage(self):
        embed = discord.Embed(colour = discord.Colour.orange())
        embed.title = 'Left 4 Dead game starting soon!'
        embed.description = 'Only one more player is needed for a full lobby.\n'
        for player in self.players:
          embed.description += f'• {player.getMention()}\n'
        embed.description += f'\nJoin {self.channel.mention} to get involved!'
        return embed