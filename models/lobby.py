from functools import reduce
import asyncio
import re
from typing import Callable, List, Dict, Optional, Tuple
from asyncio.locks import Lock

from discord import Message, File, Embed, Colour
from discord import Member, Status
from discord import VoiceChannel, TextChannel
from discord.ext.commands import Bot

from models.player import Player
from utils.composite import draw_composite
from utils.handle import handle
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
        self.temp_messages: List[Message] = []
        self.show_lobby_lock: Lock = Lock()

    async def add(self, user: Member, author: Optional[Member] = None) -> None:
        if author is not None:
            if not self.has_joined(Player(author)):
                raise UsageException.adder_must_join(self.channel)

            # Other players cannot add you to the lobby
            # if you left on your own. (until lobby reset)
            if self.has_left_before(Player(user)):
                raise UsageException.leaver_not_added(self.channel)

        player = Player(user)
        if self.has_joined(player):
            raise UsageException.already_joined(
                self.channel, author is not None
            )

        self.players.append(player)

        if self.ready_count() == 7:
            await self.broadcast_game_almost_full()

        await self.show(title=f"{player.get_name()} has Joined!")

    async def remove(self, user: Member, author: Optional[Member] = None):
        player = Player(user)
        if player not in self.players:
            raise UsageException.not_in_lobby(self.channel, player)

        if author is None:
            # If a user removes themself, then _others_
            # can't add them back until the lobby resets.
            self.leavers.append(player)

        self.players.remove(player)

        await self.show(title=f"{player.get_name()} has Left")

    async def show(
        self,
        mention: bool = False,
        title: Optional[str] = None,
        temp: bool = True,
    ) -> None:
        await self.show_lobby_lock.acquire()
        try:
            ops = [self.__delMsgSafe(m) for m in self.temp_messages]
            self.temp_messages = []
            if len(ops) > 0:
                await asyncio.wait(ops)

            embed = self.get_lobby_message(title=title, mention=mention)
            msg = await self.channel.send(embed=embed)
            if temp:
                self.temp_messages.append(msg)
        except BaseException as exception:
            await handle(self.channel, exception)
        finally:
            self.show_lobby_lock.release()

    async def show_numbers(self) -> None:
        lobby_count = len(self.players)
        if self.is_ready():
            title = "We got a game!"
        elif lobby_count >= 8:
            title = "I think we got numbers!"
        elif lobby_count == 0:
            title = "We absolutely do **not** have numbers."
        else:
            title = "These are some numbers for sure."

        voice_count = 0
        for channel in self.bot.get_all_channels():
            if isinstance(channel, VoiceChannel):
                voice_count += sum(not m.bot for m in channel.members)

        online_count = 0
        for guild_member in self.channel.guild.members:
            if not (guild_member.bot) and guild_member.status == Status.online:
                online_count += 1

        color = Colour.green() if self.is_ready() else Colour.orange()
        embed = Embed(colour=color)
        embed.title = title
        embed.add_field(name="Online", value=online_count, inline=False)
        embed.add_field(name="In Voice", value=voice_count, inline=False)
        embed.add_field(name="Joined", value=lobby_count, inline=False)
        embed.add_field(name="Ready", value=self.ready_count(), inline=False)
        await self.channel.send(embed=embed)

    async def ready(self, user: Member) -> None:
        player = Player(user)
        if player not in self.players:
            await self.add(user)

        if player.is_ready():
            raise UsageException.already_ready(self.channel)

        if self.is_ready():
            raise UsageException.game_is_full(self.channel)

        ind = self.players.index(player)
        self.players[ind].set_ready()
        self.reset_orderings()

        if self.is_ready():
            title = f"Game Starting in #{self.channel.name}"
            await self.show(title=title, mention=True)
        else:
            await self.show(title=f"{player.get_name()} is Ready!")

    async def unready(self, user: Member) -> None:
        player = Player(user)
        if player not in self.players:
            raise UsageException.join_the_lobby_first(self.channel)

        ind = self.players.index(player)
        self.players[ind].set_unready()
        self.reset_orderings()

        await self.show(title=f"{player.get_name()} is not Ready")

    def get_players(self) -> Tuple[List[Player], List[Player]]:
        ready = []
        alternates = []
        for p in self.players:
            (ready if p.is_ready() else alternates).append(p)

        return ready, alternates

    async def get_next_match(self, order: Callable) -> Optional[Match]:
        if order.__name__ not in self.orderings:
            ready, _ = self.get_players()
            match_finder = await MatchFinder.new(ready, order)
            self.orderings[order.__name__] = match_finder

        return self.orderings[order.__name__].get_next_match()

    async def show_next_match(self, order: Callable) -> None:
        if not self.is_ready():
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

    def get_lobby_message(
        self,
        mention: bool = False,
        title: Optional[str] = None,
    ) -> Embed:
        color = Colour.green() if self.is_ready() else Colour.orange()
        embed = Embed(colour=color)
        embed.title = title or f"Lobby ({len(self.players)})"

        ready, alternates = self.get_players()

        if ready:
            print = "get_mention" if mention else "get_name"
            value = "".join([f"• {(getattr(p, print))()}\n" for p in ready])
            if self.is_ready():
                url = "http://lfd2.zambonihunters.com"
                value = f"{value}[Click here to launch the game]({url})\n"
            embed.add_field(
                name=f"Players ({len(ready)})",
                value=value,
                inline=False,
            )

        if alternates:
            embed.add_field(
                name=f"Alternates ({len(alternates)})",
                value="".join([f"• {p.get_name()}\n" for p in alternates]),
                inline=False,
            )

        remaining_spots = 8 - self.ready_count()
        if remaining_spots == 0:
            text = "Use `?shuffle` or `?ranked` to start building teams.\n"
        elif remaining_spots == 1:
            text = "There's one spot remaining!"
        else:
            text = f"There are {remaining_spots} spots remaining!"

        embed.set_footer(text=text)
        return embed

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

    def is_ready(self) -> bool:
        return self.ready_count() == 8

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

    async def __delMsgSafe(self, msg: Message) -> None:
        try:
            await msg.delete()
        except BaseException as exception:
            await handle(self.channel, exception)
