# 🧠⚽ AVANCES DEL SISTEMA — Wuru (memoria completa del proyecto)
### Estado al 23-jun-2026 · Documento de preservación de memoria (no omite nada)

> Propósito: capturar TODO lo construido — el modelo predictivo, su calibración/validación, el sistema de apuestas (paper trading) y el estado actual — para poder retomar el proyecto en cualquier momento sin perder contexto. Acompaña a `estrategia de analisis.md` (la metodología detallada, 24 secciones).

---

## 0. Qué es el proyecto
Un **sistema de predicción de fútbol** (Mundial 2026) que:
1. Simula partidos con un **modelo completo** (3 capas: estadístico + agentes-por-jugador + gemelos digitales con física/entorno).
2. **Valida** su acierto contra resultados reales (backtest + calibración).
3. Convierte las predicciones en una **estrategia de apuestas con paper trading** (app Next.js: value betting, ¼ Kelly, CLV, dashboard).

**Hardware:** Apple M4 Pro (14 núcleos), 24 GB RAM, Python 3.14 (numpy/scipy), Node 24, Docker 29.

---

## 1. CRONOLOGÍA — todo lo que hicimos
1. **Caso base México vs Corea (18-jun):** modelo completo profundo (agentes por jugador con vida/familia/emoción + monólogos). Resultado real **México 1-0** → el modelo acertó favorito + portería a cero.
2. **3 modelos** construidos y triangulados (estadístico, agente-por-jugador, gemelos digitales).
3. **Capa física** (altura, velocidad, durabilidad) + **entorno** (clima, altitud, pasto, afición).
4. **Calibración post-partido** (v2): goles más realistas, capa de portero, fatiga por distancia real (no "desplome por altura").
5. **Backtest** sobre 28 partidos del Mundial → 57% acierto 1X2; bien calibrado en extremos, flojo en partidos parejos.
6. **Calibración con datos reales** + **búsqueda masiva de parámetros** (CV + bootstrap): el tuning NO mejora significativamente con muestra chica → calibración modesta.
7. **Ensamble agentes + Elo:** el CV descartó el Elo (los agentes ya lo subsumen) → validó el enfoque.
8. **Backtest histórico** (Mundiales 2018+2022+2026 = 124 partidos): priors transferibles (Mundial goleador, favoritos más separados, ventaja anfitrión ~90 Elo). El modelo de agentes **le gana al motor Elo calibrado** (log-loss 0.856 vs 0.952).
9. **Proyección del torneo completo** (Monte Carlo 50,000 torneos): favoritos Argentina 17%, España 15%, Francia 13%.
10. **Bracket jugado partido por partido** con el modelo completo (75 agentes) → campeón de ESE universo: Canadá. **Bracket visual** en PNG + PDF.
11. **Runbook maestro** (sección 21 del .md) + **comando gatillo "correr el modelo del .md"** + reglas inviolables (sección 22): jamás omitir nada, hasta 200 agentes, 1 agente por jugador con contexto real.
12. **Predicciones diarias** con el modelo completo (1 agente por jugador), día por día:
    - **19-jun (G C/D):** 3/4 ✓ (falló Paraguay-Türkiye upset)
    - **20-jun (G E/F):** 3/4 ✓ (falló Ecuador-Curazao 0-0)
    - **22-jun (G I/J):** 3/4 ✓ (reanudado tras límite de sesión)
    - **23-jun (G K/L):** predicho
    - **24-jun (G A/B/C):** predicho en 2 tandas (incluye México-Chequia en Azteca con altitud)
    - **Acumulado ≈ 9/12 ganadores (~75%).**
13. **Sistema de apuestas `wuru-bets`** (Next.js + Postgres/Neon): value betting + paper trading 100k MXN + dashboard. Probado en local con Docker.

---

## 2. EL MODELO — arquitectura (3 capas)
| Capa | Archivo | Qué captura |
|---|---|---|
| 1. Estadístico frío | `sim_mex_kor.py` | Poisson/Dixon-Coles/Elo/mercado |
| 2. Agente-por-jugador | `sim_agentes.py` + `player_minds.json` | estado mental/emocional + monólogo |
| 3. Gemelos digitales | `sim_gemelos.py` / `sim_gemelos_v2.py` (calibrado) | bio + física + entorno (estocástico) |
| Motor genérico por partido | `sim_match.py` | usa gemelos + Elo base + calibración; 100k Monte Carlo |
| Predictor calibrado | `predict_match.py` | λ → probabilidades calibradas (1X2, O/U, BTTS, marcadores) |

