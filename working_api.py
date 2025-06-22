#!/usr/bin/env python3
"""
Veikiantis API sprendimas su keliais alternatyvais
"""

import aiohttp
import asyncio
from typing import Dict, Optional, List
import json
import time
import random
import urllib.parse

class WorkingAPI:
    def __init__(self):
        """
        Inicializuoja veikiantį API su keliais alternatyvais
        """
        self.apis = [
            {
                'name': 'COD Stats API',
                'base_url': 'https://call-of-duty-modern-warfare.p.rapidapi.com',
                'headers': {
                    "x-rapidapi-key": "ce477eae5dmsh238966977333d6dp1065ffjsn5923ec0a9ab0",
                    "x-rapidapi-host": "call-of-duty-modern-warfare.p.rapidapi.com"
                },
                'endpoint': '/warzone/{username}/{platform}',
                'platform_map': {'battlenet': 'battle', 'battle': 'battle', 'psn': 'psn', 'xbl': 'xbl'}
            },
            {
                'name': 'COD API Hub',
                'base_url': 'https://cod-api.uno',
                'headers': {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json"
                },
                'endpoint': '/stats/cod/v1/mw/warzone/{username}/{platform}',
                'platform_map': {'battlenet': 'battle', 'battle': 'battle', 'psn': 'psn', 'xbl': 'xbl'}
            },
            {
                'name': 'COD Tracker API',
                'base_url': 'https://cod.tracker.gg',
                'headers': {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json"
                },
                'endpoint': '/api/v1/cod/mw/profile/{platform}/{username}',
                'platform_map': {'battlenet': 'battlenet', 'battle': 'battlenet', 'psn': 'psn', 'xbl': 'xbl'}
            }
        ]
        
        self.request_times = []
        self.max_requests_per_minute = 10
        self.retry_attempts = 2
        self.retry_delay = 3

    def _check_rate_limit(self):
        """Patikrina rate limiting"""
        current_time = time.time()
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        if len(self.request_times) >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                print(f"Rate limit pasiektas. Palaukiame {sleep_time:.1f} sekundžių...")
                time.sleep(sleep_time)
        
        self.request_times.append(current_time)

    async def _make_request_with_retry(self, url: str, headers: Dict) -> Optional[aiohttp.ClientResponse]:
        """Atlieka užklausą su retry logika"""
        for attempt in range(self.retry_attempts):
            try:
                timeout = aiohttp.ClientTimeout(total=20)
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return response
                        elif response.status in [400, 403, 404, 429, 502, 503]:
                            print(f"HTTP {response.status} klaida (bandymas {attempt + 1}/{self.retry_attempts})")
                            if attempt < self.retry_attempts - 1:
                                wait_time = self.retry_delay * (attempt + 1)
                                print(f"Palaukiame {wait_time} sekundžių...")
                                await asyncio.sleep(wait_time)
                            else:
                                return None
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

    def _parse_cod_stats_api(self, data: Dict, username: str, platform: str) -> Optional[Dict]:
        """Apdoroja COD Stats API duomenis"""
        try:
            if 'stats' not in data:
                return None
                
            stats = data['stats']
            return {
                'username': username,
                'platform': platform,
                'kills': stats.get('kills', 0),
                'deaths': stats.get('deaths', 0),
                'kd_ratio': stats.get('kdRatio', 0),
                'wins': stats.get('wins', 0),
                'top_10': stats.get('top10', 0),
                'score_per_minute': stats.get('scorePerMinute', 0),
                'games_played': stats.get('gamesPlayed', 0),
                'avg_life_time': 0,
                'damage_done': 0,
                'damage_taken': 0,
                'headshots': 0,
                'longest_shot': 0,
                'revives': 0,
                'time_played': 0
            }
        except Exception as e:
            print(f"Klaida apdorojant COD Stats API duomenis: {e}")
            return None

    def _parse_cod_api_hub(self, data: Dict, username: str, platform: str) -> Optional[Dict]:
        """Apdoroja COD API Hub duomenis"""
        try:
            if 'data' not in data or 'stats' not in data['data']:
                return None
                
            stats = data['data']['stats']
            return {
                'username': username,
                'platform': platform,
                'kills': stats.get('kills', 0),
                'deaths': stats.get('deaths', 0),
                'kd_ratio': stats.get('kdRatio', 0),
                'wins': stats.get('wins', 0),
                'top_10': stats.get('top10', 0),
                'score_per_minute': stats.get('scorePerMinute', 0),
                'games_played': stats.get('gamesPlayed', 0),
                'avg_life_time': stats.get('avgLifeTime', 0),
                'damage_done': stats.get('damageDone', 0),
                'damage_taken': stats.get('damageTaken', 0),
                'headshots': stats.get('headshots', 0),
                'longest_shot': stats.get('longestShot', 0),
                'revives': stats.get('revives', 0),
                'time_played': stats.get('timePlayed', 0)
            }
        except Exception as e:
            print(f"Klaida apdorojant COD API Hub duomenis: {e}")
            return None

    def _parse_cod_tracker(self, data: Dict, username: str, platform: str) -> Optional[Dict]:
        """Apdoroja COD Tracker API duomenis"""
        try:
            if 'data' not in data or 'stats' not in data['data']:
                return None
                
            stats = data['data']['stats']
            result = {
                'username': username,
                'platform': platform,
                'kills': 0,
                'deaths': 0,
                'kd_ratio': 0,
                'wins': 0,
                'top_10': 0,
                'score_per_minute': 0,
                'games_played': 0,
                'avg_life_time': 0,
                'damage_done': 0,
                'damage_taken': 0,
                'headshots': 0,
                'longest_shot': 0,
                'revives': 0,
                'time_played': 0
            }
            
            # Ieškome statistikos pagal metadata key
            for stat in stats:
                key = stat.get('metadata', {}).get('key', '')
                value = float(stat.get('value', 0))
                
                if key == 'kills':
                    result['kills'] = value
                elif key == 'deaths':
                    result['deaths'] = value
                elif key == 'kdRatio':
                    result['kd_ratio'] = value
                elif key == 'wins':
                    result['wins'] = value
                elif key == 'top10':
                    result['top_10'] = value
                elif key == 'scorePerMinute':
                    result['score_per_minute'] = value
                elif key == 'gamesPlayed':
                    result['games_played'] = value
                elif key == 'avgLifeTime':
                    result['avg_life_time'] = value
                elif key == 'damageDone':
                    result['damage_done'] = value
                elif key == 'damageTaken':
                    result['damage_taken'] = value
                elif key == 'headshots':
                    result['headshots'] = value
                elif key == 'longestShot':
                    result['longest_shot'] = value
                elif key == 'revives':
                    result['revives'] = value
                elif key == 'timePlayed':
                    result['time_played'] = value
            
            return result
        except Exception as e:
            print(f"Klaida apdorojant COD Tracker duomenis: {e}")
            return None

    async def get_player_stats(self, username: str, platform: str = "battlenet") -> Optional[Dict]:
        """
        Gauna žaidėjo statistiką iš visų galimų API
        """
        try:
            self._check_rate_limit()
            
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            # Pašaliname # ir viską po jo
            clean_username = username.split('#')[0]
            
            # Bandome kiekvieną API
            for api_config in self.apis:
                try:
                    print(f"Bandome {api_config['name']} su {username}...")
                    
                    # Nustatome platformą pagal API
                    api_platform = api_config['platform_map'].get(platform, platform)
                    
                    # Formatuojame URL
                    url = f"{api_config['base_url']}{api_config['endpoint'].format(username=clean_username, platform=api_platform)}"
                    
                    response = await self._make_request_with_retry(url, api_config['headers'])
                    if not response:
                        print(f"{api_config['name']} nepavyko")
                        continue
                    
                    data = await response.json()
                    
                    # Apdoroja duomenis pagal API tipą
                    if api_config['name'] == 'COD Stats API':
                        result = self._parse_cod_stats_api(data, username, platform)
                    elif api_config['name'] == 'COD API Hub':
                        result = self._parse_cod_api_hub(data, username, platform)
                    elif api_config['name'] == 'COD Tracker API':
                        result = self._parse_cod_tracker(data, username, platform)
                    else:
                        result = None
                    
                    if result:
                        print(f"Sėkmingai gauta statistikos iš {api_config['name']}: {result['username']}")
                        return result
                        
                except Exception as e:
                    print(f"Klaida su {api_config['name']}: {str(e)}")
                    continue
            
            print(f"Nepavyko gauti {username} statistikos iš jokio API")
            return None
                
        except Exception as e:
            print(f"Klaida gaunant statistiką: {str(e)}")
            return None

    async def get_recent_matches(self, username: str, platform: str = "battlenet", limit: int = 5) -> Optional[List[Dict]]:
        """
        Gauna žaidėjo neseniausias žaidimas
        """
        # Šiuo metu nepalaikoma, bet galima pridėti vėliau
        return None

# Testavimo funkcija
async def test_working_api():
    """Testuoja veikiantį API"""
    print("🧪 Testuojame veikiantį API...")
    
    api = WorkingAPI()
    
    # Testuojame su žinomu žaidėju
    test_username = "m1nd3#2311"
    test_platform = "battlenet"
    
    print(f"📋 Testuojame: {test_username} ({test_platform})")
    
    try:
        stats = await api.get_player_stats(test_username, test_platform)
        if stats:
            print("✅ Veikiantis API veikia!")
            print(f"   Vardas: {stats.get('username', 'N/A')}")
            print(f"   Žudymai: {stats.get('kills', 0):,}")
            print(f"   K/D: {stats.get('kd_ratio', 0):.2f}")
            print(f"   Perėmimai: {stats.get('wins', 0):,}")
        else:
            print("❌ Veikiantis API nepavyko")
            
    except Exception as e:
        print(f"❌ Klaida testuojant veikiantį API: {e}")

if __name__ == "__main__":
    asyncio.run(test_working_api()) 