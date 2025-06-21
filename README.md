# 🎮 Warzone Statistikos Bot (Multi-API)

Discord botas Call of Duty Warzone žaidėjų statistikos stebėjimui naudojant kelis API:
- **Oficialus Activision API** (pagrindinis)
- **Tracker.gg API** (atsarginė kopija)
- **COD Stats API** (atsarginė kopija)
- **COD API Hub** (atsarginė kopija)

## ✨ Funkcijos

- **Žaidėjų stebėjimas**: Automatinis žaidėjų statistikos gavimas
- **Multi-platforma**: Palaiko Battle.net, PlayStation Network ir Xbox Live
- **Realaus laiko atnaujinimai**: Periodinis statistikos tikrinimas
- **Miego režimas**: Automatinis stebėjimo sustabdymas naktį (23:00-08:00)
- **Lietuviška sąsaja**: Visi pranešimai lietuvių kalba
- **Rate limiting**: Automatinis užklausų limitavimas
- **Multi-API Fallback**: Automatinis perjungimas tarp 4 skirtingų API
- **Patobulinta klaidų tvarkymas**: Retry logika ir HTTP 403 klaidų sprendimas

## 🚀 Diegimas

### 1. Reikalavimai
- Python 3.8+
- Node.js 16+
- Discord bot token
- Activision SSO token
- Railway.app arba Heroku paskyra

### 2. Lokalus diegimas

```bash
# Klonuoti repozitoriją
git clone <repository-url>
cd warzone

# Įdiegti Python priklausomybes
pip install -r requirements.txt

# Įdiegti Node.js priklausomybes
npm install

# Sukurti .env failą
cp .env.example .env
```

### 3. Aplinkos kintamieji

Sukurkite `.env` failą su šiais kintamaisiais:

```env
DISCORD_TOKEN=your_discord_bot_token
CHANNEL_ID=your_channel_id
TIMEZONE=Europe/Vilnius
COD_SSO=your_activision_sso_token
```

### 4. Discord bot sukūrimas

