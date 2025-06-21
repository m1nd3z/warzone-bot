#!/usr/bin/env python3
"""
Trečias API alternatyva - COD API Hub
"""

import aiohttp
import asyncio
from typing import Dict, Optional, List
import json
import time
import random

class ThirdAPI:
    def __init__(self):
        """
        Inicializuoja trečią API (COD API Hub)
        """
        self.base_url = "https://cod-api.uno"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
        self.request_times = []
        self.max_requests_per_minute = 15
        self.retry_attempts = 3
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

    async def _make_request_with_retry(self, url: str) -> Optional[aiohttp.ClientResponse]:
        """Atlieka užklausą su retry logika"""
        for attempt in range(self.retry_attempts):
            try:
                timeout = aiohttp.ClientTimeout(total=20)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=self.headers) as response:
                        if response.status == 200:
                            return response
                        elif response.status == 403:
                            print(f"HTTP 403 - Prieiga uždrausta (bandymas {attempt + 1}/{self.retry_attempts})")
                            if attempt < self.retry_attempts - 1:
                                wait_time = self.retry_delay * (attempt + 1)
                                print(f"Palaukiame {wait_time} sekundžių...")
                                await asyncio.sleep(wait_time)
                            else:
                                print("Visi bandymai nepavyko.")
                                return None
                        elif response.status == 404:
                            print("Žaidėjas nerastas (404)")
                            return None
                        elif response.status == 429:
                            print(f"Rate limit viršytas (429) - palaukiame 30 sekundžių...")
                            await asyncio.sleep(30)
                            continue
                        elif response.status == 502:
                            print(f"HTTP 502 - Serverio klaida (bandymas {attempt + 1}/{self.retry_attempts})")
                            if attempt < self.retry_attempts - 1:
                                wait_time = self.retry_delay * (attempt + 1) * 2
                                print(f"Palaukiame {wait_time} sekundžių...")
                                await asyncio.sleep(wait_time)
                            else:
                                print("Visi bandymai nepavyko - serveris nepasiekiamas.")
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

    async def get_player_stats(self, username: str, platform: str = "battlenet") -> Optional[Dict]:
        """
        Gauna žaidėjo statistiką iš trečio API
        """
        try:
            self._check_rate_limit()
            
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            # Pašaliname # ir viską po jo
            clean_username = username.split('#')[0]
            
            # Nustatome platformą pagal COD API Hub
            cod_platform = "battle" if platform == "battlenet" else platform
            
            url = f"{self.base_url}/stats/cod/v1/mw/warzone/{clean_username}/{cod_platform}"
            print(f"Bandome gauti statistiką iš trečio API: {url}")
            
            response = await self._make_request_with_retry(url)
            if not response:
                return None
            
            data = await response.json()
            
            if not data or 'data' not in data:
                print("Neteisingi duomenys iš trečio API")
                return None

            stats = data['data']['stats']
            
            # Konvertuojame duomenis į mūsų formatą
            result = {
                'username': username,  # Grąžiname originalų vardą
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
            
            print(f"Sėkmingai gauta statistikos iš trečio API: {result['username']}")
            return result
                
        except Exception as e:
            print(f"Klaida gaunant statistiką iš trečio API: {str(e)}")
            return None

    async def get_recent_matches(self, username: str, platform: str = "battlenet", limit: int = 5) -> Optional[List[Dict]]:
        """
        Gauna žaidėjo neseniausias žaidimas
        """
        try:
            self._check_rate_limit()
            
            clean_username = username.split('#')[0]
            cod_platform = "battle" if platform == "battlenet" else platform
            
            url = f"{self.base_url}/matches/cod/v1/mw/warzone/{clean_username}/{cod_platform}"
            print(f"Bandome gauti žaidimus iš trečio API: {url}")
            
            response = await self._make_request_with_retry(url)
            if not response:
                return None
            
            data = await response.json()
            
            if not data or 'data' not in data:
                return None

            matches = data['data']['matches']
            return matches[:limit] if matches else []
                
        except Exception as e:
            print(f"Klaida gaunant žaidimus iš trečio API: {str(e)}")
            return None

# Testavimo funkcija
async def test_third_api():
    """Testuoja trečią API"""
    print("🧪 Testuojame trečią API...")
    
    api = ThirdAPI()
    
    # Testuojame su žinomu žaidėju
    test_username = "m1nd3#2311"
    test_platform = "battlenet"
    
    print(f"📋 Testuojame: {test_username} ({test_platform})")
    
    try:
        stats = await api.get_player_stats(test_username, test_platform)
        if stats:
            print("✅ Trečias API veikia!")
            print(f"   Vardas: {stats.get('username', 'N/A')}")
            print(f"   Žudymai: {stats.get('kills', 0):,}")
            print(f"   K/D: {stats.get('kd_ratio', 0):.2f}")
            print(f"   Perėmimai: {stats.get('wins', 0):,}")
        else:
            print("❌ Trečias API nepavyko")
            
    except Exception as e:
        print(f"❌ Klaida: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_third_api()) 