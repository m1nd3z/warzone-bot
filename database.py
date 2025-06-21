import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class WarzoneDatabase:
    def __init__(self, db_path: str = "warzone_stats.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializuoja duomenų bazę su visomis reikalingomis lentelėmis"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS players(
                    player_uno_id TEXT PRIMARY KEY UNIQUE,
                    player_id TEXT NOT NULL,
                    activision_tag TEXT,
                    is_core BOOLEAN NOT NULL DEFAULT 0 CHECK(is_core IN(0, 1))
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS raw_games(
                    game_id TEXT NOT NULL,
                    player_uno_id TEXT NOT NULL,
                    stats BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (game_id, player_uno_id),
                    FOREIGN KEY (player_uno_id)
                        REFERENCES players (player_uno_id)
                            ON DELETE CASCADE
                            ON UPDATE NO ACTION
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wz_valid_games(
                    date_key TEXT NOT NULL,
                    game_mode TEXT NOT NULL CHECK(game_mode IN ('mp', 'wz')),
                    game_mode_sub TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    player_uno_id TEXT NOT NULL,
                    numberOfPlayers INTEGER NOT NULL CHECK(numberOfPlayers > 0),
                    numberOfTeams INTEGER NOT NULL CHECK(numberOfTeams > 0),
                    score INTEGER NOT NULL,
                    scorePerMinute REAL NOT NULL,
                    kills INTEGER NOT NULL,
                    deaths INTEGER NOT NULL,
                    damageDone INTEGER NOT NULL,
                    damageTaken INTEGER NOT NULL,
                    gulagKills INTEGER NOT NULL,
                    gulagDeaths INTEGER NOT NULL,
                    teamPlacement INTEGER NOT NULL CHECK(teamPlacement > 0),
                    kdRatio REAL NOT NULL,
                    distanceTraveled REAL NOT NULL,
                    headshots INTEGER NOT NULL,
                    objectiveBrCacheOpen INTEGER NOT NULL,
                    objectiveReviver INTEGER NOT NULL,
                    objectiveBrDownAll INTEGER NOT NULL,
                    objectiveDestroyedVehicleAll INTEGER NOT NULL,
                    stats BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (game_id, player_uno_id),
                    FOREIGN KEY (player_uno_id)
                        REFERENCES players (player_uno_id)
                            ON DELETE CASCADE
                            ON UPDATE NO ACTION
                )
            """)
            
            # Sukuriame indeksus greitesniam paieškai
            conn.execute("CREATE INDEX IF NOT EXISTS idx_players_player_id ON players(player_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_wz_valid_games_player_uno_id ON wz_valid_games(player_uno_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_wz_valid_games_date_key ON wz_valid_games(date_key)")
            
            conn.commit()
    
    def seed_players(self, players_data: List[Dict]):
        """Prideda žaidėjus iš JSON duomenų"""
        with sqlite3.connect(self.db_path) as conn:
            for player in players_data:
                player_id = player['name'].lower()
                is_core = player.get('isCore', False)
                
                for account in player['accounts']:
                    uno_id = account['unoId']
                    activision_tag = account['activisionTag']
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO players(player_uno_id, player_id, activision_tag, is_core)
                        VALUES (?, ?, ?, ?)
                    """, (uno_id, player_id, activision_tag, is_core))
            
            conn.commit()
    
    def add_player(self, player_id: str, uno_id: str, activision_tag: str, is_core: bool = False):
        """Prideda naują žaidėją"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO players(player_uno_id, player_id, activision_tag, is_core)
                VALUES (?, ?, ?, ?)
            """, (uno_id, player_id.lower(), activision_tag, is_core))
            conn.commit()
    
    def get_player_by_name(self, player_name: str) -> Optional[Dict]:
        """Gauna žaidėją pagal vardą"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT player_uno_id, player_id, activision_tag, is_core
                FROM players
                WHERE player_id = ?
            """, (player_name.lower(),))
            
            row = cursor.fetchone()
            if row:
                return {
                    'uno_id': row[0],
                    'player_id': row[1],
                    'activision_tag': row[2],
                    'is_core': bool(row[3])
                }
            return None
    
    def get_all_players(self) -> List[Dict]:
        """Gauna visus žaidėjus"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT player_uno_id, player_id, activision_tag, is_core
                FROM players
                ORDER BY player_id
            """)
            
            return [
                {
                    'uno_id': row[0],
                    'player_id': row[1],
                    'activision_tag': row[2],
                    'is_core': bool(row[3])
                }
                for row in cursor.fetchall()
            ]
    
    def save_game_stats(self, game_id: str, player_uno_id: str, stats: Dict):
        """Išsaugo žaidimo statistiką"""
        with sqlite3.connect(self.db_path) as conn:
            stats_json = json.dumps(stats)
            conn.execute("""
                INSERT OR REPLACE INTO raw_games(game_id, player_uno_id, stats)
                VALUES (?, ?, ?)
            """, (game_id, player_uno_id, stats_json))
            conn.commit()
    
    def get_player_recent_stats(self, player_name: str, days: int = 7) -> List[Dict]:
        """Gauna žaidėjo statistiką per paskutines dienas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    date_key,
                    game_mode_sub,
                    kills,
                    deaths,
                    damageDone,
                    teamPlacement,
                    kdRatio,
                    scorePerMinute,
                    headshots,
                    distanceTraveled
                FROM wz_valid_games wvg
                JOIN players p ON p.player_uno_id = wvg.player_uno_id
                WHERE p.player_id = ? 
                AND date_key >= datetime('now', '-{} days')
                ORDER BY date_key DESC
            """.format(days), (player_name.lower(),))
            
            return [
                {
                    'date': row[0],
                    'mode': row[1],
                    'kills': row[2],
                    'deaths': row[3],
                    'damage': row[4],
                    'placement': row[5],
                    'kd_ratio': row[6],
                    'score_per_minute': row[7],
                    'headshots': row[8],
                    'distance': row[9]
                }
                for row in cursor.fetchall()
            ]
    
    def get_player_summary_stats(self, player_name: str, days: int = 7) -> Dict:
        """Gauna žaidėjo suvestinę statistiką"""
        recent_stats = self.get_player_recent_stats(player_name, days)
        
        if not recent_stats:
            return {}
        
        total_games = len(recent_stats)
        total_kills = sum(stat['kills'] for stat in recent_stats)
        total_deaths = sum(stat['deaths'] for stat in recent_stats)
        total_damage = sum(stat['damage'] for stat in recent_stats)
        wins = sum(1 for stat in recent_stats if stat['placement'] == 1)
        top_5 = sum(1 for stat in recent_stats if stat['placement'] <= 5)
        top_10 = sum(1 for stat in recent_stats if stat['placement'] <= 10)
        
        avg_kd = total_kills / total_deaths if total_deaths > 0 else total_kills
        avg_damage = total_damage / total_games
        win_rate = (wins / total_games) * 100 if total_games > 0 else 0
        
        return {
            'total_games': total_games,
            'total_kills': total_kills,
            'total_deaths': total_deaths,
            'total_damage': total_damage,
            'wins': wins,
            'top_5': top_5,
            'top_10': top_10,
            'avg_kd': round(avg_kd, 2),
            'avg_damage': round(avg_damage, 0),
            'win_rate': round(win_rate, 1)
        }
    
    def get_team_stats(self, player_names: List[str], days: int = 7) -> Dict:
        """Gauna komandos statistiką"""
        team_stats = []
        for player_name in player_names:
            player_summary = self.get_player_summary_stats(player_name, days)
            if player_summary:
                player_summary['player_name'] = player_name
                team_stats.append(player_summary)
        
        if not team_stats:
            return {}
        
        total_games = max(stat['total_games'] for stat in team_stats)
        total_kills = sum(stat['total_kills'] for stat in team_stats)
        total_deaths = sum(stat['total_deaths'] for stat in team_stats)
        total_wins = sum(stat['wins'] for stat in team_stats)
        
        return {
            'players': team_stats,
            'total_games': total_games,
            'total_kills': total_kills,
            'total_deaths': total_deaths,
            'total_wins': total_wins,
            'team_kd': round(total_kills / total_deaths, 2) if total_deaths > 0 else total_kills,
            'win_rate': round((total_wins / total_games) * 100, 1) if total_games > 0 else 0
        } 