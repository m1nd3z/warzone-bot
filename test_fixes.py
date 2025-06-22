#!/usr/bin/env python3
"""
Testavimo failas pataisymų patikrinimui
"""

import asyncio
import json
from tracker_api import TrackerGGAPI
from alternative_api import AlternativeAPI
from stats_fetcher import StatsFetcher

async def test_platform_normalization():
    """Testuoja platformos normalizaciją"""
    print("🧪 Testuojame platformos normalizaciją...")
    
    api = TrackerGGAPI()
    
    # Testuojame su "battle" platforma
    test_cases = [
        {"username": "m1nd3#2311", "platform": "battle"},
        {"username": "Deivid299#2888", "platform": "battlenet"},
        {"username": "TestPlayer", "platform": "psn"}
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testuojame: {test_case['username']} ({test_case['platform']})")
        
        try:
            # Tikriname ar platforma normalizuojama
            if test_case['platform'] == "battle":
                print("   Platforma 'battle' turėtų būti normalizuota į 'battlenet'")
            
            stats = await api.get_player_stats(test_case['username'], test_case['platform'])
            if stats:
                print(f"   ✅ Statistikos gavimas sėkmingas!")
                print(f"   Platforma rezultate: {stats.get('platform', 'N/A')}")
            else:
                print("   ❌ Statistikos gavimas nepavyko")
                
        except Exception as e:
            print(f"   ❌ Klaida: {str(e)}")

async def test_stats_fetcher():
    """Testuoja StatsFetcher su platformos normalizacija"""
    print("\n🔧 Testuojame StatsFetcher...")
    
    fetcher = StatsFetcher()
    
    # Testuojame su "battle" platforma
    test_username = "m1nd3#2311"
    test_platform = "battle"
    
    print(f"📝 Testuojame StatsFetcher su: {test_username} ({test_platform})")
    
    try:
        stats = await fetcher.get_player_stats(test_username, test_platform)
        
        if stats:
            print("✅ StatsFetcher veikia!")
            print(f"   Šaltinis: {stats.get('source', 'N/A')}")
            print(f"   Platforma: {stats.get('platform', 'N/A')}")
        else:
            print("❌ StatsFetcher nepavyko")
            
    except Exception as e:
        print(f"❌ Klaida: {str(e)}")

async def test_alternative_api():
    """Testuoja alternatyvų API"""
    print("\n🔄 Testuojame alternatyvų API...")
    
    api = AlternativeAPI()
    
    # Testuojame su žinomu žaidėju
    test_username = "m1nd3#2311"
    test_platform = "battlenet"
    
    print(f"📋 Testuojame: {test_username} ({test_platform})")
    
    try:
        stats = await api.get_player_stats(test_username, test_platform)
        if stats:
            print("✅ Alternatyvus API veikia!")
            print(f"   Vardas: {stats.get('username', 'N/A')}")
            print(f"   Žudymai: {stats.get('kills', 0):,}")
        else:
            print("❌ Alternatyvus API nepavyko")
            
    except Exception as e:
        print(f"❌ Klaida: {str(e)}")

async def main():
    """Pagrindinė testavimo funkcija"""
    print("🚀 Pradedame pataisymų testavimą...")
    
    try:
        # Testuojame platformos normalizaciją
        await test_platform_normalization()
        
        # Testuojame StatsFetcher
        await test_stats_fetcher()
        
        # Testuojame alternatyvų API
        await test_alternative_api()
        
        print("\n✅ Visi testai baigti!")
        
    except Exception as e:
        print(f"\n❌ Testavimo klaida: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 