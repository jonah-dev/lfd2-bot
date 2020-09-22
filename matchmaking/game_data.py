import re
import json
from datetime import datetime
from utils.handle import handle
from utils.usage_exception import UsageException
from discord.channel import TextChannel
from gsheets import Sheets
from cachetools.func import ttl_cache
from typing import List, Set

from utils.asyncify import asyncify


class Team:
    def __init__(self, players: List[int], score: int):
        self.players = players
        self.score = score

    def __contains__(self, player) -> bool:
        return player in self.players


class Game:
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


class GameData:
    def __init__(self, games: List[Game]):
        self.games = games

    @staticmethod
    @ttl_cache(maxsize=128, ttl=1800)  # 30 minutes
    async def fetch(channel: TextChannel):
        url = GameData.__get_url(channel)
        sheets_fetcher = Sheets.from_files(
            "client_secrets.json",
            "oath_cache.json",
        )
        sheets = await asyncify(sheets_fetcher.get(url))
        games: List[Game] = []
        # Must be the second sheet
        # Skip headers
        for row in sheets[1]._values[0:]:
            try:
                games.append(
                    Game(
                        datetime.strptime(row[4], "%m/%d/%Y"),
                        Team(json.loads(row[0]), row[1]),
                        Team(json.loads(row[2]), row[3]),
                    )
                )
            except BaseException as exception:
                handle(None, exception)

        return GameData(games)

    @staticmethod
    def __get_url(channel: TextChannel) -> str:
        if channel.topic is None:
            raise UsageException.directive_missing(channel, 'games')

        id = re.findall(r"^\?games #([^\s]+)", channel.topic, re.M)
        return f"https://docs.google.com/spreadsheets/d/{id}"

    def get_all_players(self) -> Set[int]:
        players: Set[int] = set()
        for g in self.games:
            players.update(g.team_one.players)
            players.update(g.team_two.players)

        return players
