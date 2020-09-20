from itertools import combinations
from math import ceil
from typing import Optional, List, Tuple

from models.player import Player

Team = List[Player]
Match = Tuple[Team, Team]

class MatchFinder():
    def __init__(self, players: List[Player], rank):
        self.match_num: int = 0
        self.matches: List[Match] = self.__get_all_matches(players, rank)

    async def get_next_match(self) -> Optional[Tuple[int, Match]]:
        if self.match_num > len(self.matches):
            return None

        self.match_num += 1
        (team_one, team_two) = self.matches[self.match_num - 1]
        return (self.match_num, (team_one, team_two))

    @staticmethod
    def __get_all_matches(players, order) -> List[Match]:
        team_size = ceil(len(players) // 2)
        teams = list()
        for team in combinations(players, team_size):
            team_one: List[Player] = sorted(team)
            team_two: List[Player] = sorted([p for p in players if p not in team])
            if team_one not in teams and team_two not in teams:
                teams.append((team_one, team_two))

        order(teams)
        return teams