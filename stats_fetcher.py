import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from activision_api import ActivisionAPI
from tracker_api import TrackerGGAPI
from alternative_api import AlternativeAPI
from third_api import ThirdAPI

class StatsFetcher:
    def __init__(self):
        """
        Inicializuoja statistikos gavimo klasę
        """
        self.activision_api = ActivisionAPI()
        self.tracker_api = TrackerGGAPI()
        self.alternative_api = AlternativeAPI()
        self.third_api = ThirdAPI()
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
            
            # 1. Pirmiausia bandome oficialų Activision API
            print(f"Bandome oficialų Activision API su {username}...")
            stats = await self.activision_api.get_player_stats(username, platform)
            
            if stats:
                # Pridedame laiko žymę
                stats['timestamp'] = datetime.now().isoformat()
                stats['source'] = 'activision_official'
                return stats
            
            # 2. Jei oficialus API nepavyko, bandome Tracker.gg API
            print(f"Oficialus API nepavyko, bandome Tracker.gg API su {username}...")
            stats = await self.tracker_api.get_player_stats(username, platform)
            
            if stats:
                # Pridedame laiko žymę
                stats['timestamp'] = datetime.now().isoformat()
                stats['source'] = 'tracker_gg'
                return stats
            
            # 3. Jei Tracker.gg nepavyko, bandome alternatyvų API
            print(f"Tracker.gg nepavyko, bandome alternatyvų API su {username}...")
            stats = await self.alternative_api.get_player_stats(username, platform)
            
            if stats:
                # Pridedame laiko žymę
                stats['timestamp'] = datetime.now().isoformat()
                stats['source'] = 'alternative_api'
                return stats
            
            # 4. Jei alternatyvus API nepavyko, bandome trečią API
            print(f"Alternatyvus API nepavyko, bandome trečią API su {username}...")
            stats = await self.third_api.get_player_stats(username, platform)
            
            if stats:
                # Pridedame laiko žymę
                stats['timestamp'] = datetime.now().isoformat()
                stats['source'] = 'third_api'
                return stats
            
            print(f"Nepavyko gauti {username} statistikos iš visų keturių API")
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
            'activision_official': "🏆",
            'tracker_gg': "🔗",
            'alternative_api': "🔄", 
            'third_api': "⚡"
        }
        source_texts = {
            'activision_official': "Oficialus Activision API",
            'tracker_gg': "Tracker.gg",
            'alternative_api': "Alternatyvus API",
            'third_api': "Trečias API"
        }
        
        source_emoji = source_emojis.get(source, "❓")
        source_text = source_texts.get(source, "Nežinomas šaltinis")
        
        # Formatuojame laiką
        time_played = stats.get('time_played', 0)
        hours = int(time_played // 3600)
        minutes = int((time_played % 3600) // 60)
        
        message = f"**🎮 {username} ({platform_display})** {source_emoji} {source_text}\n"
        message += f"📊 **Statistika:**\n"
        message += f"• 🎯 Žudymai: **{stats.get('kills', 0):,}**\n"
        message += f"• 💀 Mirtys: **{stats.get('deaths', 0):,}**\n"
        message += f"• ⚖️ K/D: **{stats.get('kd_ratio', 0):.2f}**\n"
        message += f"• 🏆 Perėmimai: **{stats.get('wins', 0):,}**\n"
        message += f"• 🥇 Top 10: **{stats.get('top_10', 0):,}**\n"
        message += f"• 🎮 Žaidimai: **{stats.get('games_played', 0):,}**\n"
        
        # Pridedame laiko informaciją tik jei ji yra
        if time_played > 0:
            message += f"• ⏱️ Žaidimo laikas: **{hours}h {minutes}m**\n"
        
        message += f"• 📈 Taškai/min: **{stats.get('score_per_minute', 0):.0f}**\n"
        
        # Pridedame papildomą informaciją tik jei ji yra ir nėra 0
        if stats.get('headshots', 0) > 0:
            message += f"• 🎯 Galvos šūviai: **{stats.get('headshots', 0):,}**\n"
        
        if stats.get('revives', 0) > 0:
            message += f"• 💚 Atgaivinimai: **{stats.get('revives', 0):,}**\n"
        
        if stats.get('longest_shot', 0) > 0:
            message += f"• 🎯 Ilgiausias šūvis: **{stats.get('longest_shot', 0):.0f}m**\n"
        
        message += f"\n🕐 Atnaujinta: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message

    def format_summary_message(self, all_stats: List[Dict]) -> str:
        """
        Formatuoja bendrą statistikos suvestinę
        """
        if not all_stats:
            return "❌ Nepavyko gauti jokios statistikos"
        
        total_kills = sum(stats.get('kills', 0) for stats in all_stats)
        total_deaths = sum(stats.get('deaths', 0) for stats in all_stats)
        total_wins = sum(stats.get('wins', 0) for stats in all_stats)
        total_games = sum(stats.get('games_played', 0) for stats in all_stats)
        
        overall_kd = total_kills / total_deaths if total_deaths > 0 else 0
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        
        message = f"**📊 BENDRA KOMANDOS STATISTIKA**\n\n"
        message += f"👥 Žaidėjų: **{len(all_stats)}**\n"
        message += f"🎯 Bendri žudymai: **{total_kills:,}**\n"
        message += f"💀 Bendros mirtys: **{total_deaths:,}**\n"
        message += f"⚖️ Bendras K/D: **{overall_kd:.2f}**\n"
        message += f"🏆 Bendri perėmimai: **{total_wins:,}**\n"
        message += f"🎮 Bendri žaidimai: **{total_games:,}**\n"
        message += f"📈 Perėmimų %: **{win_rate:.1f}%**\n\n"
        
        # Pridedame geriausius žaidėjus
        if all_stats:
            best_kd = max(all_stats, key=lambda x: x.get('kd_ratio', 0))
            most_kills = max(all_stats, key=lambda x: x.get('kills', 0))
            most_wins = max(all_stats, key=lambda x: x.get('wins', 0))
            
            message += f"**🏆 Geriausi žaidėjai:**\n"
            message += f"🥇 Geriausias K/D: **{best_kd['username']}** ({best_kd.get('kd_ratio', 0):.2f})\n"
            message += f"🥈 Daugiausiai žudymų: **{most_kills['username']}** ({most_kills.get('kills', 0):,})\n"
            message += f"🥉 Daugiausiai perėmimų: **{most_wins['username']}** ({most_wins.get('wins', 0):,})\n"
        
        message += f"\n🕐 Atnaujinta: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message

    def get_player_list(self) -> str:
        """
        Grąžina žaidėjų sąrašą
        """
        if not self.players:
            return "📝 Žaidėjų sąrašas tuščias"
        
        message = "**📝 ŽAIDĖJŲ SĄRAŠAS:**\n\n"
        
        for i, player in enumerate(self.players, 1):
            # Saugiai gauname visus laukus
            username = player.get('username', 'Nežinomas')
            status = "✅" if player.get('is_active', True) else "❌"
            platform = player.get('platform', 'battlenet')
            
            platform_names = {
                'battlenet': 'Battle.net',
                'psn': 'PlayStation',
                'xbl': 'Xbox'
            }
            platform_display = platform_names.get(platform, platform)
            
            message += f"{i}. {status} **{username}** ({platform_display})\n"
            
            if player.get('last_check'):
                try:
                    last_check = datetime.fromisoformat(player['last_check'])
                    message += f"   └─ Paskutinis patikrinimas: {last_check.strftime('%Y-%m-%d %H:%M')}\n"
                except:
                    pass  # Ignoruojame neteisingą datą
        
        return message

    def cleanup_players_data(self):
        """
        Išvalo neteisingus žaidėjų duomenis
        """
        cleaned_players = []
        
        for player in self.players:
            # Tikriname ar žaidėjas turi reikiamus laukus
            if player.get('username') and isinstance(player['username'], str):
                # Pridedame trūkstamus laukus
                if 'platform' not in player:
                    player['platform'] = 'battlenet'
                if 'added_date' not in player:
                    player['added_date'] = datetime.now().isoformat()
                if 'is_active' not in player:
                    player['is_active'] = True
                
                cleaned_players.append(player)
            else:
                print(f"Pašalinamas neteisingas žaidėjas: {player}")
        
        self.players = cleaned_players
        self.save_players()
        print(f"Išvalyta {len(cleaned_players)} žaidėjų")

# Testavimo funkcija
async def test_stats_fetcher():
    """
    Testuoja StatsFetcher funkcionalumą
    """
    fetcher = StatsFetcher()
    
    # Pridedame testinį žaidėją
    test_username = "test#1234"  # Pakeiskite į tikrą vardą
    test_platform = "battlenet"
    
    print("Testuojame StatsFetcher...")
    
    # Pridedame žaidėją
    if fetcher.add_player(test_username, test_platform):
        print("Žaidėjas pridėtas sėkmingai")
    
    # Gauname statistiką
    stats = await fetcher.get_player_stats(test_username, test_platform)
    if stats:
        print("Gauta statistikos:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
        # Formatuojame pranešimą
        message = fetcher.format_stats_message(stats)
        print("\nFormatuotas pranešimas:")
        print(message)
    else:
        print("Nepavyko gauti statistikos")
    
    # Rodyti žaidėjų sąrašą
    print("\nŽaidėjų sąrašas:")
    print(fetcher.get_player_list())

if __name__ == "__main__":
    asyncio.run(test_stats_fetcher()) 