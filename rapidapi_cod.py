#!/usr/bin/env python3
"""
RapidAPI Call of Duty Modern Warfare API implementacija
Naudoja https://rapidapi.com/elreco/api/call-of-duty-modern-warfare
"""

import aiohttp
import asyncio
from typing import Dict, Optional, List
import json
import time
import urllib.parse
import os
from dotenv import load_dotenv

# Įkeliame aplinkos kintamuosius
load_dotenv()

class RapidAPICOD:
    def __init__(self):
        """
        Inicializuoja RapidAPI COD API
        """
        # RapidAPI konfigūracija
        self.base_url = "https://call-of-duty-modern-warfare.p.rapidapi.com"
        self.api_key = os.getenv('RAPIDAPI_KEY', 'ce477eae5dmsh238966977333d6dp1065ffjsn5923ec0a9ab0')
        self.host = "call-of-duty-modern-warfare.p.rapidapi.com"
        
        # Rate limiting
        self.request_times = []
        self.max_requests_per_minute = 30  # RapidAPI limitas
        self.retry_attempts = 3
        self.retry_delay = 2
        
        # Platformų atvaizdavimas
        self.platform_map = {
            'battlenet': 'battle',
            'battle': 'battle', 
            'psn': 'psn',
            'xbl': 'xbl',
            'steam': 'steam',
            'uno': 'uno'
        }

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
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host
        }
        
        for attempt in range(self.retry_attempts):
            try:
                timeout = aiohttp.ClientTimeout(total=15)
                connector = aiohttp.TCPConnector(ssl=False)
                
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return response
                        elif response.status == 429:
                            print(f"Rate limit pasiektas (bandymas {attempt + 1}/{self.retry_attempts})")
                            if attempt < self.retry_attempts - 1:
                                wait_time = self.retry_delay * (attempt + 1) * 2
                                print(f"Palaukiame {wait_time} sekundžių...")
                                await asyncio.sleep(wait_time)
                            else:
                                return None
                        elif response.status in [400, 403, 404, 502, 503]:
                            print(f"HTTP {response.status} klaida (bandymas {attempt + 1}/{self.retry_attempts})")
                            if attempt < self.retry_attempts - 1:
                                wait_time = self.retry_delay * (attempt + 1)
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

    def _parse_warzone_stats(self, data: Dict, username: str, platform: str) -> Optional[Dict]:
        """Apdoroja Warzone statistikos duomenis"""
        try:
            if 'stats' not in data:
                return None
                
            stats = data['stats']
            
            # Gauname pagrindinę statistiką
            result = {
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
                'time_played': stats.get('timePlayed', 0),
                'source': 'rapidapi_cod'
            }
            
            # Pridedame papildomą informaciją jei yra
            if 'level' in stats:
                result['level'] = stats['level']
            if 'rank' in stats:
                result['rank'] = stats['rank']
                
            return result
            
        except Exception as e:
            print(f"Klaida apdorojant RapidAPI duomenis: {e}")
            return None

    async def get_player_stats(self, username: str, platform: str = "battlenet") -> Optional[Dict]:
        """
        Gauna žaidėjo Warzone statistiką iš RapidAPI
        """
        try:
            self._check_rate_limit()
            
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            # Pašaliname # ir viską po jo
            clean_username = username.split('#')[0]
            
            # Nustatome platformą pagal API
            api_platform = self.platform_map.get(platform, platform)
            
            # Formatuojame URL
            url = f"{self.base_url}/warzone/{urllib.parse.quote(clean_username)}/{api_platform}"
            
            print(f"RapidAPI užklausa: {url}")
            
            response = await self._make_request_with_retry(url)
            if not response:
                print(f"RapidAPI nepavyko gauti duomenų")
                return None
            
            data = await response.json()
            
            # Apdoroja duomenis
            result = self._parse_warzone_stats(data, username, platform)
            
            if result:
                print(f"Sėkmingai gauta statistikos iš RapidAPI: {result['username']}")
                return result
            else:
                print(f"Nepavyko apdoroti RapidAPI duomenų")
                return None
                
        except Exception as e:
            print(f"Klaida gaunant statistiką iš RapidAPI: {str(e)}")
            return None

    async def get_recent_matches(self, username: str, platform: str = "battlenet", limit: int = 5) -> Optional[List[Dict]]:
        """
        Gauna žaidėjo neseniausias žaidimas (jei palaikoma)
        """
        try:
            self._check_rate_limit()
            
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            # Pašaliname # ir viską po jo
            clean_username = username.split('#')[0]
            
            # Nustatome platformą pagal API
            api_platform = self.platform_map.get(platform, platform)
            
            # Formatuojame URL
            url = f"{self.base_url}/matches/{urllib.parse.quote(clean_username)}/{api_platform}"
            
            response = await self._make_request_with_retry(url)
            if not response:
                return None
            
            data = await response.json()
            
            # Apdoroja duomenis (paprastas formatas)
            if 'matches' in data:
                matches = data['matches'][:limit]
                return matches
            
            return None
            
        except Exception as e:
            print(f"Klaida gaunant žaidimus iš RapidAPI: {str(e)}")
            return None

    async def get_player_info(self, username: str, platform: str = "battlenet") -> Optional[Dict]:
        """
        Gauna žaidėjo pagrindinę informaciją
        """
        try:
            self._check_rate_limit()
            
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            # Pašaliname # ir viską po jo
            clean_username = username.split('#')[0]
            
            # Nustatome platformą pagal API
            api_platform = self.platform_map.get(platform, platform)
            
            # Formatuojame URL
            url = f"{self.base_url}/profile/{urllib.parse.quote(clean_username)}/{api_platform}"
            
            response = await self._make_request_with_retry(url)
            if not response:
                return None
            
            data = await response.json()
            
            # Apdoroja duomenis
            if 'data' in data:
                profile = data['data']
                return {
                    'username': username,
                    'platform': platform,
                    'level': profile.get('level', 0),
                    'rank': profile.get('rank', ''),
                    'prestige': profile.get('prestige', 0),
                    'source': 'rapidapi_cod'
                }
            
            return None
            
        except Exception as e:
            print(f"Klaida gaunant žaidėjo informaciją iš RapidAPI: {str(e)}")
            return None

