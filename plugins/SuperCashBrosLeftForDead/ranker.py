from plugins.SuperCashBrosLeftForDead.season import Season
from typing import Callable, List, Dict, Set
from numpy import matrix
from sklearn.linear_model import LinearRegression
from statistics import stdev, mean

from utils.verses import Match

from .game_data import Game

import plugins.SuperCashBrosLeftForDead.ranking_config as rc


async def rank(matches: List[Match], get_player_rank: Callable):
    def mean_balance(match: Match) -> float:
        (team_one, team_two) = match
        avg_one = mean([get_player_rank(p.member.id) for p in team_one])
        avg_two = mean([get_player_rank(p.member.id) for p in team_two])
        return abs(avg_one - avg_two)

    matches.sort(key=mean_balance)


def get_ranks(all_games: List[Game], season: Season) -> Dict[int, float]:
    players = season.get_players(all_games)
    if len(players) == 0:
        return dict()

    games = season.get_games(all_games)
    model = LinearRegression().fit(
        __get_training_data(players, games),
        __get_target_values(games),
        __get_weights(games),
    )

    scores = model.coef_[0]
    average = mean(scores)
    std_dev = stdev(scores)

    player_scores = {}
    for i, player in enumerate(players):
        score = (scores[i] - average) / std_dev
        player_scores[player] = __normalize(score)
    return player_scores


def __normalize(score: float) -> int:
    score *= 1000
    score += rc.AVERAGE_RANK
    return int(score)


def __get_training_data(players: Set[int], games: List[Game]) -> matrix:
    game_rows = []
    for game in games:
        player_cols = []
        for player in players:
            player_cols.append(game.get_player_team_modifier(player))
        game_rows.append(player_cols)

    return matrix(game_rows)


def __get_target_values(games: List[Game]) -> matrix:
    return matrix([[g.get_percent_difference()] for g in games])


def __get_weights(games: List[Game]) -> matrix:
    decay_weights = __get_decay_weights(games)
    game_points = [g.team_one.score + g.team_two.score for g in games]
    return [
        decay * points for decay, points in zip(decay_weights, game_points)
    ]


def __get_decay_weights(games: List[Game]) -> matrix:
    newest = max([g.date for g in games])
    return [
        0.5 ** ((newest - g.date).days / rc.GAME_WEIGHT_HALFLIFE_DAYS)
        for g in games
    ]
