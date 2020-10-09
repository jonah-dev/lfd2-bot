from datetime import datetime
from matchmaking.game_data import Game, GameData, Team
from unittest.mock import AsyncMock, patch
from random import choice, randint
from string import digits
from typing import Callable, List

from aiounittest import AsyncTestCase
from discord import Member, Status, Colour
from discord import TextChannel, VoiceChannel
from discord.ext.commands.bot import Bot

from models.lobby import Lobby
from utils.usage_exception import UsageException
from matchmaking.linear_regression_ranker import get_ranker
from matchmaking.random_shuffler import get_shuffler


def id() -> str:
    return int("".join(choice(digits) for _ in range(10)))


def channel(name: str = "", topic: str = "") -> TextChannel:
    channel = AsyncMock(spec=TextChannel)
    channel.id = id()
    channel.name = name
    channel.topic = topic
    return channel


def vchannel(participants: List[Member]) -> VoiceChannel:
    vchannel = AsyncMock(spec=VoiceChannel)
    vchannel.id = id()
    vchannel.members = participants
    return vchannel


def bot() -> Bot:
    bot = AsyncMock(spec=Bot)
    return bot


def member(status: Status = Status.online) -> Member:
    member = AsyncMock(spec=Member)
    member.id = id()
    member.display_name = id()
    member.bot = None
    member.status = status
    return member


async def game_data(_channel) -> GameData:
    return GameData(
        [
            Game(
                datetime.today(),
                Team([id() for _ in range(4)], randint(1000, 3000)),
                Team([id() for _ in range(4)], randint(1000, 3000)),
            )
            for _ in range(5)
        ]
    )


class TestLobby(AsyncTestCase):
    async def test_add_remove(self):
        lobby = Lobby(bot(), channel())
        await lobby.add(player_one := member())
        assert len(lobby.players) == 1

        await lobby.add(player_two := member(), player_one)
        assert len(lobby.players) == 2

        await lobby.remove(player_one)
        assert len(lobby.players) == 1

        await lobby.remove(player_two)
        assert len(lobby.players) == 0

    async def test_full_lobby(self):
        lobby = Lobby(bot(), channel())
        await lobby.add(member())
        assert not lobby.is_full()
        for _ in range(7):
            await lobby.add(member())
        assert lobby.is_full()

        with self.assertRaises(UsageException):
            await lobby.add(member())

    async def test_leavers(self):
        lobby = Lobby(bot(), channel())
        await lobby.add(author := member())
        await lobby.add(leaver := member(), author)

        # Removal by others does not prevent re-add
        await lobby.remove(leaver, author)
        assert not lobby.has_left_before(leaver)
        await lobby.add(leaver, author)

        # Leaving prevents re-add
        await lobby.remove(leaver)
        with self.assertRaises(UsageException):
            await lobby.add(leaver, author)
        await lobby.add(leaver)

    async def test_ready_unready(self):
        lobby = Lobby(bot(), channel())
        await lobby.add(player := member())

        await lobby.ready(player)
        assert lobby.ready_count() == 1

        await lobby.unready(player)
        assert lobby.ready_count() == 0

        await lobby.remove(player)
        with self.assertRaises(UsageException):
            await lobby.ready(player)
        with self.assertRaises(UsageException):
            await lobby.unready(player)

        await lobby.flyin(player)
        assert lobby.ready_count() == 1

    async def test_lobby_embed(self):
        lobby = Lobby(bot(), channel())
        embed = lobby.get_lobby_message()
        assert embed.footer.text == "There are 8 spots remaining!"
        assert embed.colour == Colour.orange()

        await lobby.add(player := member())
        embed = lobby.get_lobby_message()
        assert embed.footer.text == "There are 7 spots remaining!"
        assert embed.colour == Colour.orange()
        assert len(embed.fields) == 1
        assert embed.fields[0].name == ":x: Not Ready"
        assert str(player.display_name) in embed.fields[0].value

        await lobby.ready(player)
        embed = lobby.get_lobby_message()
        assert embed.footer.text == "There are 7 spots remaining!"
        assert embed.colour == Colour.orange()
        assert len(embed.fields) == 1
        assert embed.fields[0].name == ":white_check_mark: Ready!"
        assert str(player.display_name) in embed.fields[0].value

        for _ in range(7):
            await lobby.flyin(member())
        embed = lobby.get_lobby_message()
        assert embed.footer.text == "This lobby is full!"
        assert embed.colour == Colour.green()
        assert len(embed.fields) == 1
        assert embed.fields[0].name == ":white_check_mark: Ready!"

        await lobby.unready(player)
        embed = lobby.get_lobby_message()
        assert embed.footer.text == "This lobby is full!"
        assert embed.colour == Colour.green()
        assert len(embed.fields) == 2

        await lobby.remove(player)
        embed = lobby.get_lobby_message()
        assert embed.footer.text == "There's one spot remaining!"
        assert embed.colour == Colour.orange()

    async def test_numbers(self):
        discord_bot = bot()
        discord_bot.get_all_channels.return_value = [
            vchannel(participants=[member(), member()]),
            vchannel(participants=[member()]),
        ]

        lobby_channel = channel()
        online = [member() for _ in range(7)]
        offline = [member(status=Status.offline) for _ in range(5)]
        lobby_channel.guild.members = online + offline
        lobby = Lobby(discord_bot, lobby_channel)
        await lobby.add(member())
        await lobby.show_numbers()
        lobby_channel.send.assert_called_with(
            "There's 7 online, 3 in chat, and only 1 in the lobby."
        )

    @patch("matchmaking.game_data.GameData.fetch", game_data)
    async def test_match_combinations(self):
        async def test_with_ordering(order: Callable):
            lobby = Lobby(bot(), channel())
            for _ in range(8):
                await lobby.flyin(member())

            seen = set()
            for _ in range(35):  # 35 times: (8 choose 4) / 2
                (_, (one, two)) = await lobby.get_next_match(order)
                assert (one, two) not in seen
                assert (two, one) not in seen
                seen.add((one, two))
                seen.add((two, one))

            final = await lobby.get_next_match(order)
            assert final is None

        await test_with_ordering(get_shuffler())
        await test_with_ordering(get_ranker(channel()))

    async def test_broadcast(self):
        discord_bot = bot()
        discord_bot.get_all_channels.return_value = [
            lobby_channel := channel(
                name="lobby", topic="@broadcast(#dest1)\n@broadcast(#dest2)"
            ),
            dest_one := channel(name="dest1"),
            dest_two := channel(name="dest2"),
            misc_channel := channel(name="misc"),
        ]

        lobby = Lobby(discord_bot, lobby_channel)
        await lobby.broadcast_game_almost_full()
        assert dest_one.send.call_count == 1
        assert dest_two.send.call_count == 1
        assert misc_channel.send.call_count == 0
