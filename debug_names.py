#!/usr/bin/env python3
"""
Vardų patikrinimo ir debug skriptas
"""

import asyncio
import aiohttp
import json
from urllib.parse import quote

async def test_username_variations():
    """Testuoja skirtingus vardų variantus"""
    print("🔍 Testuojame vardų variantus...")
    
    # Testuojame skirtingus vardų variantus
    test_cases = [
        "Deivid299#2888",
        "deivid299#2888",  # mažosios raidės
        "DEIVID299#2888",  # didžiosios raidės
        "Deivid299",       # be #
        "deivid299",       # be #, mažosios
        "m1nd3#2311",
        "m1nd3",           # be #
        "M1ND3#2311",      # didžiosios
    ]
    
    for username in test_cases:
        print(f"\n📋 Testuojame: {username}")
        
        # Testuojame Tracker.gg formatą
        if '#' in username:
            formatted = username.replace('#', '%23')
            url = f"https://api.tracker.gg/api/v2/warzone/standard/profile/battlenet/{formatted}"
        else:
            url = f"https://api.tracker.gg/api/v2/warzone/standard/profile/battlenet/{username}"
        
        print(f"   Tracker.gg URL: {url}")
        
        # Testuojame alternatyvaus API formatą
        clean_name = username.split('#')[0]
        alt_url = f"https://call-of-duty-modern-warfare.p.rapidapi.com/warzone/{clean_name}/battle"
        print(f"   Alt API URL: {alt_url}")

async def test_tracker_gg_direct():
    """Testuoja tiesioginį Tracker.gg API"""
    print("\n🔗 Testuojame Tracker.gg API tiesiogiai...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    test_usernames = [
        "Deivid299#2888",
        "m1nd3#2311",
        "test#1234"  # testinis vardas
    ]
    
    for username in test_usernames:
        print(f"\n📋 Testuojame: {username}")
        
        formatted = username.replace('#', '%23')
        url = f"https://api.tracker.gg/api/v2/warzone/standard/profile/battlenet/{formatted}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    print(f"   Status: {response.status}")
                    print(f"   Headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Sėkminga! Duomenys: {len(str(data))} simbolių")
                    elif response.status == 403:
                        print(f"   ❌ 403 - Prieiga uždrausta")
                    elif response.status == 400:
                        print(f"   ❌ 400 - Neteisingi duomenys")
                        try:
                            error_data = await response.text()
                            print(f"   Klaidos tekstas: {error_data[:200]}")
                        except:
                            pass
                    else:
                        print(f"   ❌ {response.status} - Kita klaida")
                        
        except Exception as e:
            print(f"   ❌ Klaida: {str(e)}")

async def test_alternative_api_direct():
    """Testuoja tiesioginį alternatyvų API"""
    print("\n🔄 Testuojame alternatyvų API tiesiogiai...")
    
    headers = {
        "x-rapidapi-key": "ce477eae5dmsh238966977333d6dp1065ffjsn5923ec0a9ab0",
        "x-rapidapi-host": "call-of-duty-modern-warfare.p.rapidapi.com"
    }
    
    test_usernames = [
        "Deivid299",
        "m1nd3",
        "test"
    ]
    
    for username in test_usernames:
        print(f"\n📋 Testuojame: {username}")
        
        url = f"https://call-of-duty-modern-warfare.p.rapidapi.com/warzone/{username}/battle"
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.get(url, headers=headers) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Sėkminga! Duomenys: {len(str(data))} simbolių")
                    elif response.status == 502:
                        print(f"   ❌ 502 - Serverio klaida")
                    elif response.status == 404:
                        print(f"   ❌ 404 - Žaidėjas nerastas")
                    else:
                        print(f"   ❌ {response.status} - Kita klaida")
                        
        except Exception as e:
            print(f"   ❌ Klaida: {str(e)}")

async def main():
    """Pagrindinė funkcija"""
    print("🚀 Pradedame vardų debug...")
    
    await test_username_variations()
    await test_tracker_gg_direct()
    await test_alternative_api_direct()
    
    print("\n✅ Debug baigtas!")

if __name__ == "__main__":
    asyncio.run(main()) 