import asyncio
from aiounittest import AsyncTestCase
from unittest.mock import AsyncMock, patch
from datetime import datetime
from random import randint, shuffle
from statistics import mean

from discord.channel import TextChannel
from discord.ext.commands.bot import Bot
from discord.member import Member

from models.lobby import Lobby
from plugins.SuperCashBrosLeftForDead.ranker import get_player_ranks
from plugins.SuperCashBrosLeftForDead.game_data import GameData, Game, Team
from plugins.SuperCashBrosLeftForDead.plugin import ranked, rank


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


ids = [id for id in range(8)]
data = []
for _ in range(5):
    shuffle(ids)
    data.append(
        Game(
            datetime.today(),
            Team(ids[4:], randint(1000, 3000)),
            Team(ids[:4], randint(1000, 3000)),
        )
    )
data = GameData(data)


async def game_data(_id, _channel) -> GameData:
    return data


@patch("plugins.SuperCashBrosLeftForDead.game_data.GameData.fetch", game_data)
@patch("plugins.SuperCashBrosLeftForDead.plugin.draw_composite")
class TestSuperCashBrosLeftForDead(AsyncTestCase):
    async def test_ranked_composite(self, draw_composite):
        topic = "@SuperCashBrosLeftForDead(history: 'patched')"
        lobby = Lobby(bot(), ctx := channel(topic=topic))
        for id in range(8):
            await lobby.ready(member(id + 1))

        f = asyncio.Future()
        f.set_result("assets/coach_small.png")
        draw_composite.return_value = f

        await ranked(lobby, ctx)
        assert draw_composite.await_count == 1

    async def test_ranking_order(self, draw_composite):
        topic = "@SuperCashBrosLeftForDead(history: 'patched')"
        lobby = Lobby(bot(), ctx := channel(topic=topic))
        for id in range(8):
            await lobby.ready(member(id))

        data = await game_data("patched", ctx)
        ranks = get_player_ranks(data)

        matches = lobby.get_matches()
        await rank(matches, "patched", ctx)

        last_diff = -1
        for m in matches:
            m = list(m)
            mean_1 = mean([ranks[p.member.id] for p in list(m[0])])
            mean_2 = mean([ranks[p.member.id] for p in list(m[1])])
            next_diff = abs(mean_1 - mean_2)
            assert next_diff >= last_diff
            last_diff = next_diff