# Testavimo funkcija
async def test_rapidapi_cod():
    """Testuoja RapidAPI COD API"""
    print("🧪 Testuojame RapidAPI COD API...")
    
    api = RapidAPICOD()
    
    # Testuojame su žinomu žaidėju
    test_username = "m1nd3#2311"
    test_platform = "battlenet"
    
    print(f"�� Testuojame: {test_username} ({test_platform})")
    
    try:
        # Testuojame statistiką
        stats = await api.get_player_stats(test_username, test_platform)
        if stats:
            print("✅ RapidAPI COD API veikia!")
            print(f"   Vardas: {stats.get('username', 'N/A')}")
            print(f"   Žudymai: {stats.get('kills', 0):,}")
            print(f"   K/D: {stats.get('kd_ratio', 0):.2f}")
            print(f"   Perėmimai: {stats.get('wins', 0):,}")
            print(f"   Žaidimai: {stats.get('games_played', 0):,}")
        else:
            print("❌ RapidAPI COD API nepavyko gauti statistikos")
        
        # Testuojame žaidėjo informaciją
        print("\n�� Testuojame žaidėjo informaciją...")
        info = await api.get_player_info(test_username, test_platform)
        if info:
            print("✅ Žaidėjo informacija gauta!")
            print(f"   Lygis: {info.get('level', 'N/A')}")
            print(f"   Rangas: {info.get('rank', 'N/A')}")
        else:
            print("❌ Nepavyko gauti žaidėjo informacijos")
            
    except Exception as e:
        print(f"❌ Klaida testuojant RapidAPI COD API: {e}")

if __name__ == "__main__":
    asyncio.run(test_rapidapi_cod())