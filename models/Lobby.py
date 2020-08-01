from discord import VoiceChannel, TextChannel, Status
import discord
import random
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import numpy
import re
import asyncio

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
        
        await self.channel.send(player.getName() + ' has joined the game!')
        return

    async def remove(self, user):
        if len(self.players) == 0:
          await self.channel.send('There are no players in the game')
          return

        player = Player(user)
        if player not in self.players:
          await self.channel.send(f'Player not in lobby: {player.getName()}')
          return

        try:
          self.players = list(filter(lambda x: x != player, self.players))
          await self.channel.send(
            f'Succesfully removed: {player.getName()} from the game.'
            + f'\n There are now {str(8 - len(self.players))} spots available'
          )
        except:
          await self.channel.send(f'Error removing player from lobby: {player.getName()}')

    async def showLobby(self):
        if len(self.players):
            await self.channel.send(self.getPlayerList())
        else:
            await self.channel.send('There are no players in the game')
        return

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
        for member in self.channel.guild.members:
          if (not(member.bot) and member.status == Status.online):
            onlineCount += 1

        if (voiceCount >= 8):
          await self.channel.send(f'There\'s {voiceCount} in chat but only {lobbyCount} in the lobby. C\'mon!')
          return

        if (onlineCount >= 8):
          await self.channel.send(f'There\'s {onlineCount} online and you\'re telling me we only have {lobbyCount} in the lobby???')
          return

        await self.channel.send(f'There\'s {onlineCount} online, {voiceCount} in chat, and only {lobbyCount} in the lobby.')
        return

    async def ready(self, user):
        player = Player(user)
        if not(player in self.players):
            await self.channel.send('You cannot ready if you are not in the lobby')
        if player.isReady():
            await self.channel.send('Player is already ready.')
        else:
            ind = self.players.index(player)
            if ind > -1:
                self.players[ind].setReady()
                await self.channel.send(player.getName() + ' ready!. ' + ':white_check_mark:')
            else:
                await self.channel.send('Cannot find player')
        return

    async def unready(self, user):
        player = Player(user)
        if not(player in self.players):
            await self.channel.send('You cannot unready if you are not in the lobby')
        else:
            ind = self.players.index(player)
            if ind > -1:
                self.players[ind].setUnready()
                await self.channel.send(player.getName() + ' unreadied!. ' + ':x:')
            else:
                await self.channel.send('Cannot find player')

    async def showNewShuffle(self):
        if (len(self.players) < 2):
            await self.channel.send('LFD2 Bot needs at least two players in the lobby to shuffle teams.')
            return
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
        composite = await self.getTeamComposite(t1, t2)
        composite.save('composite.png')
        await self.channel.send(file=discord.File('composite.png'))
        self.shuffleNum += 1

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