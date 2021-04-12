import asyncio
from plugins.SuperCashBrosLeftForDead.season import Season
from aiounittest import AsyncTestCase
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from random import randint, shuffle
from statistics import mean

from discord.channel import TextChannel
from discord.ext.commands.bot import Bot
from discord.member import Member

from models.lobby import Lobby
from plugins.SuperCashBrosLeftForDead.ranker import get_ranks
from plugins.SuperCashBrosLeftForDead.game_data import Game, Team
from plugins.SuperCashBrosLeftForDead.plugin import leaderboard, ranked, rank


def noop(*args, **kwargs):
    pass


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


def _add_game(data, ids, date=datetime.today()):
    shuffle(ids)
    team_one = Team(ids[4:], randint(1000, 3000))
    team_two = Team(ids[:4], randint(1000, 3000))
    data.append(Game(date, team_one, team_two))


@patch("plugins.SuperCashBrosLeftForDead.game_data.GameData.fetch")
class TestSuperCashBrosLeftForDead(AsyncTestCase):
    @patch("plugins.SuperCashBrosLeftForDead.plugin.draw_composite")
    async def test_ranked_composite(self, draw_composite, get_games):
        draw_composite.return_value = (composit_future := asyncio.Future())
        composit_future.set_result("assets/coach_small.png")

        games = []
        get_games.return_value = (game_data_future := asyncio.Future())
        game_data_future.set_result(games)
        ids = [id for id in range(8)]
        [_add_game(games, ids) for _ in range(5)]

        topic = "@SuperCashBrosLeftForDead(history: 'patched')"
        lobby = Lobby(bot(), ctx := channel(topic=topic))
        for id in range(8):
            await lobby.ready(member(id + 1))

        await ranked(lobby, ctx)
        assert draw_composite.await_count == 1

    async def test_ranking_order(self, get_games):
        games = []
        get_games.return_value = (future := asyncio.Future())
        future.set_result(games)
        ids = [id for id in range(8)]
        [_add_game(games, ids) for _ in range(5)]

        topic = "@SuperCashBrosLeftForDead(history: 'patched')"
        lobby = Lobby(bot(), channel(topic=topic))

        for id in range(8):
            await lobby.ready(member(id))

        inactive_rank = get_ranks(games, Season.all_time())
        active_rank = get_ranks(games, Season.current())

        def get_player_rank(p) -> int:
            if active_rank and p in active_rank:
                return active_rank[p]
            if p in inactive_rank:
                return inactive_rank[p]
            return 2000

        matches = lobby.get_matches()
        await rank(matches, get_player_rank)
        last_diff = -1
        for m in matches:
            m = list(m)
            mean_1 = mean([get_player_rank(p.member.id) for p in list(m[0])])
            mean_2 = mean([get_player_rank(p.member.id) for p in list(m[1])])
            next_diff = abs(mean_1 - mean_2)
            assert next_diff >= last_diff
            last_diff = next_diff

    async def test_all_ranked_players(self, game_data):
        games = []
        game_data.return_value = (future := asyncio.Future())
        future.set_result(games)

        topic = "@SuperCashBrosLeftForDead(history: 'patched')"
        lobby = Lobby(bot(), ctx := channel(topic=topic))

        ids = [id for id in range(8)]
        long_ago = datetime.now() - timedelta(days=61)
        [_add_game(games, ids, long_ago) for _ in range(5)]

        await leaderboard(lobby, ctx)
        assert ctx.send.await_count == 1
        embed = ctx.send.await_args_list[0].kwargs["embed"]
        assert len(embed.fields) == 1
        embed.fields[0].value.startswith("No players in the lobby")
        ctx.reset_mock()

        _add_game(games, ids)
        await leaderboard(lobby, ctx)
        assert ctx.send.await_count == 1
        embed = ctx.send.await_args_list[0].kwargs["embed"]
        assert len(embed.fields) == 1
        embed.fields[0].value.startswith("No players in the lobby")
        ctx.reset_mock()

        [_add_game(games, ids) for _ in range(4)]
        await leaderboard(lobby, ctx)
        assert ctx.send.await_count == 1
        embed = ctx.send.await_args_list[0].kwargs["embed"]
        assert len(embed.fields) == 8
        ctx.reset_mock()

        ids = [id + 8 for id in range(8)]
        [_add_game(games, ids) for _ in range(5)]
        await leaderboard(lobby, ctx)
        assert ctx.send.await_count == 1
        embed = ctx.send.await_args_list[0].kwargs["embed"]
        assert len(embed.fields) == 16
