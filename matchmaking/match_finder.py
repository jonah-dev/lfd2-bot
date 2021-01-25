from itertools import combinations
from typing import Callable, FrozenSet, Optional, List, Set, Tuple, TypeVar

from models.player import Player

Team = FrozenSet[Player]
Match = FrozenSet[Team]

T = TypeVar("T")


def _pop(items: List[T]) -> Tuple[Optional[T], List[T]]:
    if not items:
        return (None, [])

    return (items[0], items[1:])


class Verses:
    """
    Verses is a short-lived path-finder that starts with a
    pool of players and a team list (e.g. `[4, 4]` is two
    teams of four). It terminates when it runs out of players
    or fulfills all teams. Each node in the path is a team
    of players.

    Note that teams can have any number of players and matches
    can have any number of teams. The team sizes do not have to
    be uniform. For example: `[1, 2, 3]` is valid.

    The final matches are appended to the `matches_ref` set.

    Sets are used to implicitly remove duplicates. There is
    wasted work in doing this, but it solves the match finding
    problem generally, and it is easier to read.
    """

    def __init__(
        self,
        prev_team: Optional["Verses"],
        new_team: Tuple[Player, ...],
        pool: List[Player],
        team_sizes: List[int],
        matches_ref: Set[Match],
    ):
        self.parent = prev_team
        self.players = new_team
        if not team_sizes:
            matches_ref.add(self._finalize_match())
            return

        pool = list(filter(lambda p: p not in new_team, pool))
        team_size, team_sizes = _pop(team_sizes)
        verses_teams = combinations(pool, team_size)
        for opponents in verses_teams:
            Verses(self, opponents, pool, team_sizes, matches_ref)

    def _finalize_match(self) -> Match:
        teams = [self]
        node = self
        while node := node.parent:
            teams.append(node) if node.players else None
        teams.reverse()

        # We use frozensets because they are immutable
        # and can be hashed. This implicitly removes
        # duplicates from the final list.

        # Player order does not matter
        matches = [frozenset(t.players) for t in teams]

        # Verses order does not matter
        return frozenset(matches)


class MatchFinder:
    @staticmethod
    async def new(
        players: List[Player],
        teams: List[int],
        reorder: Optional[Callable] = None,
    ):
        matches = set()
        Verses(None, tuple(), players, teams, matches)

        matches = list(matches)
        if reorder is not None:
            await reorder(matches)

        return MatchFinder(matches)

    def __init__(self, matches: List[Match]):
        self.match_num: int = 0
        self.matches: List[Match] = matches

    def get_next_match(self) -> Optional[Tuple[int, Match]]:
        if self.match_num >= len(self.matches):
            return None

        match = self.matches[self.match_num]
        self.match_num += 1
        return (self.match_num, match)
