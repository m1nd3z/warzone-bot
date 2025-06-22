#!/usr/bin/env python3
"""
Testavimo failas tracker.gg API
"""

import asyncio
import json
from tracker_api import TrackerGGAPI
from stats_fetcher import StatsFetcher

async def test_tracker_api():
    """Testuoja Tracker.gg API funkcionalumą"""
    print("🧪 Testuojame Tracker.gg API...")
    
    api = TrackerGGAPI()
    
    # Testuojame su žinomu žaidėju (pakeiskite į tikrą vardą)
    test_cases = [
        {"username": "test#1234", "platform": "battlenet"},
        {"username": "TestPlayer", "platform": "psn"},
        {"username": "TestGamer", "platform": "xbl"}
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testuojame: {test_case['username']} ({test_case['platform']})")
        
        try:
            # Gauname statistiką
            stats = await api.get_player_stats(test_case['username'], test_case['platform'])
            if stats:
                print("✅ Statistikos gavimas sėkmingas!")
                print(f"   Vardas: {stats.get('username', 'N/A')}")
                print(f"   Žudymai: {stats.get('kills', 0):,}")
                print(f"   Mirtys: {stats.get('deaths', 0):,}")
                print(f"   K/D: {stats.get('kd_ratio', 0):.2f}")
                print(f"   Perėmimai: {stats.get('wins', 0):,}")
            else:
                print("❌ Statistikos gavimas nepavyko")
                
        except Exception as e:
            print(f"❌ Klaida: {str(e)}")

async def test_stats_fetcher():
    """Testuoja StatsFetcher funkcionalumą"""
    print("\n🔧 Testuojame StatsFetcher...")
    
    fetcher = StatsFetcher()
    
    # Testuojame žaidėjų pridėjimą
    test_username = "TestPlayer#1234"
    test_platform = "battlenet"
    
    print(f"📝 Pridedame žaidėją: {test_username}")
    if fetcher.add_player(test_username, test_platform):
        print("✅ Žaidėjas pridėtas sėkmingai")
    else:
        print("❌ Žaidėjo pridėjimas nepavyko")
    
    # Rodyti žaidėjų sąrašą
    print("\n📋 Žaidėjų sąrašas:")
    print(fetcher.get_player_list())
    
    # Testuojame statistikos gavimą
    print(f"\n📊 Gauname {test_username} statistiką...")
    stats = await fetcher.get_player_stats(test_username, test_platform)
    
    if stats:
        print("✅ Statistikos gavimas sėkmingas!")
        message = fetcher.format_stats_message(stats)
        print("\n📝 Formatuotas pranešimas:")
        print(message)
    else:
        print("❌ Statistikos gavimas nepavyko")

async def test_rate_limiting():
    """Testuoja rate limiting funkcionalumą"""
    print("\n⏱️ Testuojame rate limiting...")
    
    api = TrackerGGAPI()
    
    # Bandome daug užklausų iš eilės
    test_username = "TestPlayer#1234"
    
    for i in range(5):
        print(f"   Užklausa {i+1}/5...")
        stats = await api.get_player_stats(test_username, "battlenet")
        if stats:
            print(f"   ✅ Užklausa {i+1} sėkminga")
        else:
            print(f"   ❌ Užklausa {i+1} nepavyko")
        
        # Trumpa pauzė tarp užklausų
        await asyncio.sleep(1)

async def main():
    """Pagrindinė testavimo funkcija"""
    print("🚀 Pradedame tracker.gg API testavimą...")
    
    try:
        # Testuojame pagrindinį API
        await test_tracker_api()
        
        # Testuojame StatsFetcher
        await test_stats_fetcher()
        
        # Testuojame rate limiting
        await test_rate_limiting()
        
        print("\n✅ Visi testai baigti!")
        
    except Exception as e:
        print(f"\n❌ Testavimo klaida: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 