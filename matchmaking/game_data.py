import json
from datetime import datetime
from gsheets import Sheets
from cachetools.func import ttl_cache
from typing import List, Set

from numpy import matrix
from sklearn.linear_model import LinearRegression
from statistics import stdev, mean

from models.player import Player
from utils.asyncify import asyncify


class Team():
    def __init__(self, players: List[int], score: int):
        self.players = players
        self.score = score

    def __contains__(self, player) -> bool:
        return player in self.players

class Game():
    def __init__(self, date: datetime, team_one: Team, team_two: Team):
        self.date = date
        self.team_one = team_one
        self.team_two = team_two

    def get_percent_difference(self) -> float:
        difference = self.team_one.score - self.team_two.score
        total = self.team_one.score + self.team_two.score
        # Should this be average instead of total?
        return float(difference) / float(total)

    def get_player_team_modifier(self, player: int) -> int:
        if player in self.team_one:
          return 1

        if player in self.team_two:
          return -1

        return 0

class GameData():
    def __init__(self, games: List[Game]):
        self.games = games

    @ttl_cache(maxsize=128, ttl=1800) # 30 minutes
    @staticmethod
    async def fetch():
        # TODO(stack) Replace with Discord declarative
        sheet_id = '1886KNfDRp-RGRnRkAbb8IQHTvQFHw_xcavz_2pXmIsg'
        sheet_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}'
        sheets_fetcher = Sheets.from_files('client_secrets.json', 'oath_cache.json')
        sheets = sheets_fetcher.get(sheet_url)
        games: List[Game] = []
        for row in sheets[1726324783]._values:
            games.append(Game(
              datetime.strptime(row[4], "%m/%d/%Y"),
              Team(json.loads(row[0]), row[1]),
              Team(json.loads(row[2]), row[3]),
            ))

        return GameData(games)

    def get_all_players(self) -> Set[int]:
        players: Set[int] = set()
        for g in self.games:
            players.union(set(g.team_one.players))
            players.union(set(g.team_two.players))
        return players