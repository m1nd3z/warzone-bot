#!/usr/bin/env python3
"""
Paprastas testas, ar Python veikia
"""

import sys
import os

print("Python versija:", sys.version)
print("Darbinis katalogas:", os.getcwd())
print("Aplinkos kintamieji:")
for key, value in os.environ.items():
    if key in ['DISCORD_TOKEN', 'CHANNEL_ID', 'ACT_SSO_COOKIE']:
        print(f"  {key}: {'*' * len(value) if value else 'None'}")

try:
    import discord
    print("✅ discord.py importuojamas sėkmingai")
except ImportError as e:
    print(f"❌ discord.py importavimo klaida: {e}")

try:
    import aiohttp
    print("✅ aiohttp importuojamas sėkmingai")
except ImportError as e:
    print(f"❌ aiohttp importavimo klaida: {e}")

print("Testas baigtas!") 