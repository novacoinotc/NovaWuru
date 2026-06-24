#!/bin/bash
# Liquidación diaria: jala resultados reales y liquida en Neon.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
cd "/Users/issacvm/Documents/Futbol Wuru" || exit 1
set -a; . ./wuru-bets/.env 2>/dev/null; set +a
echo "===== SETTLE $(date) =====" >> scheduler/settle.log
python3 settle_auto.py 3 >> scheduler/settle.log 2>&1
echo "" >> scheduler/settle.log
