#!/usr/bin/env python3
"""
Deployment testavimo skriptas
"""

import asyncio
import sys
import os

def test_imports():
    """Testuoja ar visi import'ai veikia"""
    print("🧪 Testuojame import'us...")
    
    try:
        import discord
        print("✅ discord.py - OK")
    except ImportError as e:
        print(f"❌ discord.py - {e}")
        return False
    
    try:
        import aiohttp
        print("✅ aiohttp - OK")
    except ImportError as e:
        print(f"❌ aiohttp - {e}")
        return False
    
    try:
        import pytz
        print("✅ pytz - OK")
    except ImportError as e:
        print(f"❌ pytz - {e}")
        return False
    
    try:
        from reliable_api import ReliableAPI
        print("✅ reliable_api - OK")
    except ImportError as e:
        print(f"❌ reliable_api - {e}")
        return False
    
    try:
        from stats_fetcher import StatsFetcher
        print("✅ stats_fetcher - OK")
    except ImportError as e:
        print(f"❌ stats_fetcher - {e}")
        return False
    
    return True

async def test_api():
    """Testuoja API funkcionalumą"""
    print("\n🧪 Testuojame API...")
    
    try:
        from reliable_api import ReliableAPI
        api = ReliableAPI()
        
        # Testuojame su žinomu žaidėju
        stats = await api.get_player_stats("m1nd3#2311", "battlenet")
        
        if stats:
            print("✅ API veikia!")
            print(f"   Vardas: {stats.get('username', 'N/A')}")
            print(f"   Žudymai: {stats.get('kills', 0):,}")
            print(f"   K/D: {stats.get('kd_ratio', 0):.2f}")
            if stats.get('is_fallback'):
                print("   ⚠️ Naudojami fallback duomenys")
            return True
        else:
            print("❌ API nepavyko")
            return False
            
    except Exception as e:
        print(f"❌ API klaida: {e}")
        return False

def test_environment():
    """Testuoja aplinkos kintamuosius"""
    print("\n🧪 Testuojame aplinkos kintamuosius...")
    
    required_vars = ['DISCORD_TOKEN', 'CHANNEL_ID']
    missing_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} - OK")
        else:
            print(f"❌ {var} - trūksta")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Trūksta kintamųjų: {', '.join(missing_vars)}")
        print("Railway aplinkoje šie kintamieji turėtų būti nustatyti.")
        return False
    
    return True

async def main():
    """Pagrindinė testavimo funkcija"""
    print("🚀 Pradedame deployment testavimą...\n")
    
    # Testuojame import'us
    if not test_imports():
        print("\n❌ Import'ai nepavyko - reikia įdiegti paketus")
        return False
    
    # Testuojame aplinkos kintamuosius
    if not test_environment():
        print("\n⚠️ Aplinkos kintamieji nevisi nustatyti")
        print("Bet tai gali būti OK, jei testuojate lokaliai")
    
    # Testuojame API
    if not await test_api():
        print("\n❌ API testas nepavyko")
        return False
    
    print("\n✅ Visi testai sėkmingi!")
    print("🎉 Deployment turėtų veikti Railway!")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 