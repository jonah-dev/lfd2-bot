from itertools import combinations
from math import ceil
from typing import Callable, Optional, List, Tuple

from models.player import Player

Team = Tuple[Player, ...]
Match = Tuple[Team, Team]


class MatchFinder:
    @staticmethod
    async def new(players: List[Player], order: Callable):
        team_size = ceil(len(players) // 2)
        teams = []
        for team in combinations(players, team_size):
            one = tuple(sorted(team))
            two = tuple(sorted([p for p in players if p not in team]))
            if (one, two) not in teams and (two, one) not in teams:
                teams.append((one, two))

        await order(teams)
        return MatchFinder(teams)

    def __init__(self, matches: List[Match]):
        self.match_num: int = 0
        self.matches: List[Match] = matches

    def get_next_match(self) -> Optional[Tuple[int, Match]]:
        if self.match_num >= len(self.matches):
            return None

        (team_one, team_two) = self.matches[self.match_num]
        self.match_num += 1
        return (self.match_num, (team_one, team_two))