**Calibración:** `calibration.json` (modelo agentes: G=1.05, S=1.2, ρ=−0.12, δ=1.10) · `calibration_elo.json` (motor Elo: TOTAL=2.85, GP400=1.2, HOST=90, ρ=−0.10).

**Datos:** `elo.json` (48 selecciones), `twins.json`, `env.json`, `player_minds.json`.

---

## 3. VALIDACIÓN / BACKTEST
| Archivo | Qué hace |
|---|---|
| `backtest.json` + `backtest_score.py` | 28 partidos 2026: Brier, log-loss, acierto, calibración |
| `calibrate.py` | calibración con LOO-CV (28 partidos) |
| `search_calibration.py` + `search_result.json` | búsqueda masiva 6,720 configs + bootstrap |
| `ensemble_blend.py` + `ensemble_result.json` | ensamble agentes+Elo (CV) |
| `hist_calibrate.py` + `hist2018.json`/`hist2022.json`/`elo2018.json`/`elo2022.json` | backtest histórico 124 partidos |

**Hallazgo clave:** con muestra chica el tuning no rinde más (varianza irreducible del fútbol); lo que vale es el modelo base (fuerza+forma+bajas+localía+emoción). El modelo de agentes supera al Elo puro.

---

## 4. TORNEO / BRACKET
| Archivo | Qué hace |
|---|---|
| `tournament_state.json` | 12 grupos + 72 fixtures (jugados + pendientes) |
| `tournament_sim.py` + `tournament_probs.json` | Monte Carlo 50,000 torneos → probabilidades de avance/campeón |
| `bracket_played.json` | torneo jugado 1×1 con modelo completo (75 agentes) |
| `draw_bracket.py` → `bracket_mundial2026.png` / `.pdf` | bracket visual |

---

## 5. PREDICCIONES DIARIAS (modelo completo, 1 agente por jugador)
Por partido: `match_<ID>.json` (entorno + 11 gemelos por equipo con bio/familia/personalidad/monólogo/atributos/físico). **24 archivos `match_*.json`** generados.
- Flujo: workflow (Fase 1 alineaciones+entorno → Fase 2-3 agente por jugador) → `match_*.json` → `sim_match.py` → predicción.
- `export_predictions.py` → `predictions.json` (probabilidades por mercado para la app).
- `results.json` → resultados reales para liquidar.

**Track record:** ~9/12 ganadores (75%). Aciertos en favoritos claros (Brasil, Japón, Marruecos, P.Bajos, México) y volados del lado correcto (USA, Alemania). Fallos = upsets de ~20-30% (Paraguay, Curazao) — irreducibles.

---

## 6. SISTEMA DE APUESTAS — `wuru-bets/` (Next.js + Neon)
**Estado: construido y probado en local (Docker + Postgres). Build OK, dashboard funcional.**

### Estructura
| Archivo | Función |
|---|---|
| `app/page.tsx` | dashboard (KPIs, curva de saldo, posiciones abiertas, liquidadas) |
| `components/BankrollChart.tsx` | curva de bankroll (recharts) |
| `lib/betting.ts` | EV, de-vig (potencia), **Kelly fraccionado**, **CLV**, formato MXN |
| `lib/engine.ts` | `placeBets()`: value finder + staking ¼ Kelly + cuotas (sintéticas por ahora) |
| `lib/db.ts` | conexión Postgres (Neon en prod, Docker en dev) |
| `lib/queries.ts` | consultas + KPIs (ROI, yield, CLV, hit rate) |
| `lib/ai.ts` | conectores **GLM 5.2** (z.ai, barato) + **Claude** (estrategia) |
| `scripts/dbinit.ts` | crea tablas + bankroll **100,000 MXN** |
| `scripts/seed.ts` | siembra apuestas de valor desde `predictions.json` |
| `scripts/settle.ts` | liquida con `results.json` → P&L + CLV + curva |
| `app/api/cron/route.ts` | cron diario: ingiere predicciones (POST) y coloca apuestas |
| `app/api/health/route.ts` | health check |
| `docker-compose.yml` | Postgres local | `vercel.json` | framework + cron diario |

