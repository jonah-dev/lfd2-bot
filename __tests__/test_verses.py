from aiounittest import AsyncTestCase

from typing import List

from utils.verses import Match, Verses
from string import ascii_letters


def get_matches(players, teams) -> List[Match]:
    matches = set([])
    Verses(None, [], players, teams, matches)
    return list(matches)


class TestVerses(AsyncTestCase):
    async def test_4_4(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(8)]
        matches = get_matches(players, [4, 4])
        assert len(matches) == 35

    async def test_1_4(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(5)]
        matches = get_matches(players, [1, 4])
        assert len(matches) == 5

    async def test_2_2_2(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(6)]
        matches = get_matches(players, [2, 2, 2])
        assert len(matches) == 15

    async def test_1_1_1_1_1(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(5)]
        matches = get_matches(players, [1, 1, 1, 1, 1])
        assert len(matches) == 1

    async def test_no_players(self):
        matches = get_matches([], [2, 2])
        assert len(matches) == 0

    async def test_no_teams(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(5)]
        matches = get_matches(players, [])
        assert len(matches) == 0

    async def test_too_many_players(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(5)]
        matches = get_matches(players, [1, 2])
        assert len(matches) == 30

    async def test_not_enough_players(self):
        id = iter([a for a in ascii_letters])
        players = [next(id) for _ in range(2)]
        matches = get_matches(players, [1, 2])
        assert len(matches) == 1
        assert len(teams := matches.pop()) == 2
        assert len(teams := list(teams)) == 2
        assert len(teams[0]) == 1
        assert len(teams[1]) == 1
