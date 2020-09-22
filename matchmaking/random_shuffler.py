import random
from typing import Callable, List

from matchmaking.match_finder import Match


def get_shuffler() -> Callable:
    """
    This function returns a 'ranker' function. It is meant to be used
    by matchmaker, e.g. `get_next_match(..., get_ranker(...))`, and it
    is only this complex so we can capture the channel in the closure.
    """
    async def shuffle(matches: List[Match]):
        random.shuffle(matches)
    
    return shuffle
      