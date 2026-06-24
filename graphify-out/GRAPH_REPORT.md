# Graph Report - .  (2026-06-24)

## Corpus Check
- 92 files · ~444,125 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 292 nodes · 434 edges · 29 communities (25 shown, 4 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.84)
- Token cost: 60,000 input · 6,000 output

## Community Hubs (Navigation)
- [[_COMMUNITY_App API y conectores IA|App API y conectores IA]]
- [[_COMMUNITY_Dependencias npm|Dependencias npm]]
- [[_COMMUNITY_Config TypeScript|Config TypeScript]]
- [[_COMMUNITY_Research GLM y comparacion|Research GLM y comparacion]]
- [[_COMMUNITY_Bracket simulado (campeon Canada)|Bracket simulado (campeon Canada)]]
- [[_COMMUNITY_Validacion y 3 capas del modelo|Validacion y 3 capas del modelo]]
- [[_COMMUNITY_Motor de partido (sim_match)|Motor de partido (sim_match)]]
- [[_COMMUNITY_Dashboard UI|Dashboard UI]]
- [[_COMMUNITY_Estrategia de apuestas (KellyCLV)|Estrategia de apuestas (Kelly/CLV)]]
- [[_COMMUNITY_Motor gemelos digitales v1|Motor gemelos digitales v1]]
- [[_COMMUNITY_Motor agente-por-jugador|Motor agente-por-jugador]]
- [[_COMMUNITY_Motor gemelos v2 (calibrado)|Motor gemelos v2 (calibrado)]]
- [[_COMMUNITY_Simulador de torneo|Simulador de torneo]]
- [[_COMMUNITY_Calibracion historica|Calibracion historica]]
- [[_COMMUNITY_Modulo 14|Modulo 14]]
- [[_COMMUNITY_Modulo 15|Modulo 15]]
- [[_COMMUNITY_Modulo 16|Modulo 16]]
- [[_COMMUNITY_Modulo 17|Modulo 17]]
- [[_COMMUNITY_Modulo 18|Modulo 18]]
- [[_COMMUNITY_Modulo 19|Modulo 19]]
- [[_COMMUNITY_Modulo 20|Modulo 20]]
- [[_COMMUNITY_Modulo 21|Modulo 21]]
- [[_COMMUNITY_Modulo 22|Modulo 22]]
- [[_COMMUNITY_Modulo 23|Modulo 23]]
- [[_COMMUNITY_Modulo 24|Modulo 24]]
- [[_COMMUNITY_Modulo 25|Modulo 25]]
- [[_COMMUNITY_Modulo 26|Modulo 26]]
- [[_COMMUNITY_Modulo 27|Modulo 27]]

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 16 edges
2. `placeBets()` - 13 edges
3. `metrics()` - 8 edges
4. `worker()` - 8 edges
5. `Dashboard()` - 8 edges
6. `Bracket simulado Mundial 2026 (modelo maestro, partido por partido)` - 8 edges
7. `scripts` - 7 edges
8. `research_match()` - 6 edges
9. `base_idx()` - 6 edges
10. `main()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `worker()` --calls--> `pace_idx()`  [INFERRED]
  sim_gemelos_v2.py → sim_match.py
- `p1x2()` --calls--> `metrics()`  [EXTRACTED]
  compare_glm_claude.py → export_predictions.py
- `worker()` --calls--> `pace_idx()`  [INFERRED]
  sim_gemelos.py → sim_match.py
- `Wuru Bets README` --references--> `Estrategia de Análisis — documento maestro del modelo`  [INFERRED]
  wuru-bets/README.md → estrategia de analisis.md
- `main()` --calls--> `research_match()`  [EXTRACTED]
  compare_glm_claude.py → glm_research.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline modelo→app: simulación a apuestas de valor** — avances_del_sistema_sim_match, avances_del_sistema_export_predictions, avances_del_sistema_predictions_json, wuru_bets_readme_app, avances_del_sistema_lib_engine [INFERRED 0.85]
- **Modelo de 3 capas triangulado** — avances_del_sistema_capa_estadistica, avances_del_sistema_capa_agente_jugador, avances_del_sistema_capa_gemelos_digitales [INFERRED 0.85]
- **Matemática de apuestas: value + Kelly + CLV** — avances_del_sistema_value_betting, avances_del_sistema_kelly, avances_del_sistema_clv, avances_del_sistema_lib_betting [INFERRED 0.75]

## Communities (29 total, 4 thin omitted)

### Community 0 - "App API y conectores IA"
Cohesion: 0.10
Nodes (28): GET(), POST(), GET(), aiReady(), Msg, clv(), devig(), ev() (+20 more)

### Community 1 - "Dependencias npm"
Cohesion: 0.08
Nodes (24): dependencies, next, postgres, react, react-dom, recharts, devDependencies, tailwindcss (+16 more)

### Community 2 - "Config TypeScript"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 3 - "Research GLM y comparacion"
Cohesion: 0.20
Nodes (13): main(), p1x2(), get_env(), get_twin(), get_xi(), glm(), main(), parse_json() (+5 more)

### Community 4 - "Bracket simulado (campeon Canada)"
Cohesion: 0.20
Nodes (16): Campeon proyectado: Canada, Final: Canada 2 (p) vs England 2, Bracket simulado Mundial 2026 (modelo maestro, partido por partido), Final decidida por penales (p=penales), Ronda 16avos (R32), Ronda Cuartos (4tos), Final, Ronda Octavos (8vos / R16) (+8 more)

### Community 5 - "Validacion y 3 capas del modelo"
Cohesion: 0.15
Nodes (15): Backtest / validación, backtest_score.py, Calibración, Capa agente-por-jugador, Capa estadística (Poisson/Dixon-Coles/Elo/mercado), Capa gemelos digitales (bio + física + entorno), Dixon-Coles, Elo (motor calibrado) (+7 more)

### Community 6 - "Motor de partido (sim_match)"
Cohesion: 0.32
Nodes (13): main(), metrics(), aerial_idx(), arr(), base_idx(), create(), defend(), elo_base_lams() (+5 more)

### Community 7 - "Dashboard UI"
Cohesion: 0.27
Nodes (9): Dashboard(), pct(), fmtMXN(), Bet, getBankroll(), getHistory(), getOpenBets(), getSettledBets() (+1 more)

### Community 8 - "Estrategia de apuestas (Kelly/CLV)"
Cohesion: 0.17
Nodes (13): Regla anti-Martingale, CLV (Closing Line Value), app/api/cron/route.ts (ingesta diaria de predicciones), Cuotas sintéticas (syntheticOdds), export_predictions.py → predictions.json, Staking ¼ Kelly fraccionado, lib/betting.ts (EV, de-vig, Kelly, CLV), lib/engine.ts (placeBets value finder + ¼ Kelly) (+5 more)

### Community 9 - "Motor gemelos digitales v1"
Cohesion: 0.23
Nodes (12): baseline_indices(), load(), main(), Pesos de contribucion (ataque, defensa, creatividad) segun posicion., Convierte los 22 gemelos en arrays alineados + mascaras de equipo., Indices ofensivo/defensivo del equipo para esta tanda de simulaciones.        fo, Version determinista (dia neutro) para anclar/normalizar., role_weights() (+4 more)

### Community 10 - "Motor agente-por-jugador"
Cohesion: 0.33
Nodes (9): build_lambdas(), is_attacker(), is_defender(), load_minds(), m(), main(), report(), run() (+1 more)

### Community 11 - "Motor gemelos v2 (calibrado)"
Cohesion: 0.40
Nodes (9): baseline(), gk_index(), load(), main(), role_weights(), team_create(), team_def(), to_arrays() (+1 more)

### Community 12 - "Simulador de torneo"
Cohesion: 0.44
Nodes (7): bipartite(), elo(), ko_winner(), lam(), norm(), run_chunk(), sim_goals()

### Community 13 - "Calibracion historica"
Cohesion: 0.43
Nodes (7): build_rows(), ll_for(), main(), metrics(), norm(), pois(), probs()

### Community 14 - "Modulo 14"
Cohesion: 0.46
Nodes (7): aggregate(), fair_odds(), main(), print_report(), run_ensemble(), simulate(), _worker()

### Community 15 - "Modulo 15"
Cohesion: 0.57
Nodes (6): load(), main(), metrics_for(), outc(), pois(), probs()

### Community 16 - "Modulo 16"
Cohesion: 0.47
Nodes (3): ll_for_config(), pois(), probs()

### Community 17 - "Modulo 17"
Cohesion: 0.70
Nodes (4): dc_probs(), main(), outcome(), pois()

### Community 19 - "Modulo 19"
Cohesion: 0.70
Nodes (4): main(), norm(), pois(), probs()

### Community 20 - "Modulo 20"
Cohesion: 0.60
Nodes (3): load_cal(), pois(), predict()

### Community 21 - "Modulo 21"
Cohesion: 0.67
Nodes (4): Arquitectura de costos (GLM barato + Claude estrategia), Claude (estrategia), GLM 5.2 (investigación barata, z.ai), lib/ai.ts (conectores GLM 5.2 + Claude)

### Community 22 - "Modulo 22"
Cohesion: 0.50
Nodes (3): crons, framework, $schema

### Community 24 - "Modulo 24"
Cohesion: 0.67
Nodes (3): AVANCES DEL SISTEMA — memoria del proyecto Wuru, Estrategia de Análisis — documento maestro del modelo, Wuru Bets README

### Community 25 - "Modulo 25"
Cohesion: 0.67
Nodes (3): lib/db.ts (Postgres/Neon), Postgres / Neon DB, wuru-bets docker-compose (Postgres local)

## Knowledge Gaps
- **65 isolated node(s):** `metadata`, `Msg`, `isManaged`, `g`, `ALIASES` (+60 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `pace_idx()` connect `Motor gemelos digitales v1` to `Motor gemelos v2 (calibrado)`, `Motor de partido (sim_match)`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `worker()` connect `Motor de partido (sim_match)` to `Motor gemelos digitales v1`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **What connects `Pesos de contribucion (ataque, defensa, creatividad) segun posicion.`, `Convierte los 22 gemelos en arrays alineados + mascaras de equipo.`, `Indices ofensivo/defensivo del equipo para esta tanda de simulaciones.        fo` to the rest of the system?**
  _70 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App API y conectores IA` be split into smaller, more focused modules?**
  _Cohesion score 0.0975609756097561 - nodes in this community are weakly interconnected._
- **Should `Dependencias npm` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `Config TypeScript` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._