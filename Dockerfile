FROM python:3.11-slim

WORKDIR /app

# Kopijuojame requirements.txt pirmiausia (geresnis Docker caching)
COPY requirements.txt .

# Įdiegiame Python paketus
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Kopijuojame visą aplikacijos kodą
COPY . .

# Nustatome Python kelią
ENV PYTHONPATH=/app

# Paleidžiame botą
CMD ["python3", "bot.py"] 