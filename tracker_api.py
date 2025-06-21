import aiohttp
import asyncio
from typing import Dict, Optional, List
import json
import time
import random

class TrackerGGAPI:
    def __init__(self):
        """
        Inicializuoja Tracker.gg API
        """
        self.base_url = "https://api.tracker.gg/api/v2/warzone/standard/profile"
        # Patobulinti headers su realistiškesniais duomenimis
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        # Rate limiting - sumažiname iki 5 užklausų per minutę
        self.request_times = []
        self.max_requests_per_minute = 5
        self.retry_attempts = 3
        self.retry_delay = 5  # sekundės

    def _check_rate_limit(self):
        """
        Patikrina rate limiting
        """
        current_time = time.time()
        # Pašaliname užklausas, kurios senesnės nei 1 minutė
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        if len(self.request_times) >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                print(f"Rate limit pasiektas. Palaukiame {sleep_time:.1f} sekundžių...")
                time.sleep(sleep_time)
        
        self.request_times.append(current_time)

    async def _make_request_with_retry(self, url: str) -> Optional[aiohttp.ClientResponse]:
        """
        Atlieka užklausą su retry logika
        """
        for attempt in range(self.retry_attempts):
            try:
                # Pridedame atsitiktinį User-Agent variantą
                headers = self.headers.copy()
                if attempt > 0:
                    # Pridedame atsitiktinį User-Agent po nesėkmingų bandymų
                    user_agents = [
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ]
                    headers["User-Agent"] = random.choice(user_agents)
                
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return response
                        elif response.status == 403:
                            print(f"HTTP 403 - Prieiga uždrausta (bandymas {attempt + 1}/{self.retry_attempts})")
                            if attempt < self.retry_attempts - 1:
                                wait_time = self.retry_delay * (attempt + 1)
                                print(f"Palaukiame {wait_time} sekundžių prieš kitą bandymą...")
                                await asyncio.sleep(wait_time)
                            else:
                                print("Visi bandymai nepavyko. Galbūt API yra blokuojamas.")
                                return None
                        elif response.status == 404:
                            print("Žaidėjas nerastas (404)")
                            return None
                        elif response.status == 429:
                            print(f"Rate limit viršytas (429) - palaukiame 60 sekundžių...")
                            await asyncio.sleep(60)
                            continue
                        else:
                            print(f"HTTP {response.status} klaida")
                            if attempt < self.retry_attempts - 1:
                                await asyncio.sleep(self.retry_delay)
                            else:
                                return None
                                
            except Exception as e:
                print(f"Tinklo klaida (bandymas {attempt + 1}): {str(e)}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return None
        
        return None

    async def get_player_stats(self, username: str, platform: str = "battlenet") -> Optional[Dict]:
        """
        Gauna žaidėjo statistiką iš Tracker.gg
        :param username: žaidėjo vardas
        :param platform: platforma (battlenet, battle, psn, xbl)
        :return: žaidėjo statistikos duomenys
        """
        try:
            self._check_rate_limit()
            
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            # Formatuojame username pagal platformą
            if platform == "battlenet":
                # Battle.net formatas: username#1234
                if '#' not in username:
                    print("Battle.net vartotojui reikia # su numeriu (pvz. username#1234)")
                    return None
                formatted_username = username.replace('#', '%23')
            elif platform == "psn":
                formatted_username = username
            elif platform == "xbl":
                formatted_username = username
            else:
                print(f"Nepalaikoma platforma: {platform}")
                return None

            url = f"{self.base_url}/{platform}/{formatted_username}"
            print(f"Bandome gauti statistiką iš: {url}")
            
            response = await self._make_request_with_retry(url)
            if not response:
                return None
            
            data = await response.json()
            
            if not data or 'data' not in data:
                print("Neteisingi duomenys iš API")
                return None

            stats = data['data']['stats']
            
            # Ištraukiame reikiamus duomenis
            result = {
                'username': data['data']['platformInfo']['platformUserId'],
                'platform': platform,
                'kills': self._get_stat_value(stats, 'kills'),
                'deaths': self._get_stat_value(stats, 'deaths'),
                'kd_ratio': self._get_stat_value(stats, 'kdRatio'),
                'wins': self._get_stat_value(stats, 'wins'),
                'top_10': self._get_stat_value(stats, 'top10'),
                'score_per_minute': self._get_stat_value(stats, 'scorePerMinute'),
                'games_played': self._get_stat_value(stats, 'gamesPlayed'),
                'avg_life_time': self._get_stat_value(stats, 'avgLifeTime'),
                'damage_done': self._get_stat_value(stats, 'damageDone'),
                'damage_taken': self._get_stat_value(stats, 'damageTaken'),
                'headshots': self._get_stat_value(stats, 'headshots'),
                'longest_shot': self._get_stat_value(stats, 'longestShot'),
                'revives': self._get_stat_value(stats, 'revives'),
                'time_played': self._get_stat_value(stats, 'timePlayed')
            }
            
            print(f"Sėkmingai gauta statistikos: {result['username']}")
            return result
                
        except Exception as e:
            print(f"Klaida gaunant statistiką: {str(e)}")
            return None

    def _get_stat_value(self, stats: List[Dict], stat_name: str) -> float:
        """
        Ištraukia statistikos reikšmę iš stats sąrašo
        """
        for stat in stats:
            if stat.get('metadata', {}).get('key') == stat_name:
                return float(stat.get('value', 0))
        return 0.0

    async def get_recent_matches(self, username: str, platform: str = "battlenet", limit: int = 5) -> Optional[List[Dict]]:
        """
        Gauna žaidėjo neseniausias žaidimas
        :param username: žaidėjo vardas
        :param platform: platforma
        :param limit: kiek žaidimų gauti
        :return: žaidimų sąrašas
        """
        try:
            self._check_rate_limit()
            
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            # Formatuojame username
            if platform == "battlenet" and '#' in username:
                formatted_username = username.replace('#', '%23')
            else:
                formatted_username = username

            url = f"{self.base_url}/{platform}/{formatted_username}/matches"
            print(f"Bandome gauti žaidimus iš: {url}")
            
            response = await self._make_request_with_retry(url)
            if not response:
                return None
            
            data = await response.json()
            
            if not data or 'data' not in data:
                return None

            matches = data['data']['matches']
            return matches[:limit] if matches else []
                
        except Exception as e:
            print(f"Klaida gaunant žaidimus: {str(e)}")
            return None

    async def get_player_info(self, username: str, platform: str = "battlenet") -> Optional[Dict]:
        """
        Gauna pagrindinę žaidėjo informaciją
        """
        try:
            self._check_rate_limit()
            
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            if platform == "battlenet" and '#' in username:
                formatted_username = username.replace('#', '%23')
            else:
                formatted_username = username

            url = f"{self.base_url}/{platform}/{formatted_username}"
            
            response = await self._make_request_with_retry(url)
            if not response:
                return None
            
            data = await response.json()
            
            if not data or 'data' not in data:
                return None

            platform_info = data['data']['platformInfo']
            return {
                'username': platform_info['platformUserId'],
                'platform': platform_info['platformSlug'],
                'avatar': platform_info.get('avatarUrl'),
                'level': data['data'].get('level', 0)
            }
                
        except Exception as e:
            print(f"Klaida gaunant žaidėjo informaciją: {str(e)}")
            return None

# Testavimo funkcija
async def test_tracker_api():
    """
    Testuoja Tracker.gg API funkcionalumą
    """
    api = TrackerGGAPI()
    
    # Testuojame su žinomu žaidėju (pakeiskite į tikrą vardą)
    test_username = "test#1234"  # Pakeiskite į tikrą Battle.net vardą
    test_platform = "battlenet"
    
    print("Testuojame Tracker.gg API...")
    
    # Gauname statistiką
    stats = await api.get_player_stats(test_username, test_platform)
    if stats:
        print("Statistika:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print("Nepavyko gauti statistikos")
    
    # Gauname žaidėjo informaciją
    info = await api.get_player_info(test_username, test_platform)
    if info:
        print("Žaidėjo informacija:")
        print(json.dumps(info, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_tracker_api()) 