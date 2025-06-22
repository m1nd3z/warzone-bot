# 🚀 Warzone Bot Paleidimo Instrukcija

## 1. Aplinkos kintamieji

Sukurkite `.env` failą su šiais kintamaisiais:

```env
DISCORD_TOKEN=your_discord_bot_token_here
CHANNEL_ID=your_channel_id_here
TIMEZONE=Europe/Vilnius
```

## 2. Discord Bot Sukūrimas

1. Eikite į [Discord Developer Portal](https://discord.com/developers/applications)
2. Sukurkite naują aplikaciją
3. Eikite į "Bot" skiltį
4. Sukurkite botą ir nukopijuokite token
5. Įjunkite "Message Content Intent"

## 3. Lokalus Paleidimas

```bash
# Įdiegti priklausomybes
pip install -r requirements.txt

# Testuoti API
python quick_test.py

# Paleisti botą
python bot.py
```

## 4. Railway.app Deploy

1. Sukurkite Railway.app paskyrą
2. Prijunkite GitHub repozitoriją
3. Nustatykite aplinkos kintamuosius
4. Deploy!

## 5. Komandos

```bash
# Pridėti save
!prisijungiu PlayerName#1234 battlenet

# Rodyti statistiką
!statistika PlayerName#1234 battlenet

# Testuoti API
!test PlayerName#1234 battlenet

# Pradėti stebėjimą
!start

# Rodyti pagalbą
!help
```

## 6. Palaikomos Platformos

- **battlenet** - Battle.net (pvz. username#1234)
- **psn** - PlayStation Network  
- **xbl** - Xbox Live 