#!/usr/bin/env python3
"""
Oficialus Activision API - naudojant call-of-duty-api biblioteką
"""

import asyncio
import json
import time
import os
import subprocess
from typing import Dict, Optional, List

class ActivisionAPI:
    def __init__(self, sso_token: str = None):
        """
        Inicializuoja oficialų Activision API
        :param sso_token: Activision SSO token (neprivalomas)
        """
        self.sso_token = sso_token or os.getenv('ACT_SSO_COOKIE') or os.getenv('COD_SSO')
        self.request_times = []
        self.max_requests_per_minute = 20
        self.retry_attempts = 3
        self.retry_delay = 2

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

    async def _run_node_script(self, script_content: str) -> Optional[Dict]:
        """Paleidžia Node.js skriptą ir grąžina rezultatą"""
        try:
            # Sukuriame laikiną .js failą
            script_file = "temp_activision_script.js"
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Paleidžiame Node.js skriptą
            result = subprocess.run(
                ['node', script_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Išvalome laikiną failą
            if os.path.exists(script_file):
                os.remove(script_file)
            
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
            else:
                print(f"Node.js klaida: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Node.js skriptas užtruko per ilgai")
            return None
        except Exception as e:
            print(f"Klaida paleidžiant Node.js skriptą: {str(e)}")
            return None

    async def get_player_stats(self, username: str, platform: str = "battlenet") -> Optional[Dict]:
        """
        Gauna žaidėjo statistiką iš oficialaus Activision API
        """
        try:
            self._check_rate_limit()
            
            if not self.sso_token:
                print("❌ COD_SSO token nerastas!")
                return None
            
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            # Pašaliname # ir viską po jo
            clean_username = username.split('#')[0]
            
            # Nustatome platformą pagal Activision API
            cod_platform = "battle" if platform == "battlenet" else platform
            
            print(f"Bandome gauti statistiką iš oficialaus Activision API: {clean_username} ({cod_platform})")
            
            # Node.js skriptas žaidėjo statistikos gavimui
            script = f"""
const cod = require('call-of-duty-api')();

async function getPlayerStats() {{
    try {{
        // Prisijungiame su SSO token
        await cod.login('{self.sso_token}');
        
        // Ieškome žaidėjo
        const player = await cod.findPlayer('{clean_username}', '{cod_platform}');
        
        if (!player) {{
            console.log(JSON.stringify({{ error: 'Žaidėjas nerastas' }}));
            return;
        }}
        
        // Gauname žaidėjo statistiką
        const stats = await cod.MWcombatwz(player.username, player.platform);
        
        // Formatuojame rezultatą
        const result = {{
            username: player.username,
            platform: player.platform,
            kills: stats.lifetime.all.properties.kills || 0,
            deaths: stats.lifetime.all.properties.deaths || 0,
            wins: stats.lifetime.all.properties.wins || 0,
            games_played: stats.lifetime.all.properties.gamesPlayed || 0,
            kd_ratio: stats.lifetime.all.properties.kdRatio || 0,
            avg_life: stats.lifetime.all.properties.avgLifeTime || 0,
            score_per_minute: stats.lifetime.all.properties.scorePerMinute || 0,
            damage_done: stats.lifetime.all.properties.damageDone || 0,
            damage_taken: stats.lifetime.all.properties.damageTaken || 0,
            headshots: stats.lifetime.all.properties.headshots || 0,
            accuracy: stats.lifetime.all.properties.accuracy || 0,
            source: 'Activision API'
        }};
        
        console.log(JSON.stringify(result));
        
    }} catch (error) {{
        console.log(JSON.stringify({{ error: error.message }}));
    }}
}}

getPlayerStats();
"""
            
            result = await self._run_node_script(script)
            
            if result and 'error' not in result:
                print("✅ Oficialus Activision API sėkmingas!")
                return result
            else:
                error_msg = result.get('error', 'Nežinoma klaida') if result else 'Nepavyko gauti duomenų'
                print(f"❌ Oficialus Activision API klaida: {error_msg}")
                return None
                
        except Exception as e:
            print(f"Klaida gaunant statistiką iš oficialaus Activision API: {str(e)}")
            return None

    async def search_player(self, username: str, platform: str = "battlenet") -> Optional[Dict]:
        """
        Ieško žaidėjo pagal vardą
        """
        try:
            self._check_rate_limit()
            
            if not self.sso_token:
                print("❌ COD_SSO token nerastas!")
                return None
            
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            # Pašaliname # ir viską po jo
            clean_username = username.split('#')[0]
            
            # Nustatome platformą pagal Activision API
            cod_platform = "battle" if platform == "battlenet" else platform
            
            print(f"Ieškome žaidėjo: {clean_username} ({cod_platform})")
            
            # Node.js skriptas žaidėjo paieškai
            script = f"""
const cod = require('call-of-duty-api')();

async function searchPlayer() {{
    try {{
        // Prisijungiame su SSO token
        await cod.login('{self.sso_token}');
        
        // Ieškome žaidėjo
        const player = await cod.findPlayer('{clean_username}', '{cod_platform}');
        
        if (player) {{
            const result = {{
                username: player.username,
                platform: player.platform,
                found: true
            }};
            console.log(JSON.stringify(result));
        }} else {{
            console.log(JSON.stringify({{ found: false, error: 'Žaidėjas nerastas' }}));
        }}
        
    }} catch (error) {{
        console.log(JSON.stringify({{ found: false, error: error.message }}));
    }}
}}

searchPlayer();
"""
            
            result = await self._run_node_script(script)
            
            if result and result.get('found', False):
                print("✅ Žaidėjas rastas!")
                return result
            else:
                error_msg = result.get('error', 'Nežinoma klaida') if result else 'Nepavyko rasti žaidėjo'
                print(f"❌ Žaidėjo paieškos klaida: {error_msg}")
                return None
                
        except Exception as e:
            print(f"Klaida ieškant žaidėjo: {str(e)}")
            return None

# Testavimo funkcija
async def test_activision_api():
    """Testuoja oficialų Activision API"""
    print("🧪 Testuojame oficialų Activision API...")
    
    # Patikriname ar yra SSO token
    sso_token = os.getenv('ACT_SSO_COOKIE') or os.getenv('COD_SSO')
    if not sso_token:
        print("❌ ACT_SSO_COOKIE arba COD_SSO aplinkos kintamasis nerastas!")
        print("Nustatykite ACT_SSO_COOKIE aplinkos kintamąjį su savo Activision SSO token")
        print("Pavyzdys: export ACT_SSO_COOKIE='your_sso_token_here'")
        return
    
    api = ActivisionAPI(sso_token)
    
    # Testuojame žaidėjo paiešką
    test_username = "m1nd3#2311"
    test_platform = "battlenet"
    
    print(f"📋 Testuojame žaidėjo paiešką: {test_username}")
    
    try:
        # Pirma ieškome žaidėjo
        player = await api.search_player(test_username, test_platform)
        if player:
            print("✅ Žaidėjas rastas!")
            print(f"   Vardas: {player.get('username', 'N/A')}")
            print(f"   Platforma: {player.get('platform', 'N/A')}")
            
            # Tada gauname statistiką
            print(f"\n📊 Gauname statistiką...")
            stats = await api.get_player_stats(test_username, test_platform)
            
            if stats:
                print("✅ Statistikos gavimas sėkmingas!")
                print(f"   Žudymai: {stats.get('kills', 0):,}")
                print(f"   Mirtys: {stats.get('deaths', 0):,}")
                print(f"   K/D: {stats.get('kd_ratio', 0):.2f}")
                print(f"   Perėmimai: {stats.get('wins', 0):,}")
                print(f"   Žaidimai: {stats.get('games_played', 0):,}")
            else:
                print("❌ Statistikos gavimas nepavyko")
        else:
            print("❌ Žaidėjas nerastas")
            
    except Exception as e:
        print(f"❌ Klaida: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_activision_api()) 