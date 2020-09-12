from functools import reduce
from itertools import combinations
from math import ceil
import asyncio
import random
import re
from typing import List, Tuple, Optional

from discord import File, Embed, Colour
from discord import Member, Status
from discord import VoiceChannel, TextChannel
from discord.ext.commands import Bot

from models.player import Player
from utils.Composite import Composite
from utils.UsageException import UsageException


class Lobby:
    def __init__(self, bot: Bot, channel: TextChannel):
        self.bot = bot
        self.channel: TextChannel = channel
        self.players: List[Player] = []
        self.shuffle_num: int = 1
        self.shuffles: Optional[List[Tuple[Player, ...]]] = None

    async def add(self, user: Member) -> None:
        if self.is_full():
            raise UsageException(
                self.channel,
                "Sorry the game is full. Please wait for someone to leave.",
            )

        player = Player(user)
        if self.has_joined(player):
            raise UsageException(
                self.channel, "You are already in the game you pepega."
            )

        self.players.append(player)
        self.reset_shuffles()

        if self.ready_count() == 7:
            await self.broadcast_game_almost_full()

        await self.channel.send(f"{player.getName()} has joined the game!")

    async def remove(self, user: Member) -> None:
        if len(self.players) == 0:
            raise UsageException(self.channel, "There are no players in the game")

        player = Player(user)
        if player not in self.players:
            raise UsageException(
                self.channel, f"Player not in lobby: {player.getName()}"
            )

        self.players.remove(player)
        self.reset_shuffles()

        await self.channel.send(
            f"Succesfully removed: {player.getName()} from the game."
            + f"\n There are now {str(8 - len(self.players))} spots available"
        )

    async def show_lobby(self) -> None:
        if len(self.players) < 1:
            raise UsageException(self.channel, "There are no players in the game")

        await self.channel.send(embed=self.get_lobby_message())

    async def show_numbers(self) -> None:
        lobby_count = len(self.players)
        if lobby_count == 8:
            raise UsageException(self.channel, "I think we got numbers!")

        voice_count = 0
        for channel in self.bot.get_all_channels():
            if isinstance(channel, VoiceChannel):
                voice_count += len(list(filter(lambda m: not (m.bot), channel.members)))

        online_count = 0
        for guild_member in self.channel.guild.members:
            if not (guild_member.bot) and guild_member.status == Status.online:
                online_count += 1

        if voice_count >= 8:
            raise UsageException(
                self.channel,
                f"There's {voice_count} in chat but only {lobby_count} in the lobby. C'mon!",
            )

        if online_count >= 8:
            raise UsageException(
                self.channel,
                f"There's {online_count} online and you're telling me we only have {lobby_count} in the lobby???",
            )

        await self.channel.send(
            f"There's {online_count} online, {voice_count} in chat, and only {lobby_count} in the lobby."
        )

    async def ready(self, user: Member) -> None:
        player = Player(user)
        if player not in self.players:
            raise UsageException(
                self.channel, "You cannot ready if you are not in the lobby"
            )

        if player.isReady():
            raise UsageException(
                self.channel,
                "You're already marked as ready. I can tell you're really excited.",
            )

        ind = self.players.index(player)
        if ind < 0:
            raise UsageException(self.channel, "Cannot find player")

        self.players[ind].setReady()
        await self.channel.send(f"{player.getName()} ready!. :white_check_mark:")

    async def unready(self, user: Member) -> None:
        player = Player(user)
        if player not in self.players:
            raise UsageException(
                self.channel, "You cannot unready if you are not in the lobby"
            )

        ind = self.players.index(player)
        if ind < 0:
            raise UsageException(self.channel, "Cannot find player")

        self.players[ind].setUnready()
        await self.channel.send(f"{player.getName()} unreadied!. :x:")

    async def flyin(self, user):
        self.add(user)
        self.ready(user)

    async def show_new_shuffle(self) -> None:
        if len(self.players) < 2:
            raise UsageException(
                self.channel,
                "LFD2 Bot needs at least two players in the lobby to shuffle teams.",
            )

        if self.shuffles is None:
            self.shuffles = self.get_all_combinations()

        if self.shuffle_num > len(self.shuffles):
            raise UsageException(
                self.channel, "You've already seen all possible shuffles"
            )

        team1 = self.shuffles[self.shuffle_num - 1]
        team2 = tuple(sorted([p for p in self.players if p not in team1]))
        composite = await Composite.make(self, team1, team2)
        await self.channel.send(file=File(composite))
        self.shuffle_num += 1

    def get_lobby_message(self) -> Embed:
        color = Colour.green() if self.is_full() else Colour.orange()
        embed = Embed(colour=color)
        embed.title = f"Left 4 Dead Lobby ({len(self.players)}/8)"

        if self.ready_count() != 0:
            ready = ""
            for player in self.players:
                if player.isReady():
                    ready += f"• {player.getName()}\n"
            embed.add_field(name=":white_check_mark: Ready!", value=ready, inline=False)

        if self.ready_count() != len(self.players):
            not_ready = ""
            for player in self.players:
                if not player.isReady():
                    not_ready += f"• {player.getName()}\n"
            embed.add_field(name=":x: Not Ready", value=not_ready, inline=False)

        embed.set_footer(
            text=f"There are {str(8 - len(self.players))} spots still available!"
        )
        return embed

    def is_full(self) -> bool:
        return len(self.players) == 8

    def has_joined(self, player: Player) -> bool:
        return player in self.players

    def ready_count(self) -> int:
        return reduce(lambda a, p: a + 1 if p.isReady() else a, self.players, 0)

    def reset_shuffles(self) -> None:
        self.shuffle_num = 1
        self.shuffles = None

    def get_all_combinations(self) -> List[Tuple[Player, ...]]:
        team_size = ceil(len(self.players) // 2)
        teams = list()
        for team in combinations(self.players, team_size):
            team = tuple(sorted(team))
            other_team = tuple(sorted([p for p in self.players if p not in team]))
            if team not in teams and other_team not in teams:
                teams.append(team)
        random.shuffle(teams)
        return teams

    async def broadcast_game_almost_full(self) -> None:
        destinations = self.get_broadcast_channels()
        message = self.get_broadcast_message()
        broadcasts = []
        for channel in self.bot.get_all_channels():
            if isinstance(channel, TextChannel) and channel.name in destinations:
                broadcasts.append(channel.send(embed=message))

        if len(broadcasts) > 0:
            await asyncio.wait(broadcasts)

    def get_broadcast_channels(self) -> List[TextChannel]:
        if self.channel.topic is None:
            return []

        return re.findall(r"^\?broadcast #([^\s]+)", self.channel.topic, re.M)

    def get_broadcast_message(self) -> Embed:
        embed = Embed(colour=Colour.orange())
        embed.title = "Left 4 Dead game starting soon!"
        embed.description = "Only one more player is needed for a full lobby.\n"
        for player in self.players:
            embed.description += f"• {player.getMention()}\n"
        embed.description += f"\nJoin {self.channel.mention} to get involved!"
        return embed
