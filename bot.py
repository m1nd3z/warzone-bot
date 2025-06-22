import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import json
import asyncio
from tracker_api import TrackerGGAPI
from stats_fetcher import StatsFetcher
from datetime import datetime, time
import pytz

print("BOT STARTED")
# Įkeliame aplinkos kintamuosius
load_dotenv()
print("CHANNEL_ID:", os.getenv('CHANNEL_ID'))
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Vilnius')  # Nustatome Vilniaus laiko juostą

# Patikriname ar yra būtini kintamieji
if not TOKEN:
    print("ERROR: DISCORD_TOKEN nerastas aplinkos kintamuosiuose!")
    exit(1)

if not CHANNEL_ID:
    print("WARNING: CHANNEL_ID nerastas. Kai kurios funkcijos gali neveikti.")
    CHANNEL_ID = None
else:
    try:
        CHANNEL_ID = int(CHANNEL_ID)
    except ValueError:
        print("ERROR: CHANNEL_ID turi būti skaičius!")
        CHANNEL_ID = None

# Bot'o konfigūracija
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Inicializuojame Tracker.gg API ir statistikos gavimo klasę
tracker_api = TrackerGGAPI()
stats_fetcher = StatsFetcher()

# Žaidėjų statistikos stebėjimo būsena
monitoring = False
check_interval = 300  # 5 minutės pagal nutylėjimą

# Sleep režimo nustatymai
SLEEP_START = time(23, 0)  # 23:00
SLEEP_END = time(8, 0)     # 08:00

@bot.event
async def on_ready():
    """Bot'o paleidimo įvykis"""
    print(f"{bot.user} prisijungė prie Discord!")
    
    # Pradedame periodinį statistikos tikrinimą tik jei yra CHANNEL_ID
    if CHANNEL_ID:
        monitor_stats.start()
        print(f"Stebėjimas pradėtas kanale {CHANNEL_ID}")
    else:
        print("Stebėjimas nepradėtas - nėra CHANNEL_ID")

@bot.command(name='add')
async def add_player(ctx, username: str, platform: str = "battlenet"):
    """Prideda žaidėją į stebėjimo sąrašą"""
    if stats_fetcher.add_player(username, platform):
        await ctx.send(f"✅ Žaidėjas **{username}** pridėtas į stebėjimo sąrašą! ({platform})")
    else:
        await ctx.send(f"❌ Žaidėjas **{username}** jau yra sąraše!")

@bot.command(name='remove')
async def remove_player(ctx, username: str, platform: str = "battlenet"):
    """Pašalina žaidėją iš stebėjimo sąrašo"""
    if stats_fetcher.remove_player(username, platform):
        await ctx.send(f"✅ Žaidėjas **{username}** pašalintas iš sąrašo!")
    else:
        await ctx.send(f"❌ Žaidėjas **{username}** nerastas sąraše!")

@bot.command(name='list')
async def list_players(ctx):
    """Rodo visus žaidėjus stebėjimo sąraše"""
    player_list = stats_fetcher.get_player_list()
    await ctx.send(player_list)

@bot.command(name='prisijungiu')
async def auto_add_player(ctx, username: str, platform: str = "battlenet"):
    """Žaidėjas pats save prideda į stebėjimo sąrašą"""
    if stats_fetcher.add_player(username, platform):
        await ctx.send(f"✅ Sėkmingai prisijungėte! **{username}** pridėtas į stebėjimo sąrašą! ({platform})")
    else:
        await ctx.send(f"❌ Jūs jau esate sąraše! Naudokite `!remove {username} {platform}` jei norite pašalinti save.")

@bot.command(name='statistika')
async def show_player_stats(ctx, username: str = None, platform: str = "battlenet"):
    """Rodo žaidėjo statistiką"""
    print("STATISTIKA KOMANDA GAUTA")
    
    if username is None:
        # Jei nenurodytas vardas, naudojame komandos autoriaus vardą
        username = str(ctx.author)
        # Bandome rasti žaidėją sąraše
        found = False
        for player in stats_fetcher.players:
            if player['username'] == username:
                platform = player['platform']
                found = True
                break
        
        if not found:
            await ctx.send(f"❌ Jūsų vardas **{username}** nerastas sąraše. Naudokite `!prisijungiu username platform` arba nurodykite kitą žaidėjo vardą.")
            return
    
    # Gauname statistiką iš Tracker.gg
    await ctx.send(f"🔄 Gauname **{username}** statistiką...")
    stats = await stats_fetcher.get_player_stats(username, platform)
    
    if stats:
        message = stats_fetcher.format_stats_message(stats)
        await ctx.send(message)
    else:
        await ctx.send(f"❌ Nepavyko gauti **{username}** statistikos. Patikrinkite vardą ir platformą.")

