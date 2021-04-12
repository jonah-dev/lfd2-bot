from datetime import datetime, timedelta
from typing import Dict, List, Set
from plugins.SuperCashBrosLeftForDead.game_data import Game

import plugins.SuperCashBrosLeftForDead.ranking_config as rc


class Season:
    @staticmethod
    def all_time():
        return Season(999999999, 0)

    @staticmethod
    def current():
        return Season(rc.LENGTH_DAYS, rc.PLACEMENT_GAMES)

    def __init__(self, days_ago: int, placements: int):
        self.days_ago = days_ago
        self.placements = placements

    def get_players(self, games: List[Game]) -> Set[int]:
        all: Dict[int, int] = dict()  # id => #games
        for g in self.get_games(games):
            for p in g.team_one.players + g.team_two.players:
                all[p] = all.get(p, 0) + 1  # counting games

        return set([p for p in all if all[p] >= self.placements])

    def get_games(self, games: List[Game]) -> List[Game]:
        today = datetime.now()
        season_start = timedelta(days=self.days_ago)
        return [g for g in games if (today - g.date) < season_start]
