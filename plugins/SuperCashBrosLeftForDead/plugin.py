from plugins.SuperCashBrosLeftForDead.season import Season
from discord import Colour, Embed, File
from discord.ext.commands.context import Context
from discord.ext.commands.core import command

from models.lobby import Lobby
from models.config import Config
from .ranker import get_ranks, rank
from .composite import draw_composite
from .game_data import GameData
from utils.directive import directive, parse_multi
from utils.usage_exception import UsageException

import plugins.SuperCashBrosLeftForDead.ranking_config as rc


@directive
def SuperCashBrosLeftForDead(config: Config, props: str):
    config.asSteamGame(550)
    config.vMin = 8

    config.pLeft4Dead = {}

    if not props:
        return

    props = parse_multi(props)
    if type(props) is not dict:
        config.issue("You must provide named properties.")
        return

    if "history" in props:
        history = props["history"]
        if type(history) is not str:
            config.issue("'history' must be a google sheet. (see the docs)'")
        else:
            config.pLeft4Dead["history"] = history
            config.installCommand(ranked)
            config.installCommand(leaderboard)


@command()
async def ranked(lobby: "Lobby", ctx: Context):
    """Create fair teams based on player history"""
    if not lobby.is_ready():
        raise UsageException.not_enough_for_match(lobby.channel)

    if __name__ not in lobby._cache:
        id = lobby.c.pLeft4Dead["history"]
        matches = lobby.get_matches()
        data = await GameData.fetch(id, lobby.channel)
        inactive_rank = get_ranks(data, Season.all_time())
        if rc.USE_ROLLING_SEASON:
            season = Season(rc.LENGTH_DAYS, rc.PLACEMENT_GAMES)
            active_rank = get_ranks(data, season)

        def get_player_rank(p: int) -> int:
            if active_rank and p in active_rank:
                return active_rank[p]
            if p in inactive_rank:
                return inactive_rank[p]
            return rc.AVERAGE_RANK

        await rank(matches, get_player_rank)
        lobby._cache[__name__] = iter(enumerate(matches))
        lobby._cache[f"{__name__}-get_rank"] = get_player_rank

    next_match = next(lobby._cache[__name__], None)
    if next_match is None:
        raise UsageException.seen_all_matches(lobby.channel)

    i, teams = next_match
    teams = list(teams)
    team1, team2 = list(teams)[0], list(teams[1])
    channel = lobby.channel.id
    get_rank = lobby._cache[f"{__name__}-get_rank"]
    composite = await draw_composite(i, team1, team2, channel, get_rank)
    await ctx.send(file=File(composite))


@command()
async def leaderboard(lobby, ctx: Context, option: str = None):
    """See player ranks"""
    filter_lobby = option == "lobby"
    id = lobby.c.pLeft4Dead["history"]
    all_games = await GameData.fetch(id, lobby.channel)
    season = Season.current() if rc.USE_ROLLING_SEASON else Season.all_time()
    scores = get_ranks(all_games, season)
    embed = Embed(colour=Colour.blurple())
    embed.title = "Lobby Rankings" if filter_lobby else "Player Rankings"

    def order(item):
        return item[1] or 0  # by score

    if filter_lobby:
        players = [p.member.id for p in lobby.players]
        users = {id: scores.get(id) for id in players}.items()
        ranks = {id: s for id, s in sorted(users, key=order, reverse=True)}
    else:
        user = scores.items()
        ranks = {id: s for id, s in sorted(user, key=order, reverse=True)}

    rank = 1
    for user_id in ranks:
        user = lobby.bot.get_user(user_id)
        if user is None:
            continue

        score = ranks.get(user_id, "(unranked)")
        embed.add_field(name=f"{rank}. {user}", value=score, inline=False)
        rank += 1

    if len(embed.fields) == 0:
        text = "No players in the lobby (or channel) have a ranking."
        embed.add_field(name="No players", value=text)
        await ctx.send(embed=embed)
        return

    if rc.USE_ROLLING_SEASON:
        embed.description = (
            f"Ranking considers all games in the past {rc.LENGTH_DAYS} days."
            f" You must play {rc.PLACEMENT_GAMES} games in this time to be"
            " ranked. Matchmaking for new and unranked players will use all"
            " available data to estimate the player's rank or use the median"
            f" rank of {rc.AVERAGE_RANK}."
        )

    await ctx.send(embed=embed)
