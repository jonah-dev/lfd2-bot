from typing import List, Tuple, Optional
from discord import VoiceChannel, TextChannel, Status
from discord.ext.commands import command, Cog, Bot, Context
import discord
import random
import re
import asyncio
from math import ceil
from functools import reduce
from itertools import combinations 

from models.Player import Player
from utils.Composite import Composite
from utils.UsageException import UsageException

class Lobby:

    def __init__(self, bot: Bot, channel: TextChannel):
        self.bot = bot
        self.channel: TextChannel = channel
        self.players: List[Player] = []
        self.leavers: List[Player] = []
        self.shuffleNum: int = 1
        self.shuffles: Optional[List[Tuple[Player, ...]]] = None
        pass

    async def add(self, user: discord.member, author: Optional[discord.member]=None) -> None:
        if author is not None:
          if (not self.hasJoined(Player(author))):
            raise UsageException(self.channel, 'You must be in the lobby to add other players.')
          
          # Other players cannot add you to the lobby
          # if you left on your own. (until lobby reset) 
          if (self.hasLeftBefore(Player(user))):
            raise UsageException(self.channel, 'This player has recently left the lobby and cannot be added back by other players.')

        if self.isFull():
          raise UsageException(self.channel, 'Sorry the game is full. Please wait for someone to leave.')

        player = Player(user)
        if self.hasJoined(player):
          raise UsageException(self.channel, 'You are already in the game you pepega.')

        self.players.append(player)
        self.resetShuffles()

        if self.readyCount() == 7:
          await self.broadcastGameAlmostFull()
        
        await self.channel.send(f'{player.getName()} has joined the game!')
    
    async def remove(self, user: discord.member, author: Optional[discord.member]=None) -> None:
        if len(self.players) == 0:
          raise UsageException(self.channel, 'There are no players in the game')

        player = Player(user)
        if player not in self.players:
          raise UsageException(self.channel, f'Player not in lobby: {player.getName()}')
        
        if author is None:
          # If a user removes themself, then _others_
          # can't add them back until the lobby resets. 
          self.leavers.append(player)

        self.players.remove(player)
        self.resetShuffles()

        await self.channel.send(
          f'Succesfully removed: {player.getName()} from the game.'
          + f'\n There are now {str(8 - len(self.players))} spots available'
        )

    async def showLobby(self) -> None:
        if len(self.players) < 1:
          raise UsageException(self.channel, 'There are no players in the game')
        
        await self.channel.send(embed=self.getLobbyMessage())

    async def showNumbers(self) -> None:
        lobbyCount = len(self.players)
        if (lobbyCount == 8):
          raise UsageException(self.channel, 'I think we got numbers!')

        voiceCount = 0
        for channel in self.bot.get_all_channels():
          if isinstance(channel, VoiceChannel):
            voiceCount += len(list(filter(lambda m: not(m.bot), channel.members)))

        onlineCount = 0
        for member in self.channel.guild.members:
          if (not(member.bot) and member.status == Status.online):
            onlineCount += 1

        if (voiceCount >= 8):
          raise UsageException(self.channel, f'There\'s {voiceCount} in chat but only {lobbyCount} in the lobby. C\'mon!')

        if (onlineCount >= 8):
          raise UsageException(self.channel, f'There\'s {onlineCount} online and you\'re telling me we only have {lobbyCount} in the lobby???')

        await self.channel.send(f'There\'s {onlineCount} online, {voiceCount} in chat, and only {lobbyCount} in the lobby.')

    async def ready(self, user: discord.member) -> None:
        player = Player(user)
        if not(player in self.players):
          raise UsageException(self.channel, 'You cannot ready if you are not in the lobby')
        
        if player.isReady():
          raise UsageException(self.channel, 'You\'re already marked as ready. I can tell you\'re really excited.')
        
        ind = self.players.index(player)
        if ind < 0:
          raise UsageException(self.channel, 'Cannot find player')

        self.players[ind].setReady()
        await self.channel.send(f'{player.getName()} ready!. :white_check_mark:')

    async def unready(self, user: discord.member) -> None:
        player = Player(user)
        if not(player in self.players):
          raise UsageException(self.channel, 'You cannot unready if you are not in the lobby')
        
        ind = self.players.index(player)
        if ind < 0:
          raise UsageException(self.channel, 'Cannot find player')

        self.players[ind].setUnready()
        await self.channel.send(f'{player.getName()} unreadied!. :x:')
    
    async def flyin(self, user):
        self.add(user)
        self.ready(user)

    async def showNewShuffle(self) -> None:
        if (len(self.players) < 2):
          raise UsageException(self.channel, 'LFD2 Bot needs at least two players in the lobby to shuffle teams.')

        if self.shuffles is None:
          self.shuffles = self.getAllCombinations()

        if self.shuffleNum > len(self.shuffles):
          raise UsageException(self.channel, 'You\'ve already seen all possible shuffles')

        team1 = self.shuffles[self.shuffleNum - 1]
        team2 = tuple(sorted([p for p in self.players if p not in team1]))
        composite = await Composite.make(self, team1, team2)
        await self.channel.send(file=discord.File(composite))
        self.shuffleNum += 1

    def getLobbyMessage(self) -> discord.Embed:
        color = discord.Colour.green() if self.isFull() else discord.Colour.orange()
        embed = discord.Embed(colour=color)
        embed.title = f'Left 4 Dead Lobby ({len(self.players)}/8)'

        if self.readyCount() != 0:
          ready = ''
          for player in self.players:
            if player.isReady():
              ready += f'• {player.getName()}\n'
          embed.add_field(name=":white_check_mark: Ready!", value=ready, inline=False)

        if self.readyCount() != len(self.players):
          notReady = ''
          for player in self.players:
            if not(player.isReady()):
              notReady += f'• {player.getName()}\n'
          embed.add_field(name=":x: Not Ready", value=notReady, inline=False)

        embed.set_footer(text=f'There are {str(8 - len(self.players))} spots still available!')
        return embed

    def isFull(self) -> bool:
        return len(self.players) == 8

    def hasJoined(self, player: Player) -> bool:
        return player in self.players
    
    def hasLeftBefore(self, player):
        return player in self.leavers

    def readyCount(self) -> int:
        return reduce(lambda a, p: a+1 if p.isReady() else a, self.players, 0)
    
    def resetShuffles(self) -> None:
        self.shuffleNum = 1
        self.shuffles = None

    def getAllCombinations(self) -> List[Tuple[Player, ...]]:
        teamSize = ceil(len(self.players) // 2)
        teams = list()
        for team in combinations(self.players, teamSize):
          team = tuple(sorted(team))
          otherTeam = tuple(sorted([p for p in self.players if p not in team]))
          if (team not in teams and otherTeam not in teams):
            teams.append(team)
        random.shuffle(teams)
        return teams

    async def broadcastGameAlmostFull(self) -> None:
        destinations = self.getBroadcastChannels()
        message = self.getBroadcastMessage()
        broadcasts = []
        for channel in self.bot.get_all_channels():
          if isinstance(channel, TextChannel) and channel.name in destinations:
            broadcasts.append(channel.send(embed=message))

        if len(broadcasts) > 0:
          await asyncio.wait(broadcasts)
    
    def getBroadcastChannels(self) -> List[TextChannel]:
        if self.channel.topic is None:
          return []

        return re.findall(r"^\?broadcast #([^\s]+)", self.channel.topic, re.M)

    def getBroadcastMessage(self) -> discord.Embed:
        embed = discord.Embed(colour = discord.Colour.orange())
        embed.title = 'Left 4 Dead game starting soon!'
        embed.description = 'Only one more player is needed for a full lobby.\n'
        for player in self.players:
          embed.description += f'• {player.getMention()}\n'
        embed.description += f'\nJoin {self.channel.mention} to get involved!'
        return embed