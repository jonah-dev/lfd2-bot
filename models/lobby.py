from functools import reduce
import asyncio
from asyncio.locks import Lock
from random import shuffle

from typing import List, Dict, Optional, Tuple

from discord import Message, Embed, Colour
from discord import Member, TextChannel
from discord.ext.commands import Bot
from discord.ext.commands.core import Command

from models.config import Config
from models.player import Player
from utils.handle import handle
from utils.usage_exception import UsageException
from utils.verses import Verses


class Lobby:
    def __init__(self, bot: Bot, channel: TextChannel):
        self.bot = bot
        self.channel: TextChannel = channel
        self.plugin_commands: Dict[str, Command] = {}
        self.c: Config = Config(channel, bot, self.installCommands)
        self.players: List[Player] = []
        self.leavers: List[Player] = []
        self.temp_messages: dict[str, List[Message]] = {}
        self.locks: Dict[str, Lock] = {}
        self._cache = {}

    # -- Plugins --------------------------------------------------------------

    def installCommands(self, command: Command):
        invoked_with = f"?{command.name}"
        if invoked_with in self.plugin_commands:
            self.c.issue(
                f"Duplicate plugin command: `?{invoked_with}`", skip_frames=2
            )
            return

        self.plugin_commands[invoked_with] = command

    # -- Operations -----------------------------------------------------------

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

        if not self.has_open_spots():
            raise UsageException.no_overflow(self.channel)

        self.players.append(player)

        await self.show(desc=f"{player.get_name()} has Joined!")

    async def remove(self, user: Member, author: Optional[Member] = None, rage=False):
        player = Player(user)
        if player not in self.players:
            raise UsageException.not_in_lobby(self.channel, player)

        if author is None:
            # If a user removes themself, then _others_
            # can't add them back until the lobby resets.
            self.leavers.append(player)

        await self.unready(user)
        self.players.remove(player)

        if not rage:
            await self.show(desc=f"{player.get_name()} has Left")
        else:
            await self.show(desc=f"{player.get_name()} says see ya jerks")

    async def show(
        self,
        *,
        mention: bool = False,
        desc: Optional[str] = None,
        temp: bool = True,
    ) -> None:
        embed = self.get_lobby_message(
            mention=mention,
            desc=desc,
        )
        await self.__replaceMessage("lobby", embed, temp)

    async def ready(self, user: Member) -> None:
        player = Player(user)
        if player not in self.players:
            await self.add(user)

        if player.is_ready():
            raise UsageException.already_ready(self.channel)

        if self.is_full():
            raise UsageException.game_is_full(self.channel)

        was_ready = self.is_ready()

        ind = self.players.index(player)
        self.players[ind].set_ready()
        self.clear_cache()

        if self.c.vMax is not None and self.ready_count() == self.c.vMax - 1:
            await self.broadcast_game_almost_full()

        if not was_ready and self.is_ready():
            await self.show(mention=True, desc="The lobby is now ready!")
        else:
            await self.show(desc=f"{player.get_name()} is Ready!")

    async def unready(self, user: Member) -> None:
        player = Player(user)
        if player not in self.players:
            raise UsageException.join_the_lobby_first(self.channel)

        ind = self.players.index(player)
        player = self.players[ind]
        if player.is_ready():
            player.set_unready()
            self.clear_cache()

        await self.show(desc=f"{player.get_name()} is not Ready")

    def get_players(self) -> Tuple[List[Player], List[Player]]:
        ready = []
        alternates = []
        for p in self.players:
            (ready if p.is_ready() else alternates).append(p)

        return ready, alternates

    async def show_next_shuffle(self) -> None:
        if not self.is_ready():
            raise UsageException.not_enough_for_match(self.channel)

        if "shuffles" not in self._cache:
            matches = self.get_matches()
            shuffle(matches)
            self._cache["shuffles"] = iter(enumerate(matches))

        next_match = next(self._cache["shuffles"], None)
        if next_match is None:
            raise UsageException.seen_all_matches(self.channel)

        (number, match) = next_match
        embed = Embed(colour=Colour.teal())
        embed.title = f"Shuffle {number+1}"
        for i, team in enumerate(match):
            players = "".join([f"• {p.get_name()}\n" for p in team])
            players = players if players else "(empty)"
            embed.add_field(name=f"Team {i+1}", value=players, inline=False)
        await self.channel.send(embed=embed)

    async def show_config(self) -> None:
        embed = self.c.describe()
        await self.__replaceMessage("config", embed)

    def get_lobby_message(
        self,
        *,
        mention: bool = False,
        desc: Optional[str] = None,
    ) -> Embed:
        color = Colour.green() if self.is_ready() else Colour.orange()
        embed = Embed(colour=color)
        embed.set_author(name=self.c.vName, icon_url=self.c.vIcon or "")
        embed.description = desc

        ready, alternates = self.get_players()
        if ready:
            print = "get_mention" if mention else "get_name"
            value = "".join([f"• {(getattr(p, print))()}\n" for p in ready])
            if self.is_ready() and self.c.vLaunch:
                value = f"{value}Launch: {self.c.vLaunch}\n"
            embed.add_field(
                name=f"Players ({len(ready)})",
                value=value,
                inline=False,
            )

        others = "Alternates" if self.c.vOverflow else "Not Ready"
        if alternates:
            embed.add_field(
                name=f"{others} ({len(alternates)})",
                value="".join([f"• {p.get_name()}\n" for p in alternates]),
                inline=False,
            )

        game_ready = ""
        if self.c.vMin is not None and self.ready_count() >= self.c.vMin:
            game_ready = "Game ready. "
        can_join = ""
        if not self.is_full():
            can_join = "More players can join."
        elif self.has_open_spots():
            can_join = "More alternates can join."
        embed.set_footer(text=f"{game_ready}{can_join}")

        return embed

    async def ping_alternates(self):
        _, alternates = self.get_players()
        embed = Embed(colour=Colour.red())
        embed.title = "Looking for Players"
        lobby_name = f"{self.c.vName} ({len(self.players)})"
        embed.set_author(name=lobby_name)
        value = "".join([f"• {p.get_mention()}\n" for p in alternates])
        embed.add_field(name="Are you ready to play?", value=value)
        embed.set_footer(text="Use `?ready` to ready-up!")
        await self.channel.send(embed=embed)

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

    def has_open_spots(self) -> bool:
        if self.c.vOverflow:
            return True

        return len(self.players) < self.c.vMax

    def is_full(self) -> bool:
        if self.c.vMax is None:
            return False

        return self.ready_count() >= self.c.vMax

    def is_ready(self) -> bool:
        if self.c.vMin is None:
            return True

        return self.ready_count() >= self.c.vMin

    def get_matches(self) -> List:
        players, _alternates = self.get_players()
        matches = set()
        Verses(None, tuple(), players, self.c.vTeams, matches)
        return list(matches)

    def clear_cache(self) -> None:
        self._cache = {}

    async def broadcast_game_almost_full(self) -> None:
        destinations = self.c.vBroadcastChannels
        if not destinations:
            return

        async def trySend(channel, message):
            try:
                await channel.send(embed=message)
            except Exception:
                pass

        broadcasts = []
        desc = f"Game Almost Full in {self.c.vName} Lobby!"
        message = self.get_lobby_message(desc=desc)
        for dest in destinations:
            broadcasts.append(trySend(dest, message))

        if broadcasts:
            await asyncio.wait(broadcasts)

    async def __replaceMessage(
        self, type: str, embed: Embed, is_temp: bool = True
    ):
        if type not in self.locks:
            self.locks[type] = Lock()

        if type not in self.temp_messages:
            self.temp_messages[type] = []

        await self.locks[type].acquire()
        try:
            ops = [self.__delMsgSafe(m) for m in self.temp_messages[type]]
            self.temp_messages[type] = []
            if len(ops) > 0:
                await asyncio.wait(ops)

            msg = await self.channel.send(embed=embed)
            if is_temp:
                self.temp_messages[type].append(msg)
        except BaseException as exception:
            await handle(self.channel, exception)
        finally:
            self.locks[type].release()

    async def __delMsgSafe(self, msg: Message) -> None:
        try:
            await msg.delete()
        except BaseException as exception:
            await handle(self.channel, exception)
