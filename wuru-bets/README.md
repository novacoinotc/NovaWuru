# ⚽ Wuru Bets — Paper Trading del modelo Wuru

Dashboard de value betting con paper trading (100,000 MXN virtuales), staking ¼ Kelly,
CLV y posiciones en muchos partidos a la vez. Next.js + Neon Postgres.

## Arquitectura
- **Modelo Wuru (Python, este repo padre):** simula partidos → `predictions.json`.
- **GLM 5.2 (API barata):** investigación pesada de jugadores. **Claude:** estrategia.
- **Esta app (Next.js):** value finder + paper trading + dashboard.
- **DB:** Postgres local (Docker) en dev, **Neon** en producción.

## Correr en local (Docker + dev)
```bash
cp .env.example .env          # ajusta llaves (GLM/Claude opcionales para el dashboard)
docker compose up -d          # Postgres local
npm install
npm run db:init               # crea tablas + bankroll 100k
# genera predicciones desde el modelo (en el repo padre):
cd .. && python3 export_predictions.py && cd wuru-bets
npm run seed                  # coloca apuestas de valor (paper)
npm run dev                   # http://localhost:3000
```

## Liquidar resultados
Crea `../results.json` `{ "ENG_GHA": {"hg":0,"ag":1} }` y corre `npm run settle`.

## Despliegue (Vercel + Neon)
1. Crea base Neon (Vercel Marketplace) → copia `DATABASE_URL`.
2. `vercel` → configura env vars (`DATABASE_URL`, `GLM_API_KEY`, `ANTHROPIC_API_KEY`, `BANKROLL_MXN`, `KELLY_FRACTION`, `EV_THRESHOLD`, `CRON_SECRET`).
3. Corre `npm run db:init` apuntando a Neon. El cron diario (`vercel.json`) pega a `/api/cron`.

## Flujo diario (timing de apuestas)
Cada mañana: el modelo genera predicciones → POST a `/api/cron` con `{predictions, reset:false}`
→ coloca apuestas de valor (EV ≥ umbral) ~1 día antes (mejores momios) → al cierre se liquidan y se mide **CLV**.

**Reglas:** stake por valor (¼ Kelly), **nunca Martingale**. Paper trading = dinero virtual. Juego responsable.