### Reglas del sistema
- **Bankroll: 100,000 MXN** (virtual / paper trading).
- **Staking: ¼ Kelly**, tope 3% por apuesta. **NUNCA Martingale** (stake por valor, jamás por pérdida).
- **Solo apostar con EV ≥ 5%** (modelo prob > prob implícita de la cuota).
- **Timing:** correr en la mañana, colocar ~1 día antes (mejores momios); guardar apertura/cierre para **CLV**.
- **Métricas de validación:** ROI, Yield, **CLV** (la de oro), calibración.

### Cómo correr en local
```bash
cd "/Users/issacvm/Documents/Futbol Wuru"
python3 export_predictions.py            # genera predictions.json
cd wuru-bets
cp -n .env.example .env
docker compose up -d                      # Postgres local
npm install
npm run db:init                           # tablas + bankroll 100k
npm run seed                              # coloca apuestas de valor
npm run start                             # http://localhost:3000
# liquidar: crear ../results.json y `npm run settle`
```

### Estado de la última corrida local
- 24 partidos → 23 apuestas de valor colocadas, exposición ~28k MXN.
- 8 partidos liquidados con resultados reales (J2) → 10 apuestas, bankroll ~74,302 MXN.

---

## 7. DECISIONES Y REGLAS CLAVE (no cambiar sin razón)
1. **"Correr el modelo del .md"** = ejecutar el runbook completo (sección 21 de `estrategia de analisis.md`), 5 fases, sin omitir nada.
2. **Jamás omitir nada** · **hasta 200 agentes/ejecución** · **no escatimar recursos** · **1 agente por jugador con contexto real**.
3. La **simulación Monte Carlo NO gasta tokens** (Python local gratis). El costo está en los agentes de investigación.
4. **Anti-Martingale** siempre.
5. **Paper trading primero** (mín. 50-100 apuestas, foco en CLV) antes de pensar en dinero real. Juego responsable.

---

## 8. ARQUITECTURA DE COSTOS (plan)
- **Investigación pesada (88 agentes/partido):** mover de Claude a **GLM 5.2** (vía z.ai/SiliconFlow, ~10x más barato). Mejor open-source MIT del benchmark revisado.
- **Estrategia/valor:** Claude.
- **Simulación + matemática de apuestas:** Python/TS local (gratis).
- Costo objetivo: **~$3-6 por jornada de 4 partidos** (vs ~$25-40 actual).
- Una corrida de 4 partidos del modelo completo = ~3.5M tokens (solo investigación).

---

## 9. CAVEATS HONESTOS (qué NO está resuelto)
1. **Cuotas sintéticas:** la app aún genera momios artificiales (modelo + margen + ruido). El P&L es ilustrativo. **Falta conectar feed real de momios** (The Odds API / Pinnacle) para edge real.
2. **GLM/Claude keys:** no configuradas aún (`.env`). El dashboard funciona sin ellas; la investigación barata se activa al ponerlas.
3. **Datos Tier-3 (HRV, carga de entrenamiento, GPS real):** no son públicos → van como proxy (documentado en sección 20 del .md).
4. **Despliegue Vercel+Neon:** configurado pero no ejecutado (falta cuenta/keys).
5. **Tuning:** ya tocó techo con la muestra actual; mejora real = más datos.

---

## 10. PRÓXIMOS PASOS (orden de impacto)
1. **🥇 Conectar momios reales** (The Odds API, plan gratis) → reemplazar `syntheticOdds()` → value/P&L reales.
2. **Activar GLM 5.2** (key en `.env`) → abaratar la investigación 10x.
3. **Desplegar a Vercel + Neon** (todo configurado).
4. **Auto-ingesta:** el modelo Python hace POST diario a `/api/cron`.
5. **Otros deportes/ligas** (basket/tenis necesitan modelo de scoring propio; la infraestructura se reutiliza).
6. **Re-calibrar tras J3 + octavos** (más muestra → bootstrap con poder).

---

