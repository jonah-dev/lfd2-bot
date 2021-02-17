from requests import get

from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"


def get_steam_icon(steamID: int):
    try:
        url = f"https://steamdb.info/app/{steamID}"
        page = get(url, headers={"User-Agent": USER_AGENT})
        soup = BeautifulSoup(page.content, "html.parser")
        return soup.select("img.app-icon.avatar")[0].get("src")
    except Exception:
        return None
