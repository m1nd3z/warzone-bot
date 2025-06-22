import aiohttp
import asyncio
import os
from typing import Optional, Dict

class CODAPI:
    def __init__(self):
        self.platform = "battle"
        self.base_url = "https://my.callofduty.com/api/papi-client"
        self.sso_token = os.getenv("ACT_SSO_COOKIE")
        self.headers = {
            "Cookie": f"ACT_SSO_COOKIE={self.sso_token}"
        }

    async def get_player_stats(self, username: str) -> Optional[Dict]:
        encoded_username = username.replace("#", "%23")
        url = f"{self.base_url}/stats/cod/v1/title/warzone/platform/{self.platform}/gamer/{encoded_username}/profile"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        print(f"⚠️ HTTP {response.status}")
                        return None

                    data = await response.json()
                    stats = data.get("data", {}).get("lifetime", {}).get("mode", {}).get("br", {}).get("properties", {})
                    return {
                        "kills": stats.get("kills", 0),
                        "kd_ratio": stats.get("kdRatio", 0.0),
                        "wins": stats.get("wins", 0),
                        "games_played": stats.get("gamesPlayed", 0),
                        "gulag_win_ratio": stats.get("gulagWinRatio", 0.0)
                    }
        except Exception as e:
            print(f"❌ Klaida: {e}")
            return None