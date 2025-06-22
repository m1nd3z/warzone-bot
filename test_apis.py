#!/usr/bin/env python3
"""
API testavimo skriptas - patikrina kurie API veikia
"""

import asyncio
import aiohttp
from typing import Dict, Optional

async def test_api_endpoint(url: str, headers: Dict = None, name: str = "API") -> bool:
    """Testuoja API endpoint"""
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        connector = aiohttp.TCPConnector(ssl=False)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    print(f"✅ {name}: Veikia (HTTP {response.status})")
                    return True
                else:
                    print(f"❌ {name}: HTTP {response.status} klaida")
                    return False
    except Exception as e:
        print(f"❌ {name}: Tinklo klaida - {str(e)}")
        return False

async def test_all_apis():
    """Testuoja visus API"""
    print("🧪 Testuojame visus API...\n")
    
    # Testuojame COD Stats API (RapidAPI)
    cod_stats_url = "https://call-of-duty-modern-warfare.p.rapidapi.com/warzone/m1nd3/battle"
    cod_stats_headers = {
        "x-rapidapi-key": "ce477eae5dmsh238966977333d6dp1065ffjsn5923ec0a9ab0",
        "x-rapidapi-host": "call-of-duty-modern-warfare.p.rapidapi.com"
    }
    
    # Testuojame COD API Hub
    cod_hub_url = "https://cod-api.uno/stats/cod/v1/mw/warzone/m1nd3/battle"
    cod_hub_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    # Testuojame Tracker.gg API
    tracker_url = "https://api.tracker.gg/api/v2/warzone/standard/profile/battlenet/m1nd3%232311"
    tracker_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://tracker.gg/"
    }
    
    # Testuojame COD Tracker API
    cod_tracker_url = "https://cod.tracker.gg/api/v1/cod/mw/profile/battlenet/m1nd3"
    cod_tracker_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    results = []
    
    print("1. Testuojame COD Stats API (RapidAPI)...")
    results.append(await test_api_endpoint(cod_stats_url, cod_stats_headers, "COD Stats API"))
    
    print("\n2. Testuojame COD API Hub...")
    results.append(await test_api_endpoint(cod_hub_url, cod_hub_headers, "COD API Hub"))
    
    print("\n3. Testuojame Tracker.gg API...")
    results.append(await test_api_endpoint(tracker_url, tracker_headers, "Tracker.gg API"))
    
    print("\n4. Testuojame COD Tracker API...")
    results.append(await test_api_endpoint(cod_tracker_url, cod_tracker_headers, "COD Tracker API"))
    
    # Suvestinė
    working_apis = sum(results)
    total_apis = len(results)
    
    print(f"\n📊 SUVESTINĖ:")
    print(f"Veikiantys API: {working_apis}/{total_apis}")
    
    if working_apis == 0:
        print("❌ Nėra veikiančių API!")
        print("\n💡 Rekomendacijos:")
        print("• Patikrinkite interneto ryšį")
        print("• Galbūt API yra laikinai nepasiekiami")
        print("• Reikia ieškoti alternatyvių API")
    elif working_apis == 1:
        print("⚠️ Tik vienas API veikia - reikia atsargiai naudoti")
    else:
        print("✅ Keli API veikia - geras fallback")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_all_apis()) 