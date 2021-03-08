from typing import List, Dict
from discord.channel import TextChannel
from numpy import matrix
from sklearn.linear_model import LinearRegression
from statistics import stdev, mean

from utils.verses import Match

from .game_data import GameData


GAME_WEIGHT_HALFLIFE_DAYS: int = 60
AVERAGE_SCORE: int = 2000


async def rank(matches: List[Match], id: str, channel: TextChannel):
    data = await GameData.fetch(id, channel)
    scores = get_player_ranks(data)

    def mean_balance(match: Match) -> float:
        (team_one, team_two) = match
        avg_one = mean(
            [scores.get(p.member.id, AVERAGE_SCORE) for p in team_one]
        )
        avg_two = mean(
            [scores.get(p.member.id, AVERAGE_SCORE) for p in team_two]
        )
        return abs(avg_one - avg_two)

    matches.sort(key=mean_balance)


def get_player_ranks(data: GameData) -> Dict[int, float]:
    if len(data.get_all_players()) == 0:
        return dict()

    model = LinearRegression().fit(
        __get_training_data(data),
        __get_target_values(data),
        __get_weights(data),
    )

    scores = model.coef_[0]
    average = mean(scores)
    std_dev = stdev(scores)

    player_scores = {}
    for i, player in enumerate(data.get_all_players()):
        score = (scores[i] - average) / std_dev
        player_scores[player] = __normalize(score)
    return player_scores


def __normalize(score: float) -> int:
    score *= 1000
    score += AVERAGE_SCORE
    return int(score)


def __get_training_data(data: GameData) -> matrix:
    game_rows = []
    players = data.get_all_players()

    for game in data.games:
        player_cols = []
        for player in players:
            player_cols.append(game.get_player_team_modifier(player))
        game_rows.append(player_cols)

    return matrix(game_rows)


def __get_target_values(data: GameData) -> matrix:
    return matrix([[g.get_percent_difference()] for g in data.games])


def __get_weights(data: GameData) -> matrix:
    decay_weights = __get_decay_weights(data)
    game_points = [g.team_one.score + g.team_two.score for g in data.games]
    return [
        decay * points for decay, points in zip(decay_weights, game_points)
    ]


def __get_decay_weights(data: GameData) -> matrix:
    newest = max([g.date for g in data.games])
    return [
        0.5 ** ((newest - g.date).days / GAME_WEIGHT_HALFLIFE_DAYS)
        for g in data.games
    ]
