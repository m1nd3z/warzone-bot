#!/usr/bin/env python3
"""
Testavimo failas HTTP 403 klaidos sprendimui
"""

import asyncio
import json
from tracker_api import TrackerGGAPI

async def test_403_fix():
    """Testuoja HTTP 403 klaidos sprendimą"""
    print("🧪 Testuojame HTTP 403 klaidos sprendimą...")
    
    api = TrackerGGAPI()
    
    # Testuojame su tikru žaidėju (m1nd3#2311)
    test_cases = [
        {"username": "m1nd3#2311", "platform": "battlenet"},
        {"username": "TestPlayer#1234", "platform": "battlenet"},
        {"username": "AnotherPlayer", "platform": "psn"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Testas {i}/3: {test_case['username']} ({test_case['platform']})")
        
        try:
            # Gauname statistiką
            stats = await api.get_player_stats(test_case['username'], test_case['platform'])
            if stats:
                print("✅ Statistikos gavimas sėkmingas!")
                print(f"   Vardas: {stats.get('username', 'N/A')}")
                print(f"   Žudymai: {stats.get('kills', 0):,}")
                print(f"   K/D: {stats.get('kd_ratio', 0):.2f}")
                print(f"   Perėmimai: {stats.get('wins', 0):,}")
            else:
                print("❌ Statistikos gavimas nepavyko")
                
        except Exception as e:
            print(f"❌ Klaida: {str(e)}")
        
        # Palaukiame tarp testų
        if i < len(test_cases):
            print("   Palaukiame 10 sekundžių tarp testų...")
            await asyncio.sleep(10)

async def test_rate_limiting():
    """Testuoja rate limiting su 403 klaida"""
    print("\n⏱️ Testuojame rate limiting su 403 klaida...")
    
    api = TrackerGGAPI()
    
    # Bandome daug užklausų iš eilės
    test_username = "m1nd3#2311"
    
    for i in range(3):
        print(f"   Užklausa {i+1}/3...")
        stats = await api.get_player_stats(test_username, "battlenet")
        if stats:
            print(f"   ✅ Užklausa {i+1} sėkminga")
        else:
            print(f"   ❌ Užklausa {i+1} nepavyko")
        
        # Trumpa pauzė tarp užklausų
        if i < 2:
            print("   Palaukiame 5 sekundes...")
            await asyncio.sleep(5)

async def main():
    """Pagrindinė testavimo funkcija"""
    print("🚀 Pradedame HTTP 403 klaidos sprendimo testavimą...")
    
    try:
        # Testuojame pagrindinį sprendimą
        await test_403_fix()
        
        # Testuojame rate limiting
        await test_rate_limiting()
        
        print("\n✅ Visi testai baigti!")
        
    except Exception as e:
        print(f"\n❌ Testavimo klaida: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 