# Expansión Wuru a nuevos deportes — Informe (20-jul-2026, Opus 4.8 web research)

Nuestro método (Monte Carlo + gemelos digitales IA + valor vs The Odds API + ¼ Kelly + CLV) es un **motor de contexto humano**: rinde donde las líneas son blandas, el evento es 1-vs-1 o de plantel corto, y el contexto (fatiga, motivación, lesiones, clima) mueve el precio.

## RANKING TOP 5 (edge × volumen × fit × facilidad)

1. **TENIS (Challengers/ITF)** — fit perfecto (1v1, contexto decisivo), 500-1,000 partidos/semana todo el año, edge real en tours bajos. Modelo: Markov punto→juego→set (Klaassen & Magnus; Barnett & Clarke) + Elo por superficie (Tennis Abstract). Blend académico ATP: 57.7% Elo + 12.9% Elo-superficie + 29.4% mercado. Odds API: claves por torneo `tennis_atp_*`/`tennis_wta_*` (sin Challengers — ahí se necesita feed extra). ATP top es eficientísimo; el edge vive abajo e in-play.
2. **COMBATE (Box/MMA-UFC)** — fit máximo con gemelos (psicología, campo, corte de peso, choque de estilos); líneas blandas "de opinión"; edge en props (método/rounds), prospectos y reemplazos de corto aviso. Odds API: `boxing_boxing`, `mma_mixed_martial_arts` (h2h+totals). UFC ~40-45 cards/año. Modelos serios ~67-68% acc (claims de 80% = fuga de datos). Datos: ufcstats/Tapology/BoxRec (gratis).
3. **BÁSQUET internacional (Euroliga + props NCAAB)** — eficiencia por posesión (Four Factors), pace, EPM/DARKO. NBA principal casi imbatible → ir a props (tardan en ajustar a lineup news), Euroliga (info de rotación asimétrica), college. Odds API: `basketball_nba`, `basketball_euroleague`, `basketball_ncaab` (+props con plan Business). NBA arranca 20-oct-2026.
4. **NCAAF (college football)** — 60-80 juegos/sábado, líneas lentas, 130+ equipos, transfer portal, clima crítico (viento >15mph mueve totales), lesiones QB. Odds API: `americanfootball_ncaaf`. NFL principal = el mercado más afilado del mundo → evitarlo como núcleo. Temporada: 29-ago-2026.
5. **GOLF (PGA)** — strokes-gained + course-fit + MC; Odds API `golf_*_winner` (outrights). Edge en mid/longshots. DataGolf API ~$30/mo.

**Descartados como núcleo:** MLB (fit moderado, mercado afilado; LMB sin cobertura en Odds API), amistosos de fútbol (edge condicional: solo tras XI confirmado; sin clave de API fiable), F1/darts/eSports/snooker (gran fit analítico pero NO están en The Odds API → requieren feed extra, ej. OpticOdds).

## ROADMAP

| Fase | Deporte | Esfuerzo | Datos extra/costo |
|---|---|---|---|
| 1 | Tenis | 3-4 sem | Jeff Sackmann/Tennis Abstract CSV (gratis), API-Tennis p/Challengers (~$0-50/mo) |
| 2 | Combate | 2-3 sem | ufcstats scrape gratis; Odds API ya cubre; capa gemelos reutilizable casi directa |
| 3 | Básquet intl/props | 3-4 sem | Odds API plan Business (~$119/mo, desbloquea props) + nba_api gratis |
| 4 | NCAAF | 2-3 sem | cfbfastR/CFBD gratis + OpenWeather |
| 5 | Golf | 2 sem | DataGolf ~$30/mo |

**Infra transversal:** (1) plan Business de Odds API = mayor multiplicador de edge (props); (2) generalizar la capa de gemelos de jugador-fútbol a peleador/tenista (1 agente por competidor) es reutilización casi directa; (3) CLV como métrica rectora en cada deporte nuevo antes de escalar stake.

## Calendario 2026-27 relevante
- Tenis: todo el año (US Open 31-ago→13-sep-2026)
- UFC/Box: semanal, sin offseason
- Euroliga 24-sep · NBA 20-oct · NCAAB nov · NCAAF 29-ago · NFL 9-sep
- MLB abr-oct · LMB 16-abr→6-ago
