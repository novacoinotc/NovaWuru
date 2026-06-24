#!/bin/bash
# Instala el scheduler diario (launchd): escaneo 09:00, liquidación 23:30.
set -e
DIR="/Users/issacvm/Documents/Futbol Wuru/scheduler"
LA="$HOME/Library/LaunchAgents"
chmod +x "$DIR/run_scan.sh" "$DIR/run_settle.sh"
cp "$DIR/com.wuru.scan.plist" "$LA/"
cp "$DIR/com.wuru.settle.plist" "$LA/"
launchctl unload "$LA/com.wuru.scan.plist" 2>/dev/null || true
launchctl unload "$LA/com.wuru.settle.plist" 2>/dev/null || true
launchctl load "$LA/com.wuru.scan.plist"
launchctl load "$LA/com.wuru.settle.plist"
echo "✅ Scheduler instalado:"
echo "   • Escaneo + apuestas: todos los días 09:00"
echo "   • Liquidación de resultados: todos los días 23:30"
echo "Logs: $DIR/scan.log y $DIR/settle.log"
echo "Para desinstalar: launchctl unload ~/Library/LaunchAgents/com.wuru.{scan,settle}.plist"
