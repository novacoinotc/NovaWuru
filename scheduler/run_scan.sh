#!/bin/bash
# Corrida diaria: escanea todas las ligas, top 15, modelo completo, coloca apuestas en Neon.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
cd "/Users/issacvm/Documents/Futbol Wuru" || exit 1
set -a; . ./wuru-bets/.env 2>/dev/null; set +a
echo "===== SCAN $(date) =====" >> scheduler/scan.log
python3 scanner.py 15 36 >> scheduler/scan.log 2>&1
echo "" >> scheduler/scan.log
