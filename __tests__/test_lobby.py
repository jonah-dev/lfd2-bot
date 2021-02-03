from aiounittest import AsyncTestCase
from unittest.mock import AsyncMock, Mock
from random import choice
from string import digits

from typing import List

from discord import Member, Status, Colour
from discord import TextChannel, VoiceChannel
from discord.ext.commands.bot import Bot
from discord.embeds import Embed

from models.lobby import Lobby
from utils.usage_exception import UsageException


def id() -> str:
    return int("".join(choice(digits) for _ in range(10)))


def channel(name: str = "", topic: str = "") -> TextChannel:
    channel = AsyncMock(spec=TextChannel)
    channel.id = id()
    channel.name = name
    channel.topic = topic
    channel.mention = id()
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
    member.mention = id()
    member.bot = None
    member.status = status
    return member


def embed(self, mention: bool = False, title: str = None) -> Embed:
    embed = AsyncMock(Embed)
    return embed


class TestLobby(AsyncTestCase):
    async def test_add_remove(self):
        topic = "@players(min: 8)"
        lobby = Lobby(bot(), channel(topic=topic))
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
        topic = "@players(min: 8, max: 8)"
        lobby = Lobby(bot(), channel(topic=topic))
        await lobby.ready(first := member())
        assert not lobby.is_ready()
        for _ in range(7):
            await lobby.ready(member())
        assert lobby.is_ready()

        await lobby.add(alternate := member())
        with self.assertRaises(UsageException):
            await lobby.ready(alternate)

        await lobby.remove(first)
        assert not lobby.is_ready()

        await lobby.ready(alternate)
        assert lobby.is_ready()

        with self.assertRaises(UsageException):
            await lobby.ready(first)

    async def test_leavers(self):
        topic = "@players(min: 8)"
        lobby = Lobby(bot(), channel(topic=topic))
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
        topic = "@players(min: 8)"
        lobby = Lobby(bot(), channel(topic=topic))
        await lobby.add(player := member())

        await lobby.ready(player)
        assert lobby.ready_count() == 1

        await lobby.unready(player)
        assert lobby.ready_count() == 0

        await lobby.remove(player)

        await lobby.ready(player)
        assert lobby.ready_count() == 1

        await lobby.unready(player)
        assert lobby.ready_count() == 0

        await lobby.ready(player)
        assert lobby.ready_count() == 1

    async def test_lobby_embed(self):
        topic = """
            @name(foo)
            @players(min: 8)
        """
        lobby = Lobby(bot(), channel(topic=topic))
        embed = lobby.get_lobby_message()
        assert embed.title == "foo Lobby: (0)"
        assert embed.footer.text == "More players can join."
        assert embed.colour == Colour.orange()

        await lobby.add(player := member())
        embed = lobby.get_lobby_message()
        assert embed.title == "foo Lobby: (1)"
        assert embed.footer.text == "More players can join."
        assert embed.colour == Colour.orange()
        assert len(embed.fields) == 1
        assert embed.fields[0].name == "Alternates (1)"
        assert embed.fields[0].value.count("\n") == 1
        assert str(player.display_name) in embed.fields[0].value

        embed = lobby.get_lobby_message(mention=True)
        assert str(player.display_name) in embed.fields[0].value

        await lobby.ready(player)
        embed = lobby.get_lobby_message()
        assert embed.title == "foo Lobby: (1)"
        assert embed.footer.text == "More players can join."
        assert embed.colour == Colour.orange()
        assert len(embed.fields) == 1
        assert embed.fields[0].name == "Players (1)"
        assert str(player.display_name) in embed.fields[0].value
        assert embed.fields[0].value.count("\n") == 1

        embed = lobby.get_lobby_message(mention=True)
        assert str(player.mention) in embed.fields[0].value

        for _ in range(7):
            await lobby.ready(member())
        embed = lobby.get_lobby_message()
        assert embed.title == "foo Lobby: (8)"
        assert embed.footer.text == "Game ready. More players can join."
        assert embed.colour == Colour.green()
        assert len(embed.fields) == 1
        assert embed.fields[0].name == "Players (8)"
        assert embed.fields[0].value.count("\n") == 8

        await lobby.unready(player)
        embed = lobby.get_lobby_message()
        assert embed.title == "foo Lobby: (8)"
        assert embed.footer.text == "More players can join."
        assert embed.colour == Colour.orange()
        assert len(embed.fields) == 2
        assert embed.fields[0].name == "Players (7)"
        assert embed.fields[0].value.count("\n") == 7
        assert embed.fields[1].name == "Alternates (1)"
        assert embed.fields[1].value.count("\n") == 1

        await lobby.remove(player)
        embed = lobby.get_lobby_message()
        assert embed.title == "foo Lobby: (7)"
        assert embed.footer.text == "More players can join."
        assert embed.colour == Colour.orange()
        assert len(embed.fields) == 1
        assert embed.fields[0].name == "Players (7)"
        assert embed.fields[0].value.count("\n") == 7

        for _ in range(100):
            await lobby.add(member())
        embed = lobby.get_lobby_message()
        assert embed.title == "foo Lobby: (107)"
        assert embed.footer.text == "More players can join."
        assert embed.colour == Colour.orange()
        assert len(embed.fields) == 2
        assert embed.fields[1].name == "Alternates (100)"
        assert embed.fields[1].value.count("\n") == 100

        await lobby.ready(member())
        embed = lobby.get_lobby_message()
        assert embed.title == "foo Lobby: (108)"
        assert embed.footer.text == "Game ready. More players can join."
        assert embed.colour == Colour.green()
        assert len(embed.fields) == 2
        assert embed.fields[0].name == "Players (8)"
        assert embed.fields[0].value.count("\n") == 8
        assert embed.fields[1].name == "Alternates (100)"
        assert embed.fields[1].value.count("\n") == 100

        lobby.c.vLaunch = "foo.com"
        embed = lobby.get_lobby_message()
        assert embed.fields[0].value.count("\n") == 9

        lobby.c.vMax = 8
        embed = lobby.get_lobby_message()
        assert embed.footer.text == "Game ready. More alternates can join."

        lobby.c.vMax = 9
        embed = lobby.get_lobby_message()
        assert embed.footer.text == "Game ready. More players can join."

        lobby.c.vMax = 8
        lobby.c.vOverflow = False
        embed = lobby.get_lobby_message()
        assert embed.footer.text == "Game ready. "
        assert embed.fields[1].name == "Not Ready (100)"

    async def test_game_start_message(self):
        topic = "@players(min: 8)"
        lobby = Lobby(bot(), ctx := channel("channel", topic))
        lobby.get_lobby_message = Mock()
        for _ in range(8):
            await lobby.ready(member())
        lobby.get_lobby_message.assert_called_with(
            mention=True,
            title=f"Game Starting in #{ctx.name} Lobby",
            subtitle=None,
        )

    async def test_get_matches(self):
        topic = "@teams([4, 4])"
        lobby = Lobby(bot(), channel(topic=topic))
        for _ in range(8):
            await lobby.ready(member())

        seen = set()
        matches = iter(lobby.get_matches())
        for _ in range(35):  # 35 times: (8 choose 4) / 2
            match = next(matches)
            assert len(match) == 2
            assert match not in seen
            seen.add(match)

        final = next(matches, None)
        assert final is None

    async def test_shuffle(self):
        topic = "@teams([4, 4])"
        lobby = Lobby(bot(), ctx := channel(topic=topic))
        for _ in range(8):
            await lobby.ready(member())

        ctx.reset_mock()
        await lobby.show_next_shuffle()
        assert ctx.send.await_count == 1
        _, kwargs = ctx.send.await_args_list[0]
        assert len(kwargs) == 1
        embed = kwargs["embed"]
        assert embed.title == "Shuffle 1"
        assert len(embed.fields) == 2
        assert embed.fields[0].name == "Team 1"
        assert embed.fields[0].value.count("\n") == 4
        assert embed.fields[1].name == "Team 2"
        assert embed.fields[1].value.count("\n") == 4

    async def test_broadcast(self):
        topic = """
            @players(max: 2)
            @broadcast([dest1, dest2])
        """
        discord_bot = bot()
        discord_bot.get_all_channels.return_value = [
            lobby_channel := channel(name="lobby", topic=topic),
            dest_one := channel(name="dest1"),
            dest_two := channel(name="dest2"),
            misc_channel := channel(name="misc"),
        ]

        lobby = Lobby(discord_bot, lobby_channel)
        assert dest_one.send.call_count == 0
        assert dest_two.send.call_count == 0
        assert misc_channel.send.call_count == 0

        await lobby.add(player_one := member())
        assert dest_one.send.call_count == 0
        assert dest_two.send.call_count == 0
        assert misc_channel.send.call_count == 0

        await lobby.ready(player_one)
        assert dest_one.send.call_count == 1
        assert dest_two.send.call_count == 1
        assert misc_channel.send.call_count == 0

        await lobby.ready(member())
        assert dest_one.send.call_count == 1
        assert dest_two.send.call_count == 1
        assert misc_channel.send.call_count == 0

    async def test_config(self):
        topic = """
            @name({})
            @broadcast(4)
            @players("dog")
            @teams()
            @overflow([])
            @foo()
        """
        lobby = Lobby(bot(), ctx := channel(topic=topic))
        await lobby.show_config()
        assert ctx.send.await_count == 1
        embed = ctx.send.await_args.kwargs["embed"]
        assert embed.title == "Lobby Config"
        assert len(embed.fields) == 2
        assert embed.fields[0].name == "Settings"
        assert embed.fields[0].value.count("\n") == 5
        assert embed.fields[1].name == "Issues"
        assert embed.fields[1].value.count("\n") == 12

        lobby.c.install("@name('Game night!')")
        embed = lobby.c.describe()
        assert embed.fields[1].name == "Issues"
        assert embed.fields[1].value.count("\n") == 10

        lobby.c.install("@teams([2, 2])")
        embed = lobby.c.describe()
        assert embed.fields[1].name == "Issues"
        assert embed.fields[1].value.count("\n") == 8

        lobby.c.install("@overflow(False)")
        embed = lobby.c.describe()
        assert embed.fields[1].name == "Issues"
        assert embed.fields[1].value.count("\n") == 6

        lobby.c.install("@broadcast([])")
        embed = lobby.c.describe()
        assert embed.fields[1].name == "Issues"
        assert embed.fields[1].value.count("\n") == 4

        lobby.c.install("@players(min: 3)")
        embed = lobby.c.describe()
        assert embed.fields[1].name == "Issues"
        assert embed.fields[1].value.count("\n") == 2

        ctx.topic = """
            @name("Game Night!")
            @broadcast([])
            @players(min: 3)
            @teams([2, 2])
            @overflow(False)
        """
        lobby = Lobby(bot(), ctx)
        embed = lobby.c.describe()
        assert len(embed.fields) == 1

    async def test_cache(self):
        topic = """
            @teams([2, 2])
        """
        lobby = Lobby(bot(), channel(topic=topic))
        for _ in range(8):
            await lobby.ready(member())

        assert not lobby._cache

        await lobby.show_next_shuffle()
        shuffles_cache = lobby._cache["shuffles"]
        assert shuffles_cache

        await lobby.add(p_joined := member())
        assert lobby._cache["shuffles"] == shuffles_cache

        await lobby.ready(p_ready := member())
        assert not lobby._cache

        await lobby.show_next_shuffle()
        assert lobby._cache["shuffles"]
        assert lobby._cache["shuffles"] != shuffles_cache

        await lobby.remove(p_joined)
        assert lobby._cache

        await lobby.remove(p_ready)
        assert not lobby._cache
