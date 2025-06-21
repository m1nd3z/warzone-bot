#!/usr/bin/env python3
"""
Greitas tracker.gg API testas
"""

import asyncio
from tracker_api import TrackerGGAPI

async def quick_test():
    print("🧪 Greitas tracker.gg API testas...")
    
    api = TrackerGGAPI()
    
    # Testuojame su žinomu žaidėju
    test_username = "test#1234"
    test_platform = "battlenet"
    
    print(f"📋 Testuojame: {test_username} ({test_platform})")
    
    try:
        stats = await api.get_player_stats(test_username, test_platform)
        if stats:
            print("✅ API veikia!")
            print(f"   Vardas: {stats.get('username', 'N/A')}")
            print(f"   Žudymai: {stats.get('kills', 0):,}")
            print(f"   K/D: {stats.get('kd_ratio', 0):.2f}")
        else:
            print("❌ Žaidėjas nerastas (tai normaliai - testuojame su netikru vardu)")
            
    except Exception as e:
        print(f"❌ Klaida: {str(e)}")
    
    print("✅ Testas baigtas!")

if __name__ == "__main__":
    asyncio.run(quick_test()) 