## 11. CÓMO RETOMAR (resumen ejecutivo para la próxima sesión)
- **Modelo:** ver `estrategia de analisis.md` (24 secciones, runbook en sec. 21, reglas en sec. 22).
- **Predecir un partido:** workflow del modelo completo → `match_*.json` → `python3 sim_match.py match_X.json`.
- **App de apuestas:** `wuru-bets/` (README con pasos). Corre con Docker en local; lista para Vercel+Neon.
- **Validación:** `backtest_score.py`, `calibrate.py`, `hist_calibrate.py`.
- **Memoria persistente:** `~/.claude/.../memory/futbol-wuru-modelo.md`.

---
*Documento de avances generado el 23-jun-2026. Preserva el estado completo del sistema Wuru: modelo predictivo (validado, calibrado, ~75% acierto), proyección de torneo, bracket visual, y sistema de apuestas con paper trading (Next.js + Neon, probado en local). Acompaña a `estrategia de analisis.md`.*

---
---

# 🚀 ACTUALIZACIÓN MAYOR (24-jun-2026) — Sistema de apuestas EN PRODUCCIÓN

> Desde la última versión se construyó, conectó y **desplegó** el sistema completo de apuestas con datos reales. Esto es el estado actual operativo.

## A. App de apuestas `wuru-bets/` — DESPLEGADA
- **EN VIVO:** https://nova-wuru.vercel.app (Vercel) + **Neon Postgres** (DB).
- **GitHub:** https://github.com/novacoinotc/NovaWuru (rama `main`, PÚBLICO). Autenticado como `novacoinotc`.
- **Stack:** Next.js 15.5 (App Router) + driver **@neondatabase/serverless** (prod) / postgres TCP (local Docker).
- **Dashboard:** KPIs (P&L, ROI, yield, CLV, acierto, exposición), curva de saldo (recharts), posiciones abiertas (singles + parleys), liquidadas. Chips real/sint.
- **Bankroll paper trading: 100,000 MXN.**

## B. IA conectada (claves en `wuru-bets/.env`, gitignored — NUNCA subir)
- **GLM 5.2 (plan Coding MAX, ~$150/mes):** `GLM_API_KEY=10d163...` · endpoint **Anthropic-compatible** `https://api.z.ai/api/anthropic` · modelo `glm-4.6` · **web search activo**. (OJO: el plan Coding NO sirve en el endpoint paas/v4 de tokens; solo en /anthropic.)
- **The Odds API (plan FREE, 500 req/mes):** `ODDS_API_KEY=f0bb8d31...` · multi-liga vía `ODDS_SPORT_KEYS`.
- **Neon DB:** `DATABASE_URL` (pooled, sslmode=require) — ya en Vercel (integración Neon Marketplace) y en .env local.
- Claude: opcional (capa estrategia), sin key por ahora.

## C. Pipeline de producción (archivos nuevos)
| Archivo | Función |
|---|---|
| `glm_research.py` | Research paralelo con GLM (1 agente/jugador, 11v11 garantizado, ~2min/partido, ~300K tokens) |
| `scanner.py` | **Escáner multi-liga**: analiza TODAS las ligas activas → scan rápido GLM (1 call/partido) → rankea por valor → top N → modelo completo a top N → acumula apuestas |
| `orchestrator.py` | Variante: descubre por ventana de horas y corre el flujo |
| `settle_auto.py` | Auto-liquidación: jala resultados reales (Odds API /scores) → `results.json` → liquida |
| `export_predictions.py` | match_*.json → predictions.json (probs por mercado) |
| `wuru-bets/lib/engine.ts` | `placeBets`: value finder + ¼ Kelly + **parleys** + dedup (mantiene momio temprano) |
| `wuru-bets/lib/odds.ts` | momios reales multi-liga, mediana de casas, de-vig, match por nombre |
| `wuru-bets/lib/betting.ts` | EV, Kelly, CLV, de-vig |
| `wuru-bets/scripts/{dbinit,seed,accrue,settle}.ts` | init / sembrar(reset) / acumular(no reset) / liquidar |
| `scheduler/` (launchd) | **3 escaneos/día (09/15/21) + liquidación 23:30**. `install.sh` los instala. |