@bot.command(name='komanda')
async def show_team_stats(ctx):
    """Rodo komandos statistiką"""
    await ctx.send("🔄 Gauname komandos statistiką...")
    
    all_stats = await stats_fetcher.get_all_players_stats()
    if all_stats:
        message = stats_fetcher.format_summary_message(all_stats)
        await ctx.send(message)
    else:
        await ctx.send("❌ Nepavyko gauti komandos statistikos.")

@bot.command(name='test')
async def test_api(ctx, username: str = None, platform: str = "battlenet"):
    """Testuoja visus tris API su konkrečiu žaidėju (praleidžia Activision API dėl Node.js problemų)"""
    if not username:
        await ctx.send("❌ Nurodykite žaidėjo vardą: `!test username platform`")
        return
        
    await ctx.send(f"🧪 Testuojame visus tris API su **{username}** ({platform})...")
    
    try:
        # Testuojame Tracker.gg API
        await ctx.send("🔄 Bandome Tracker.gg API...")
        tracker_stats = await tracker_api.get_player_stats(username, platform)
        
        if tracker_stats:
            await ctx.send("✅ Tracker.gg API veikia!")
        else:
            await ctx.send("❌ Tracker.gg API nepavyko")
        
        # Palaukiame tarp testų
        await asyncio.sleep(2)
        
        # Testuojame alternatyvų API
        await ctx.send("🔄 Bandome alternatyvų API...")
        from alternative_api import AlternativeAPI
        alt_api = AlternativeAPI()
        alt_stats = await alt_api.get_player_stats(username, platform)
        
        if alt_stats:
            await ctx.send("✅ Alternatyvus API veikia!")
        else:
            await ctx.send("❌ Alternatyvus API nepavyko")
        
        # Palaukiame tarp testų
        await asyncio.sleep(2)
        
        # Testuojame trečią API
        await ctx.send("🔄 Bandome trečią API...")
        from third_api import ThirdAPI
        third_api = ThirdAPI()
        third_stats = await third_api.get_player_stats(username, platform)
        
        if third_stats:
            await ctx.send("✅ Trečias API veikia!")
        else:
            await ctx.send("❌ Trečias API nepavyko")
        
        # Rodyti rezultatus
        working_apis = []
        if tracker_stats:
            working_apis.append("🔗 Tracker.gg API")
        if alt_stats:
            working_apis.append("🔄 Alternatyvus API")
        if third_stats:
            working_apis.append("⚡ Trečias API")
        
        if working_apis:
            await ctx.send("📊 **Testavimo rezultatai:**")
            for api in working_apis:
                await ctx.send(f"{api}: ✅ Veikia")
            
            if not tracker_stats:
                await ctx.send("🔗 Tracker.gg API: ❌ Nepavyksta")
            if not alt_stats:
                await ctx.send("🔄 Alternatyvus API: ❌ Nepavyksta")
            if not third_stats:
                await ctx.send("⚡ Trečias API: ❌ Nepavyksta")
        else:
            await ctx.send("❌ Visi trys API nepavyko. Patikrinkite vardą ir platformą.")
            
    except Exception as e:
        await ctx.send(f"❌ Testavimo klaida: {str(e)}")

@bot.command(name='testall')
async def test_all_apis(ctx, username: str = None, platform: str = "battlenet"):
    """Testuoja visus tris API ir rodo statistiką (praleidžia Activision API dėl Node.js problemų)"""
    if not username:
        await ctx.send("❌ Nurodykite žaidėjo vardą: `!testall username platform`")
        return
        
    await ctx.send(f"🧪 Testuojame visus tris API su **{username}** ({platform})...")
    
    try:
        # Testuojame su StatsFetcher (kuris naudoja visus tris API)
        stats = await stats_fetcher.get_player_stats(username, platform)
        
        if stats:
            source = stats.get('source', 'unknown')
            source_texts = {
                'tracker_gg': "Tracker.gg",
                'alternative_api': "Alternatyvus API",
                'third_api': "Trečias API"
            }
            source_text = source_texts.get(source, "Nežinomas šaltinis")
            await ctx.send(f"✅ Statistikos gavimas sėkmingas! Šaltinis: {source_text}")
            
            message = stats_fetcher.format_stats_message(stats)
            await ctx.send(message)
        else:
            await ctx.send("❌ Nepavyko gauti statistikos iš visų trijų API. Patikrinkite vardą ir platformą.")
            
    except Exception as e:
        await ctx.send(f"❌ Testavimo klaida: {str(e)}")

