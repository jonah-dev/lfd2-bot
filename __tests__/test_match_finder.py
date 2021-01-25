from matchmaking.match_finder import MatchFinder
from string import ascii_letters

from aiounittest import AsyncTestCase


class TestMatchFinder(AsyncTestCase):
    async def test_4_4(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(8)]
        matches = await MatchFinder.new(players, [4, 4])
        assert len(matches.matches) == 35

    async def test_1_4(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(5)]
        matches = await MatchFinder.new(players, [1, 4])
        assert len(matches.matches) == 5

    async def test_2_2_2(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(6)]
        matches = await MatchFinder.new(players, [2, 2, 2])
        assert len(matches.matches) == 15

    async def test_1_1_1_1_1(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(5)]
        matches = await MatchFinder.new(players, [1, 1, 1, 1, 1])
        assert len(matches.matches) == 1

    async def test_no_players(self):
        matches = await MatchFinder.new([], [2, 2])
        assert len(matches.matches) == 0

    async def test_no_teams(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(5)]
        matches = await MatchFinder.new(players, [])
        assert len(matches.matches) == 1

    async def test_too_many_players(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(5)]
        matches = await MatchFinder.new(players, [1, 2])
        assert len(matches.matches) == 30

    async def test_not_enough_players(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(2)]
        matches = await MatchFinder.new(players, [1, 2])
        assert len(matches.matches) == 0
