# Rolling season enabled sub-history data selection
# to provide a more reactive ranking experience.
USE_ROLLING_SEASON: bool = True
# When a rolling season is active, we'll only look
# this number of days back for games.
LENGTH_DAYS: int = 120
# When a rolling season is active, we'll only use
# your "season rank" if you've played this many games.
PLACEMENT_GAMES: int = 3

# For every interval of this value, we decrease the
# weight of games before this value (days ago)
GAME_WEIGHT_HALFLIFE_DAYS: int = 60

# If a player has no history in our data, use this score.
AVERAGE_RANK: int = 2500