@bot.command(name='testrapid')
async def test_rapidapi(ctx, username: str = None, platform: str = "battlenet"):
    """Testuoja RapidAPI COD API su konkrečiu žaidėju"""
    if not username:
        await ctx.send("❌ Nurodykite žaidėjo vardą: `!testrapid username platform`")
        return
        
    await ctx.send(f"🚀 Testuojame RapidAPI COD API su **{username}** ({platform})...")
    
    try:
        from rapidapi_cod import RapidAPICOD
        api = RapidAPICOD()
        
        # Testuojame statistiką
        await ctx.send("🔄 Gauname statistiką...")
        stats = await api.get_player_stats(username, platform)
        
        if stats:
            await ctx.send("✅ RapidAPI COD API veikia!")
            
            # Rodyti statistikos santrauką
            message = f"📊 **{username}** statistikos santrauka:\n"
            message += f"🎯 Žudymai: {stats.get('kills', 0):,}\n"
            message += f"💀 Mirtys: {stats.get('deaths', 0):,}\n"
            message += f"⚖️ K/D: {stats.get('kd_ratio', 0):.2f}\n"
            message += f"🏆 Perėmimai: {stats.get('wins', 0):,}\n"
            message += f"🎮 Žaidimai: {stats.get('games_played', 0):,}\n"
            message += f"📈 SPM: {stats.get('score_per_minute', 0):.0f}"
            
            await ctx.send(message)
        else:
            await ctx.send("❌ RapidAPI COD API nepavyko gauti statistikos")
        
        # Testuojame žaidėjo informaciją
        await ctx.send("🔄 Gauname žaidėjo informaciją...")
        info = await api.get_player_info(username, platform)
        
        if info:
            info_message = f"👤 **{username}** informacija:\n"
            info_message += f"🌟 Lygis: {info.get('level', 'N/A')}\n"
            info_message += f"⭐ Rangas: {info.get('rank', 'N/A')}\n"
            info_message += f"🏅 Prestižas: {info.get('prestige', 'N/A')}"
            
            await ctx.send(info_message)
        else:
            await ctx.send("❌ Nepavyko gauti žaidėjo informacijos")
            
    except Exception as e:
        await ctx.send(f"❌ Klaida testuojant RapidAPI: {str(e)}")

def is_sleep_time():
    """Patikrina ar dabar yra miego režimo laikas"""
    try:
        tz = pytz.timezone(TIMEZONE)
        current_time = datetime.now(tz).time()
        return SLEEP_START <= current_time or current_time <= SLEEP_END
    except Exception as e:
        print(f"Klaida tikrinant laiką: {e}")
        return False

@tasks.loop(seconds=300)
async def monitor_stats():
    """Periodiškai tikrina žaidėjų statistiką"""
    global monitoring
    
    if not monitoring or not CHANNEL_ID:
        return
    
    if is_sleep_time():
        print("Miego režimas - praleidžiame statistikos tikrinimą")
        return
    
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print(f"Kanalas {CHANNEL_ID} nerastas")
            return
        
        print("Tikriname žaidėjų statistiką...")
        all_stats = await stats_fetcher.get_all_players_stats()
        
        if all_stats:
            message = stats_fetcher.format_summary_message(all_stats)
            await channel.send(message)
        else:
            await channel.send("❌ Nepavyko gauti komandos statistikos.")
            
    except Exception as e:
        print(f"Klaida tikrinant statistiką: {e}")

@bot.command(name='start')
async def start_monitoring(ctx):
    """Pradeda statistikos stebėjimą"""
    global monitoring
    monitoring = True
    await ctx.send("✅ Statistikos stebėjimas pradėtas!")

@bot.command(name='stop')
async def stop_monitoring(ctx):
    """Sustabdo statistikos stebėjimą"""
    global monitoring
    monitoring = False
    await ctx.send("⏹️ Statistikos stebėjimas sustabdytas!")

@bot.command(name='interval')
async def set_interval(ctx, seconds: int):
    """Nustato tikrinimo intervalą sekundėmis"""
    global check_interval
    if seconds < 60:
        await ctx.send("❌ Intervalas turi būti bent 60 sekundžių!")
        return
    
    check_interval = seconds
    monitor_stats.change_interval(seconds=seconds)
    await ctx.send(f"⏱️ Tikrinimo intervalas nustatytas į {seconds} sekundžių!")

# Paleidžiame botą
bot.run(TOKEN) 