from functools import reduce
import asyncio
import re
from typing import Callable, List, Dict, Optional

from discord import File, Embed, Colour
from discord import Member, Status
from discord import VoiceChannel, TextChannel
from discord.ext.commands import Bot

from models.player import Player
from utils.composite import draw_composite
from utils.usage_exception import UsageException
from matchmaking.match_finder import MatchFinder, Match
from matchmaking.linear_regression_ranker import get_scores


class Lobby:
    def __init__(self, bot: Bot, channel: TextChannel):
        self.bot = bot
        self.channel: TextChannel = channel
        self.players: List[Player] = []
        self.leavers: List[Player] = []
        self.orderings: Dict[Callable, MatchFinder] = {}

    async def add(self, user: Member, author: Optional[Member] = None) -> None:
        if author is not None:
            if not self.has_joined(Player(author)):
                raise UsageException.adder_must_join(self.channel)

            # Other players cannot add you to the lobby
            # if you left on your own. (until lobby reset)
            if self.has_left_before(Player(user)):
                raise UsageException.leaver_not_added(self.channel)

        if self.is_full():
            raise UsageException.game_is_full(self.channel)

        player = Player(user)
        if self.has_joined(player):
            raise UsageException.already_joined(
                self.channel, author is not None
            )

        self.players.append(player)
        self.reset_orderings()

        if self.ready_count() == 7:
            await self.broadcast_game_almost_full()

        await self.channel.send(f"{player.get_name()} has joined the game!")

    async def remove(self, user: Member, author: Optional[Member] = None):
        player = Player(user)
        if player not in self.players:
            raise UsageException.not_in_lobby(self.channel)

        if author is None:
            # If a user removes themself, then _others_
            # can't add them back until the lobby resets.
            self.leavers.append(player)

        self.players.remove(player)
        self.reset_orderings()

        await self.channel.send(
            f"Succesfully removed: {player.get_name()} from the game."
            + f"\n There are now {str(8 - len(self.players))} spots available"
        )

    async def show_lobby(self) -> None:
        if len(self.players) < 1:
            raise UsageException.empty_lobby(self.channel)

        await self.channel.send(embed=self.get_lobby_message())

    async def show_numbers(self) -> None:
        lobby_count = len(self.players)
        if lobby_count == 8:
            await self.channel.send("I think we got numbers!")
            return

        if lobby_count == 0:
            await self.channel.send("We absolutely do **not** have numbers!")
            return

        voice_count = 0
        for channel in self.bot.get_all_channels():
            if isinstance(channel, VoiceChannel):
                voice_count += sum(not m.bot for m in channel.members)

        online_count = 0
        for guild_member in self.channel.guild.members:
            if not (guild_member.bot) and guild_member.status == Status.online:
                online_count += 1

        if voice_count >= 8:
            return await self.channel.send(
                f"There's {voice_count} in chat but"
                f" only {lobby_count} in the lobby. C'mon!",
            )

        if online_count >= 8:
            return await self.channel.send(
                f"There's {online_count} online and you're"
                f" telling me we only have {lobby_count} in the lobby???",
            )

        await self.channel.send(
            f"There's {online_count} online, {voice_count} in chat,"
            f" and only {lobby_count} in the lobby."
        )

    async def ready(self, user: Member) -> None:
        player = Player(user)
        if player not in self.players:
            raise UsageException.join_the_lobby_first(self.channel)

        if player.is_ready():
            raise UsageException.already_ready(self.channel)

        ind = self.players.index(player)
        self.players[ind].set_ready()
        await self.channel.send(
            f"{player.get_name()} ready!. :white_check_mark:",
        )

    async def unready(self, user: Member) -> None:
        player = Player(user)
        if player not in self.players:
            raise UsageException.join_the_lobby_first(self.channel)

        ind = self.players.index(player)
        self.players[ind].set_unready()
        await self.channel.send(f"{player.get_name()} unreadied!. :x:")

    async def flyin(self, user):
        await self.add(user)
        await self.ready(user)

    async def get_next_match(self, order: Callable) -> Optional[Match]:
        if order not in self.orderings:
            self.orderings[order] = await MatchFinder.new(self.players, order)

        return self.orderings[order].get_next_match()

    async def show_next_match(self, order: Callable) -> None:
        if len(self.players) < 2:
            raise UsageException.not_enough_for_match(self.channel)

        next_match = await self.get_next_match(order)
        if next_match is None:
            raise UsageException.seen_all_matches(self.channel)

        (number, match) = next_match
        (team_one, team_two) = match
        composite = await draw_composite(
            number,
            team_one,
            team_two,
            self.channel.id,
        )
        await self.channel.send(file=File(composite))

    async def show_ranking(self, filter_lobby: bool):
        scores = await get_scores(self.channel)
        scores = scores.items()
        scores = sorted(scores, key=lambda item: item[1], reverse=True)
        embed = Embed(colour=Colour.blurple())
        embed.title = "Lobby Rankings"
        rank = 1
        for user_id, score in scores:
            user = self.bot.get_user(user_id)
            if user is None:
                continue

            if filter_lobby and Player(user) not in self.players:
                continue

            embed.add_field(name=f"{rank}. {user}", value=score, inline=False)
            rank += 1

        if len(embed.fields) == 0:
            embed.add_field(
                name="No players",
                value="No players in the lobby (or channel) have a ranking.",
            )

        await self.channel.send(embed=embed)

    def get_lobby_message(self) -> Embed:
        color = Colour.green() if self.is_full() else Colour.orange()
        embed = Embed(colour=color)
        embed.title = f"Left 4 Dead Lobby ({len(self.players)}/8)"

        if self.ready_count() != 0:
            ready = ""
            for player in self.players:
                if player.is_ready():
                    ready += f"• {player.get_name()}\n"
            embed.add_field(
                name=":white_check_mark: Ready!",
                value=ready,
                inline=False,
            )

        if self.ready_count() != len(self.players):
            not_ready = ""
            for player in self.players:
                if not player.is_ready():
                    not_ready += f"• {player.get_name()}\n"
            embed.add_field(
                name=":x: Not Ready",
                value=not_ready,
                inline=False,
            )

        remaining_spots = 8 - len(self.players)
        if remaining_spots == 0:
            text = "This lobby is full!"
        elif remaining_spots == 1:
            text = "There's one spot remaining!"
        else:
            text = f"There are {remaining_spots} spots remaining!"

        embed.set_footer(text=text)
        return embed

    def is_full(self) -> bool:
        return len(self.players) == 8

    def has_joined(self, player: Player) -> bool:
        return player in self.players

    def has_left_before(self, player) -> bool:
        return player in self.leavers

    def ready_count(self) -> int:
        return reduce(
            lambda a, p: a + 1 if p.is_ready() else a,
            self.players,
            0,
        )

    def reset_orderings(self) -> None:
        self.orderings = {}

    async def broadcast_game_almost_full(self) -> None:
        destinations = self.get_broadcast_channels()
        if not destinations:
            return

        broadcasts = []
        message = self.get_broadcast_message()
        for channel in self.bot.get_all_channels():
            if (
                isinstance(channel, TextChannel)
                and channel.name in destinations
            ):
                broadcasts.append(channel.send(embed=message))

        if broadcasts:
            await asyncio.wait(broadcasts)

    def get_broadcast_channels(self) -> List[TextChannel]:
        if self.channel.topic is None:
            return []

        return re.findall(
            r"^@broadcast\(#([^\s]+)\)", self.channel.topic, re.M
        )

    def get_broadcast_message(self) -> Embed:
        embed = Embed(colour=Colour.orange())
        embed.title = "Left 4 Dead game starting soon!"
        embed.description = (
            "Only one more player is needed for a full lobby.\n"
        )
        for player in self.players:
            embed.description += f"• {player.get_mention()}\n"
        embed.description += f"\nJoin {self.channel.mention} to get involved!"
        return embed
