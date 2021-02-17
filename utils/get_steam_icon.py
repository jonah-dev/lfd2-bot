import os
from requests import get

URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1"
ASSET = "https://cdn.akamai.steamstatic.com/steamcommunity/public/images/apps"


def get_steam_icon(steamID: int):
    try:
        params = {
            "key": os.environ["STEAM_KEY"],
            "include_played_free_games": 1,
            "steamid": os.environ["STEAM_PROFILE"],
            "include_appinfo": 1,
            "format": "json",
            "appids_filter[0]": steamID,
        }
        game = get(URL, params=params).json()
        hash = game["response"]["games"][0]["img_icon_url"]
        return f"{ASSET}/{steamID}/{hash}.jpg"
    except Exception:
        return None