1. Eikite į [Discord Developer Portal](https://discord.com/developers/applications)
2. Sukurkite naują aplikaciją
3. Eikite į "Bot" skiltį ir sukurkite botą
4. Įjunkite "Message Content Intent"
5. Nukopijuokite bot token

### 5. Activision SSO Token gavimas

1. **Eikite į Call of Duty.com:**
   - Atsisiųskite ir įdiegite Call of Duty HQ
   - Prisijunkite prie savo Activision paskyros

2. **Gaukite SSO token:**
   - Atidarykite Developer Tools (F12)
   - Eikite į Network tab
   - Atnaujinkite puslapį
   - Ieškokite užklausų su "sso" arba "token"
   - Nukopijuokite SSO token

3. **Nustatykite aplinkos kintamąjį:**
   ```bash
   export COD_SSO='your_sso_token_here'
   ```

## 📋 Komandos

### Pagrindinės komandos
- `!prisijungiu username platform` - Pridėti save į sąrašą
- `!add username platform` - Pridėti žaidėją (admin)
- `!remove username platform` - Pašalinti žaidėją
- `!list` - Rodyti žaidėjų sąrašą
- `!statistika [username] [platform]` - Rodyti žaidėjo statistiką
- `!komanda` - Rodyti komandos statistiką

### Stebėjimo komandos
- `!start` - Pradėti automatinį stebėjimą
- `!stop` - Sustabdyti stebėjimą
- `!interval sekundės` - Nustatyti tikrinimo intervalą

### Testavimo komandos
- `!test username platform` - Testuoti abu API atskirai
- `!testboth username platform` - Testuoti abu API ir rodyti statistiką
- `!help` - Rodyti pagalbą (Discord.py built-in)

## 🔧 API Sprendimai

### Pagrindinis API: Oficialus Activision API
- **Biblioteka**: `call-of-duty-api` (Node.js)
- **Funkcijos**: Pilna oficiali statistikos informacija
- **Rate limiting**: 20 užklausų per minutę
- **Retry logika**: 3 bandymai su progresyviu laukimu
- **Reikalavimai**: Activision SSO token

### Atsarginė kopija 1: Tracker.gg API
- **URL**: `https://api.tracker.gg/api/v2/warzone/standard/profile`
- **Funkcijos**: Pilna statistikos informacija
- **Rate limiting**: 5 užklausos per minutę
- **Retry logika**: 3 bandymai su progresyviu laukimu

### Atsarginė kopija 2: COD Stats API
- **URL**: `https://call-of-duty-modern-warfare.p.rapidapi.com`
- **Funkcijos**: Pagrindinė statistikos informacija
- **Rate limiting**: 10 užklausų per minutę
- **Retry logika**: 3 bandymai su progresyviu laukimu

### Atsarginė kopija 3: COD API Hub
- **URL**: `https://api.callofduty.com/api/v1`
- **Funkcijos**: Pagrindinė statistikos informacija
- **Rate limiting**: 15 užklausų per minutę
- **Retry logika**: 3 bandymai su progresyviu laukimu

### Automatinis Fallback
Botas automatiškai perjungia tarp API šia tvarka:
1. **Oficialus Activision API** (pagrindinis)
2. **Tracker.gg API** (atsarginė kopija 1)
3. **COD Stats API** (atsarginė kopija 2)
4. **COD API Hub** (atsarginė kopija 3)

Jei bet kuris API grąžina klaidą (HTTP 403, 404, 429), botas automatiškai bando kitą.

## 🛠️ Klaidų Sprendimas

### HTTP 403 "Forbidden" Klaida
- **Priežastis**: Serveris blokuoja užklausas
- **Sprendimas**: 
  - Patobulinti User-Agent headers
  - Retry logika su progresyviu laukimu
  - Automatinis perjungimas į alternatyvų API

### Rate Limiting
- **Priežastis**: Per daug užklausų per trumpą laiką
- **Sprendimas**: Automatinis užklausų limitavimas ir laukimas

### Tinklo Klaidos
- **Priežastis**: Tinklo problemos
- **Sprendimas**: Retry logika su eksponentiniu backoff

## 📊 Statistikos Formatai

### Tracker.gg API
```
🎮 Username (Battle.net) 🔗 Tracker.gg
📊 Statistika:
• 🎯 Žudymai: 1,234
• 💀 Mirtys: 567
• ⚖️ K/D: 2.18
• 🏆 Perėmimai: 45
• 🥇 Top 10: 123
• 🎮 Žaidimai: 456
• ⏱️ Žaidimo laikas: 12h 34m
• 📈 Taškai/min: 234
• 🎯 Galvos šūviai: 89
• 💚 Atgaivinimai: 23
• 🎯 Ilgiausias šūvis: 234m
```

### Alternatyvus API
```
🎮 Username (Battle.net) 🔄 Alternatyvus API
📊 Statistika:
• 🎯 Žudymai: 1,234
• 💀 Mirtys: 567
• ⚖️ K/D: 2.18
• 🏆 Perėmimai: 45
• 🥇 Top 10: 123
• 🎮 Žaidimai: 456
• 📈 Taškai/min: 234
```

## 🚀 Deployment

### Railway.app
1. Sukurkite paskyrą [Railway.app](https://railway.app)
2. Prijunkite GitHub repozitoriją
3. Nustatykite aplinkos kintamuosius
4. Deploy!

### Render.com
1. Sukurkite paskyrą [Render.com](https://render.com)
2. Prijunkite GitHub repozitoriją
3. Nustatykite aplinkos kintamuosius
4. Deploy!

## 🔍 Testavimas

```bash
# Testuoti HTTP 403 sprendimą
python test_403_fix.py

# Testuoti alternatyvų API
python alternative_api.py

# Testuoti visą sistemą
python test_tracker.py
```

## 📝 Žinomos Problemos

1. **HTTP 403 klaidos**: Sprendžiamos su retry logika ir alternatyviu API
2. **Rate limiting**: Automatiškai tvarkomas
3. **Tinklo klaidos**: Retry logika su backoff

## 🤝 Prisidėjimas

1. Fork repozitoriją
2. Sukurkite feature branch
3. Commit pakeitimus
4. Push į branch
5. Sukurkite Pull Request

## 📄 Licencija

MIT License - žiūrėkite LICENSE failą detalesnėms informacijoms.