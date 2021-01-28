import asyncio
from aiounittest import AsyncTestCase
from unittest.mock import AsyncMock, patch
from datetime import datetime
from string import digits
from random import choice, randint

from discord.channel import TextChannel
from discord.ext.commands.bot import Bot
from discord.file import File
from discord.member import Member

from models.lobby import Lobby
from plugins.SuperCashBrosLeftForDead.game_data import GameData, Game, Team
from plugins.SuperCashBrosLeftForDead.SuperCashBrosLeftForDead import ranked


def channel(topic: str = "") -> TextChannel:
    channel = AsyncMock(spec=TextChannel)
    channel.id = 1234
    channel.topic = topic
    channel.mention = 1234
    return channel


def bot() -> Bot:
    bot = AsyncMock(spec=Bot)
    return bot


def member(id: int) -> Member:
    member = AsyncMock(spec=Member)
    member.id = id
    member.display_name = id
    member.mention = id
    member.bot = None
    return member


def id() -> str:
    return int("".join(choice(digits) for _ in range(10)))


async def game_data(_id, _channel) -> GameData:
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


# async def draw_player(
#     draw: ImageDraw.Draw,
#     composite: Image,
#     player: Player,
#     character: Image,
#     y_offset: int,
# ) -> None:


@patch("plugins.SuperCashBrosLeftForDead.game_data.GameData.fetch", game_data)
@patch("plugins.SuperCashBrosLeftForDead.composite.draw_composite")
class TestSuperCashBrosLeftForDead(AsyncTestCase):
    async def test_ranked(self, draw_composite):
        topic = "@SuperCashBrosLeftForDead(history: 'patched')"
        lobby = Lobby(bot(), ctx := channel(topic=topic))
        for id in range(8):
            await lobby.ready(member(id + 1))

        f = asyncio.Future()
        f.set_result(AsyncMock(spec=File))
        draw_composite.return_value = f
        await ranked(lobby, ctx)
        pass