## D. Estrategia de apuestas (implementada)
- **Mercados:** 1X2, Over/Under 2.5, BTTS + **parleys** (legs ≥55% prob, de partidos distintos, stake ≤1%).
- **Valor:** prob efectiva = **30% modelo + 70% mercado** (de-vig). Apuesta solo si **EV ≥5%**, **edge ≤15%** (rechaza errores del modelo), **cuota ≤7**.
- **Staking:** **¼ Kelly**, tope 3%/apuesta. **NUNCA Martingale.**
- **Captura de momios tempranos:** ventana **5 días**, 3 scans/día, **dedup** (no re-apuesta lo ya abierto → conserva el momio temprano). Guarda apertura vs cierre → **CLV**.

## E. Flujo diario automático
```
09:00/15:00/21:00 → scanner.py (todas las ligas → top 15 por valor → modelo completo → acumula en Neon)
23:30 → settle_auto.py (resultados reales → liquida singles+parleys → saldo + CLV)
Dashboard (Neon) actualizado en vivo
```

## F. Estado actual (corrida real de hoy)
- Escaneó 15 partidos → top 6 → modelo completo → **5 apuestas de valor** (Mundial + Suecia 2ªdiv + China). Saldo ~96,792 MXN.

## G. Bugs encontrados y arreglados (memoria)
1. Orden de carga `.env` en scripts (importaba lib/db antes de cargar env → escribía en Docker). Fix: `lib/loadenv.ts` primero.
2. Driver porsager `postgres` NO conecta a Neon (TLS TransformError). Fix: `@neondatabase/serverless`.
3. Momios: orientación local/visitante invertida → cuota del equipo equivocado. Fix: match por nombre.
4. Momios: "best price" capturaba outliers (edge falso 400%). Fix: **mediana** + de-vig + caps.
5. Modelo subestima favoritos (vs mercado) → value finder ingenuo apostaba ruido. Fix: mezcla 70% mercado + topes.
6. GLM JSON parse (array vs objeto) → jugadores perdidos. Fix: parse robusto + reintento + relleno (11v11 garantizado).
7. **Vercel Root Directory** apunta al repo raíz (sin app) → git auto-deploy compila vacío (404). **PENDIENTE:** poner Root Directory = `wuru-bets` en Vercel Settings. Workaround: `cd wuru-bets && vercel --prod`.

## H. Caveats honestos
- **Volumen real bajo ahora** (Europa en receso hasta ~agosto): ~15 partidos/día. En agosto: 100-200/día → ahí sí 15 apuestas top.
- **Odds API free (500/mes):** 3 scans/día multi-liga ~excede → para multi-scan real necesita **plan pago (~$30/mes)**.
- **Córners/faltas/tarjetas:** NO modelados (el modelo simula goles); momios solo en plan pago. = v2.
- **launchd** corre con la sesión de la Mac activa; para 24/7 sin Mac → servidor/cron en nube.
- **CLV** validará la teoría de "momios mejores temprano" tras unos días de datos.

## I. PRÓXIMO (idea del usuario): "Apuestas Soñadoras" 🎰
- Parleys **longshot** de varios partidos, stake mínimo (~100 MXN), **multiplicador alto** (paga mucho).
- Construir con análisis preciso: combinar selecciones con **probabilidad media-alta** (no basura) para que el combo tenga chance real pero pague grande. Tipo "billete de lotería con cabeza".
- Pendiente: módulo `dream_parlay` (selecciona N legs de prob media-alta, stake fijo 100, separa del bankroll principal o lo marca como "soñadora").

## J. Cómo retomar (post-compactación)
- **Correr el día manual:** `cd "/Users/issacvm/Documents/Futbol Wuru" && python3 scanner.py 15` (necesita env de wuru-bets/.env).
- **Liquidar:** `python3 settle_auto.py`.
- **Deploy:** `cd wuru-bets && vercel --prod` (hasta arreglar Root Directory en Vercel).
- **Dashboard:** https://nova-wuru.vercel.app
- Claves en `wuru-bets/.env` (local, gitignored). Vercel ya tiene env vars de producción.

---
*Actualización 24-jun-2026: sistema de apuestas en producción (Vercel+Neon), GLM Max conectado, escáner multi-liga + parleys + auto-liquidación + scheduler diario. Pendiente: Root Directory en Vercel + módulo "apuestas soñadoras". Chat por compactarse — este doc preserva el estado completo.*
