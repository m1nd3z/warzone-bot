import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from reliable_api import ReliableAPI
from tracker_api import TrackerGGAPI
from alternative_api import AlternativeAPI
from third_api import ThirdAPI
from rapidapi_cod import RapidAPICOD

class StatsFetcher:
    def __init__(self):
        """
        Inicializuoja statistikos gavimo klasę
        """
        self.reliable_api = ReliableAPI()
        self.tracker_api = TrackerGGAPI()
        self.alternative_api = AlternativeAPI()
        self.third_api = ThirdAPI()
        self.rapidapi_cod = RapidAPICOD()
        self.players_file = "players.json"
        self.stats_history_file = "stats_history.json"
        self.load_players()

    def load_players(self):
        """
        Užkrauna žaidėjų sąrašą iš failo
        """
        try:
            if os.path.exists(self.players_file):
                with open(self.players_file, 'r', encoding='utf-8') as f:
                    self.players = json.load(f)
                # Išvalome duomenis
                self.cleanup_players_data()
            else:
                self.players = []
                self.save_players()
        except Exception as e:
            print(f"Klaida užkraunant žaidėjus: {e}")
            self.players = []
            self.save_players()

    def save_players(self):
        """
        Išsaugo žaidėjų sąrašą į failą
        """
        try:
            with open(self.players_file, 'w', encoding='utf-8') as f:
                json.dump(self.players, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Klaida išsaugant žaidėjus: {e}")

    def add_player(self, username: str, platform: str = "battlenet") -> bool:
        """
        Prideda naują žaidėją į sąrašą
        """
        # Patikriname, ar žaidėjas jau yra sąraše
        for player in self.players:
            if player['username'] == username and player['platform'] == platform:
                print(f"Žaidėjas {username} jau yra sąraše")
                return False

        # Pridedame naują žaidėją
        new_player = {
            'username': username,
            'platform': platform,
            'added_date': datetime.now().isoformat(),
            'last_check': None,
            'is_active': True
        }
        
        self.players.append(new_player)
        self.save_players()
        print(f"Pridėtas žaidėjas: {username} ({platform})")
        return True

    def remove_player(self, username: str, platform: str = "battlenet") -> bool:
        """
        Pašalina žaidėją iš sąrašo
        """
        for i, player in enumerate(self.players):
            player_platform = player.get('platform', 'battlenet')
            if player['username'] == username and player_platform == platform:
                removed_player = self.players.pop(i)
                self.save_players()
                print(f"Pašalintas žaidėjas: {username} ({platform})")
                return True
        
        print(f"Žaidėjas {username} nerastas sąraše")
        return False

    async def get_player_stats(self, username: str, platform: str = "battlenet") -> Optional[Dict]:
        """
        Gauna vieno žaidėjo statistiką su fallback į visus API
        """
        try:
            # Normalizuojame platformą
            if platform == "battle":
                platform = "battlenet"
            
            # 1. Pirmiausia bandome RapidAPI COD (naujas, patikimas)
            print(f"Bandome RapidAPI COD su {username}...")
            stats = await self.rapidapi_cod.get_player_stats(username, platform)
            
            if stats:
                # Pridedame laiko žymę
                stats['timestamp'] = datetime.now().isoformat()
                stats['source'] = 'rapidapi_cod'
                return stats
            
            # 2. Jei RapidAPI nepavyko, bandome patikimą API (su fallback duomenimis)
            print(f"RapidAPI nepavyko, bandome patikimą API su {username}...")
            stats = await self.reliable_api.get_player_stats(username, platform)
            
            if stats:
                # Pridedame laiko žymę
                stats['timestamp'] = datetime.now().isoformat()
                if stats.get('is_fallback'):
                    stats['source'] = 'fallback_data'
                else:
                    stats['source'] = 'reliable_api'
                return stats
            
            # 3. Jei patikimas API nepavyko, bandome Tracker.gg API
            print(f"Patikimas API nepavyko, bandome Tracker.gg API su {username}...")
            stats = await self.tracker_api.get_player_stats(username, platform)
            
            if stats:
                # Pridedame laiko žymę
                stats['timestamp'] = datetime.now().isoformat()
                stats['source'] = 'tracker_gg'
                return stats
            
            # 4. Jei Tracker.gg nepavyko, bandome alternatyvų API
            print(f"Tracker.gg nepavyko, bandome alternatyvų API su {username}...")
            stats = await self.alternative_api.get_player_stats(username, platform)
            
            if stats:
                # Pridedame laiko žymę
                stats['timestamp'] = datetime.now().isoformat()
                stats['source'] = 'alternative_api'
                return stats
            
            # 5. Jei alternatyvus API nepavyko, bandome trečią API
            print(f"Alternatyvus API nepavyko, bandome trečią API su {username}...")
            stats = await self.third_api.get_player_stats(username, platform)
            
            if stats:
                # Pridedame laiko žymę
                stats['timestamp'] = datetime.now().isoformat()
                stats['source'] = 'third_api'
                return stats
            
            print(f"Nepavyko gauti {username} statistikos iš jokio API")
            return None
            
        except Exception as e:
            print(f"Klaida gaunant {username} statistiką: {e}")
            return None

    async def get_all_players_stats(self) -> List[Dict]:
        """
        Gauna visų aktyvių žaidėjų statistiką
        """
        all_stats = []
        
        for player in self.players:
            # Saugiai tikriname ar žaidėjas turi reikiamus laukus
            if not player.get('username'):
                print(f"Praleidžiame žaidėją be vardo: {player}")
                continue
            
            if player.get('is_active', True):
                platform = player.get('platform', 'battlenet')
                username = player['username']
                print(f"Gauname {username} statistiką...")
                stats = await self.get_player_stats(username, platform)
                
                if stats:
                    # Atnaujiname paskutinio patikrinimo laiką
                    player['last_check'] = datetime.now().isoformat()
                    # Atnaujiname platformą jei jos nebuvo
                    if 'platform' not in player:
                        player['platform'] = platform
                    all_stats.append(stats)
                else:
                    print(f"Nepavyko gauti {username} statistikos")
                
                # Palaukiame tarp užklausų, kad neviršytume rate limit
                await asyncio.sleep(1)
        
        # Išsaugome atnaujintą žaidėjų sąrašą
        self.save_players()
        return all_stats

    def format_stats_message(self, stats: Dict) -> str:
        """
        Formatuoja statistikos pranešimą Discord
        """
        username = stats.get('username', 'Nežinomas')
        platform = stats.get('platform', 'Nežinoma')
        source = stats.get('source', 'unknown')
        
        # Konvertuojame platformos pavadinimus
        platform_names = {
            'battlenet': 'Battle.net',
            'psn': 'PlayStation',
            'xbl': 'Xbox'
        }
        platform_display = platform_names.get(platform, platform)
        
        # Nustatome API šaltinio emoji ir tekstą
        source_emojis = {
            'reliable_api': "🚀",
            'fallback_data': "⚠️",
            'tracker_gg': "🔗",
            'alternative_api': "🔄", 
            'third_api': "⚡"
        }
        source_texts = {
            'reliable_api': "Patikimas API",
            'fallback_data': "Fallback duomenys",
            'tracker_gg': "Tracker.gg",
            'alternative_api': "Alternatyvus API",
            'third_api': "Trečias API"
        }
        
        source_emoji = source_emojis.get(source, "❓")
        source_text = source_texts.get(source, "Nežinomas šaltinis")
        
        # Formatuojame statistiką
        kills = stats.get('kills', 0)
        deaths = stats.get('deaths', 0)
        kd_ratio = stats.get('kd_ratio', 0)
        wins = stats.get('wins', 0)
        top_10 = stats.get('top_10', 0)
        games_played = stats.get('games_played', 0)
        score_per_minute = stats.get('score_per_minute', 0)
        
        # Konvertuojame laiką į skaitomą formatą
        time_played = stats.get('time_played', 0)
        if time_played > 0:
            hours = int(time_played // 3600)
            minutes = int((time_played % 3600) // 60)
            time_display = f"{hours}h {minutes}m"
        else:
            time_display = "N/A"
        
        # Pridedame fallback įspėjimą
        fallback_warning = ""
        if source == 'fallback_data':
            fallback_warning = "\n⚠️ **Pastaba:** Naudojami fallback duomenys (API nepasiekiami)"
        
        message = f"""
{source_emoji} **{username}** ({platform_display}) - {source_text}

📊 **Statistika:**
• 🎯 Žudymai: **{kills:,}**
• 💀 Mirtys: **{deaths:,}**
• ⚖️ K/D santykis: **{kd_ratio:.2f}**
• 🏆 Perėmimai: **{wins:,}**
• 🥇 Top 10: **{top_10:,}**
• 🎮 Žaidimai: **{games_played:,}**
• ⏱️ Laikas: **{time_display}**
• 📈 Taškai/min: **{score_per_minute:.1f}**{fallback_warning}
"""
        
        return message.strip()

    def format_summary_message(self, all_stats: List[Dict]) -> str:
        """
        Formatuoja suvestinės pranešimą Discord
        """
        if not all_stats:
            return "❌ Nepavyko gauti jokios statistikos"
        
        # Rūšiuojame pagal žudymus
        sorted_stats = sorted(all_stats, key=lambda x: x.get('kills', 0), reverse=True)
        
        message = "📊 **Žaidėjų statistikos suvestinė:**\n\n"
        
        for i, stats in enumerate(sorted_stats[:10], 1):  # Top 10
            username = stats.get('username', 'Nežinomas')
            kills = stats.get('kills', 0)
            kd_ratio = stats.get('kd_ratio', 0)
            wins = stats.get('wins', 0)
            
            # Emoji pagal poziciją
            if i == 1:
                position_emoji = "🥇"
            elif i == 2:
                position_emoji = "🥈"
            elif i == 3:
                position_emoji = "🥉"
            else:
                position_emoji = f"{i}."
            
            message += f"{position_emoji} **{username}** - 🎯 {kills:,} | ⚖️ {kd_ratio:.2f} | 🏆 {wins:,}\n"
        
        if len(sorted_stats) > 10:
            message += f"\n... ir dar {len(sorted_stats) - 10} žaidėjų"
        
        # Pridedame fallback įspėjimą jei yra
        fallback_count = sum(1 for stats in all_stats if stats.get('source') == 'fallback_data')
        if fallback_count > 0:
            message += f"\n\n⚠️ **Pastaba:** {fallback_count} žaidėjų duomenys iš fallback šaltinio"
        
        return message.strip()

    def get_player_list(self) -> str:
        """
        Grąžina žaidėjų sąrašą kaip tekstą
        """
        if not self.players:
            return "📋 Žaidėjų sąrašas tuščias"
        
        message = "📋 **Žaidėjų sąrašas:**\n\n"
        
        for i, player in enumerate(self.players, 1):
            username = player.get('username', 'Nežinomas')
            platform = player.get('platform', 'battlenet')
            is_active = player.get('is_active', True)
            
            # Konvertuojame platformos pavadinimus
            platform_names = {
                'battlenet': 'Battle.net',
                'psn': 'PlayStation',
                'xbl': 'Xbox'
            }
            platform_display = platform_names.get(platform, platform)
            
            status_emoji = "✅" if is_active else "❌"
            message += f"{i}. {status_emoji} **{username}** ({platform_display})\n"
        
        return message.strip()

    def cleanup_players_data(self):
        """
        Išvalo žaidėjų duomenis nuo neteisingų įrašų
        """
        cleaned_players = []
        
        for player in self.players:
            # Tikriname ar žaidėjas turi reikiamus laukus
            if not player.get('username'):
                print(f"Praleidžiame žaidėją be vardo: {player}")
                continue
            
            # Pridedame trūkstamus laukus
            if 'platform' not in player:
                player['platform'] = 'battlenet'
            if 'added_date' not in player:
                player['added_date'] = datetime.now().isoformat()
            if 'is_active' not in player:
                player['is_active'] = True
            
            cleaned_players.append(player)
        
        self.players = cleaned_players
        self.save_players()

# Testavimo funkcija
async def test_stats_fetcher():
    """Testuoja statistikos gavimo funkcionalumą"""
    print("🧪 Testuojame statistikos gavimą...")
    
    fetcher = StatsFetcher()
    
    # Testuojame su žinomu žaidėju
    test_username = "m1nd3#2311"
    test_platform = "battlenet"
    
    print(f"📋 Testuojame: {test_username} ({test_platform})")
    
    try:
        stats = await fetcher.get_player_stats(test_username, test_platform)
        if stats:
            print("✅ Statistikos gavimas veikia!")
            print(f"   Vardas: {stats.get('username', 'N/A')}")
            print(f"   Žudymai: {stats.get('kills', 0):,}")
            print(f"   K/D: {stats.get('kd_ratio', 0):.2f}")
            print(f"   Šaltinis: {stats.get('source', 'N/A')}")
            
            # Testuojame pranešimo formatavimą
            message = fetcher.format_stats_message(stats)
            print("\n📝 Formatuotas pranešimas:")
            print(message)
        else:
            print("❌ Statistikos gavimas nepavyko")
            
    except Exception as e:
        print(f"❌ Klaida testuojant statistikos gavimą: {e}")

if __name__ == "__main__":
    asyncio.run(test_stats_fetcher()) 