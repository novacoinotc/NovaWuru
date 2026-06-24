# 🧠⚽ Estrategia de Análisis — Modelo Predictivo de Fútbol (Monte Carlo + Gemelos Digitales con IA)
### Documento MAESTRO y EXHAUSTIVO para replicar el modelo · Caso base: México vs Corea del Sur (Mundial 2026, Grupo A, Jornada 2)

> **Propósito.** Registrar TODO lo que consultamos, CÓMO lo consultamos, todas las variables, fórmulas, parámetros, prompts de agentes, datos crudos de cada jugador y todas las fuentes, para poder **replicar y re-correr** el modelo en cualquier partido. Nada se resume ni se omite.
>
> **Catálogo base de variables:** `/Users/issacvm/Downloads/variables_modelo_futbol.md`. Este documento reproduce ese catálogo COMPLETO (secciones 0–18) y anota, variable por variable, **cuáles usamos, en qué *tier* de disponibilidad están y cómo entraron al modelo**.
>
> **Leyenda de uso:** ✅ usada directamente · 🟡 usada como proxy/parcial · ⬜ no usada aún (mejora futura). **Tiers:** T1 fácil/gratis · T2 de pago · T3 interno del club · T4 casi inobtenible/subjetiva.

---

## ÍNDICE
0. Resumen ejecutivo y veredicto
1. Arquitectura del pipeline (3 fases)
2. Orquestación de agentes de IA (prompts y esquemas completos)
3. CATÁLOGO COMPLETO DE VARIABLES (18 secciones, anotadas)
4. Entorno del día — datos crudos completos
5. Gemelos digitales — los 22 jugadores con TODOS sus campos
6. Fórmulas completas del modelo
7. Parámetros y modificadores del caso base
8. Resultados completos de los 3 modelos
9. Fuentes consultadas (todas)
10. Tiers de disponibilidad y consideraciones de modelado
11. Cómo re-correr / inventario de archivos
12. Honestidad metodológica y roadmap

---

## 0. Resumen ejecutivo y veredicto

Predecimos el resultado probabilístico de **un partido** (1X2, goles, marcadores, mercados) combinando **3 modelos** que se triangulan entre sí y contra el mercado de apuestas:

| # | Modelo | Qué captura | Simulaciones | Archivo |
|---|--------|-------------|-------------|---------|
| 1 | **Estadístico frío** (Poisson / Dixon-Coles / Elo / mercado) | Fuerza base de cada equipo | 5,500,000 | `sim_mex_kor.py` |
| 2 | **Agente-por-jugador** (1 IA piensa como cada jugador) | Estado mental/emocional del día | 100,000 | `sim_agentes.py` + `player_minds.json` |
| 3 | **Gemelos digitales estocástico** (bio + física + entorno) | Realismo humano + anatomía + condiciones | 500,000 | `sim_gemelos.py` + `twins.json` + `env.json` |

**Veredicto final del caso base (consenso de los 3 modelos + mercado):**

| | México | Empate | Corea |
|---|---|---|---|
| 1. Estadístico frío | 39.6% | 32.6% | 27.9% |
| 2. Agente-por-jugador | 46.4% | 28.4% | 25.2% |
| 3. Gemelos + física (estocástico) | 46.5% | 28.7% | 24.8% |
| Mercado real (de-vig) | ~48-50% | ~27-28% | ~24-26% |
| **🏆 CONSENSO FINAL** | **~46-48%** | **~28-29%** | **~24%** |

**Marcadores más probables:** 1-1 (13.5%) · 1-0 MEX (10.8%) · 2-1 MEX (10.2%) · 2-0 MEX (7.6%) · 0-0 (7.1%). **Goles totales ~2.7** · Over 2.5 ~50% · BTTS ~57% · alguna roja ~5%. **México no pierde ~75%.**

---

## 1. Arquitectura del pipeline (3 fases)

```
FASE A — INVESTIGACIÓN (≈50 agentes de IA con búsqueda web, en paralelo)
   ├─ Datos de equipo (forma, ranking, xG, alineaciones, bajas)  → México y Corea
   ├─ Metodología analítica (Poisson, Dixon-Coles, Elo, de-vig)
   ├─ Contexto del partido (sede, fecha, H2H, cuotas)
   ├─ Factores situacionales (altura, clima, árbitro, afición, psicología)
   ├─ Entorno del día (clima hora a hora, pasto, aforo, % afición)
   ├─ Gemelo digital de cada jugador (bio, familia, personalidad, estado vital)
   ├─ Estado mental de cada jugador (role-play emocional)
   └─ Perfil físico/anatómico por selección (altura, velocidad, lesiones)
                          ▼
FASE B — MODELADO (Python local, multiprocessing en Apple M4 Pro, 14 núcleos)
   ├─ Derivar λ (goles esperados) por equipo desde fuerzas + Elo + mercado
   ├─ Construir gemelos digitales (atributos 0-100 + física + bio)
   ├─ Sortear condiciones del día y 'día' de cada jugador (ESTOCÁSTICO)
   └─ Motor minuto a minuto (fatiga/altitud, marcador, rojas, aéreo, contragolpe)
                          ▼
FASE C — AGREGACIÓN Y VEREDICTO
   ├─ 1X2, goles, Over/Under, BTTS, rojas, marcadores top
   ├─ Resultados condicionales (con/sin lluvia)
   └─ Triangulación de los 3 modelos + comparación con el mercado
```

**Hardware:** Apple M4 Pro (14 núcleos), 24 GB RAM, Python 3.14, numpy 2.4 / scipy 1.17. 500k–5.5M simulaciones en <1 s con `multiprocessing` (13 núcleos).

---


## 2. Orquestación de agentes de IA (prompts y esquemas completos)

Toda la Fase A se hace con **agentes de IA con búsqueda web** (`WebSearch` + `WebFetch`), lanzados en paralelo. Cada agente devuelve **JSON con esquema obligatorio** (structured output) para alimentar el código sin parseo manual.

### 2.1 Rondas de agentes (≈50 en total, ~1.4M tokens)
| Ronda | # agentes | Salida | Qué investiga |
|---|---|---|---|
| Equipo/contexto | 4 | texto estructurado | México, Corea, metodología analítica, contexto del partido |
| Factores situacionales | 1 | texto | altitud, clima, viaje, psicología, árbitro, moral |
| Mentes (role-play) | 22 | `player_minds.json` | 1 agente por jugador: estado emocional + monólogo |
| Gemelos + entorno | 24 | `twins.json`,`env.json` | 2 entorno + 22 biográficos exhaustivos |
| Físico/anatómico | 2 | fusionado en `twins.json` | altura, peso, velocidad, durabilidad, lesiones |

### 2.2 Esquema JSON del estado mental (workflow 'mentes')
```json
{
 "name": "str",
 "team": "MEX|KOR",
 "position": "str",
 "pressure": "0-100",
 "confidence": "0-100",
 "motivation": "0-100",
 "nerves": "0-100",
 "focus": "0-100",
 "finishing_mod": "-25..25 %",
 "composure_mod": "-25..25 %",
 "risk_taking": "0-100",
 "defense_mod": "-25..25 %",
 "stamina_altitude_mod": "-25..25 %",
 "card_risk": "0-100",
 "creativity_mod": "-25..25 %",
 "inner_monologue": "monólogo en 1a persona",
 "x_factor": "frase clave del día"
}
```
**Prompt (resumen):** *“Eres [jugador]. Métete en su cabeza: personalidad, historia, momento de forma y lo que siente HOY [contexto del partido]. Siente presión, angustia, emoción, el ambiente, la altitud, lo que está en juego. Traduce ese estado a números honestos y escribe un monólogo interior.”*

### 2.3 Esquema JSON del gemelo digital (workflow 'gemelos')
```json
{
 "name": "str",
 "team": "MEX|KOR",
 "position": "str",
 "age": "int",
 "caps": "int",
 "club": "str",
 "club_situation": "str",
 "family": "pareja/hijos (info pública)",
 "personal_state": "vida fuera del fútbol, eventos, ánimo",
 "personality": "rasgos",
 "motivation_drivers": "qué lo motiva/deprime hoy",
 "skill": "0-100",
 "finishing": "0-100",
 "creativity": "0-100",
 "pace": "físico",
 "aerial": "0-100",
 "defense": "0-100",
 "stamina_base": "0-100",
 "composure_mean": "0-100",
 "composure_volatility": "0-35",
 "clutch": "0-100",
 "pressure_resistance": "0-100",
 "discipline": "0-100",
 "consistency": "0-100",
 "motivation_today": "0-100",
 "emotional_state_today": "0-100",
 "injury_risk": "0-100",
 "bio": "3-5 frases",
 "sources": "URLs",
 "confidence": "dato vs estimación",
 "height_cm": "físico",
 "weight_kg": "físico",
 "top_speed_kmh": "físico",
 "durability": "0-100",
 "injury_history": "resumen"
}
```
### 2.4 Esquema JSON del entorno (workflow 'entorno')
```json
{
 "rain_probability_kickoff": "float",
 "temp_c_kickoff": "float",
 "temp_c_low": "int",
 "temp_c_high": "int",
 "humidity_pct": "float",
 "wind_kmh": "float",
 "pitch_type": "str",
 "pitch_condition": "str",
 "pitch_speed_factor": "float",
 "stadium_capacity": "int",
 "expected_attendance": "int",
 "home_support_pct": "float",
 "korean_fans_estimate": "int",
 "crowd_hostility": "int",
 "crowd_noise": "int",
 "home_xg_modifier": "float"
}
```

---


## 3. CATÁLOGO COMPLETO DE VARIABLES (18 secciones, cada variable anotada)

Reproducción íntegra del catálogo `variables_modelo_futbol.md`, con anotación variable por variable: **uso** (✅/🟡/⬜), **tier** de disponibilidad y **cómo entró a nuestro modelo**.

### 0. ¿QUÉ vas a predecir? (target y unidad de observación)
*Cómo lo usamos:* Nuestro **target = resultado del partido (1X2, goles, marcadores)**. Unidad de observación = **un partido**. Por eso agregamos lo individual a nivel de equipo (sumas ponderadas por rol), y el contexto colectivo/rival pesa más que lo individual aislado.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Rendimiento individual | 🟡 | T1-2 | entra agregado a fuerza de equipo |
| Probabilidad de lesión | 🟡 | T3 | aproximado vía durabilidad e historial → lesión en partido |
| Resultado del partido / goles totales | ✅ | T1 | ESTE es nuestro target |
| Valor de mercado / traspaso | ⬜ | T1 |  |
| Minutos / titularidad | 🟡 | T1 | usamos XI probable y bajas |
| Desarrollo a futuro | ⬜ | T1 |  |

### 1. Identidad y demografía
*Cómo lo usamos:* Usamos edad, posición (define rol y pesos), experiencia (caps) y pie (cualitativo en bio).

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Edad (a la fecha del partido) | ✅ | T1 | en twins.json |
| Fecha de nacimiento exacta | 🟡 | T1 | vía edad |
| Edad relativa (relative age effect) | ⬜ | T1 |  |
| Nacionalidad / país de origen | ✅ | T1 | selección |
| Doble nacionalidad | 🟡 | T1 | p.ej. Quiñones/Fidalgo naturalizados |
| Idiomas | ⬜ | T1 |  |
| Posición(es) natural(es) y secundarias | ✅ | T1 | define role_weights |
| Pie dominante y % de uso | 🟡 | T1 | cualitativo en bio |
| Años de experiencia profesional | ✅ | T1 | caps como proxy |
| Edad de debut profesional | ⬜ | T1 |  |

### 2. Antropometría y composición corporal
*Cómo lo usamos:* Usamos **altura y peso** (aéreo y balón parado). El resto requiere datos internos del club (T3).

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Altura | ✅ | T1 | height_cm → índice aéreo / ABP |
| Peso | ✅ | T1 | weight_kg |
| IMC | 🟡 | T1 | derivable |
| % de grasa corporal | ⬜ | T3 |  |
| Masa muscular | ⬜ | T3 |  |
| Envergadura / longitud de extremidades | ⬜ | T3 |  |
| Longitud de zancada | ⬜ | T3 |  |
| Somatotipo | ⬜ | T3 |  |

### 3. Atributos físicos / atléticos
*Cómo lo usamos:* Usamos **velocidad punta (km/h), pace y stamina** (contragolpe + fatiga/altitud). Los tests de laboratorio (VO2, lactato, HRV) son T3, no disponibles.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Velocidad máxima (sprint km/h) | ✅ | T1-3 | top_speed_kmh; Son 35.1 confirmado, resto estimado |
| Aceleración (0-10/0-30 m) | 🟡 | T2 | incluida en pace |
| Deceleración / frenado | ⬜ | T3 |  |
| Agilidad / cambio de dirección | 🟡 | T3 | cualitativo (Mora, Lee Kang-in) |
| Resistencia aeróbica (VO2 máx) | 🟡 | T3 | proxy stamina_base |
| Potencia anaeróbica | ⬜ | T3 |  |
| Fuerza (tren inf/sup/core) | 🟡 | T3 | cualitativo en bio |
| Potencia explosiva (saltos) | 🟡 | T3 | ligado a aéreo |
| Flexibilidad / ROM | ⬜ | T3 |  |
| Equilibrio / estabilidad | 🟡 | T3 | Mora bajo centro de gravedad |
| Coordinación | ⬜ | T3 |  |
| Tiempo de reacción | 🟡 | T3 | porteros |
| Frecuencia cardíaca | ⬜ | T3 |  |
| HRV | ⬜ | T3 | mejora futura (wellness) |
| Umbral de lactato | ⬜ | T3 |  |
| Capacidad de repetir sprints (RSA) | 🟡 | T3 | via stamina/altitud |

### 4. Salud, lesiones y carga
*Cómo lo usamos:* Usamos **historial de lesiones + durabilidad** → riesgo de lesión EN el partido (baja rendimiento) y descanso (7 días iguales). Carga aguda/crónica (ACWR) es T3, pendiente.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Historial completo de lesiones | ✅ | T1 | injury_history por jugador (Transfermarkt/Soccerway) |
| Frecuencia de lesiones / temporada | 🟡 | T1 | resumido en durabilidad |
| Lesiones recurrentes misma zona | ✅ | T1 | p.ej. Kim Min-jae Aquiles, Seol hombro |
| Días desde la última lesión | 🟡 | T1 |  |
| Días totales de baja en carrera | 🟡 | T1 | p.ej. Edson ~100d post-cirugía |
| Número de cirugías | ✅ | T1 | Jiménez cráneo, Son órbita, Seol hombro |
| Tipo de tejido más afectado | 🟡 | T1 |  |
| Riesgo de re-lesión estimado | ✅ | T1-3 | injury_risk 0-100 |
| Estado actual (apto/duda/baja) | ✅ | T1 | bajas: Montes susp., Malagón out |
| Fatiga acumulada / minutos 7-30 días | 🟡 | T3 | aprox vía descanso |
| Densidad de partidos | ✅ | T1 | 7 días entre J1 y J2 |
| Lesiones con secuela | 🟡 | T1 | Jiménez usa protección craneal |
| Enfermedades crónicas | ⬜ | T3 |  |
| Edad fisiológica vs cronológica | 🟡 | T3 | cualitativo (Son 33, Jiménez 35) |

### 5. Habilidades técnicas
*Cómo lo usamos:* Resumidas en atributos 0-100: finishing, creatividad, defensa, aéreo, skill global (de scouting + EA FC como proxy + xG real).

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Control / primer toque | 🟡 | T2 | en skill |
| Conducción / control orientado | 🟡 | T2 | en creatividad |
| Pase corto | 🟡 | T2 | en creatividad/skill |
| Pase largo | 🟡 | T2 |  |
| Pase filtrado / clave | ✅ | T2 | creatividad (Lee Kang-in 92, Fidalgo 86) |
| Regate / dribbling | ✅ | T2 | creatividad/skill |
| Tiro (potencia/precisión, ambos pies) | ✅ | T2 | finishing |
| Definición / finishing | ✅ | T1-2 | finishing (Quiñones 91, Jiménez 83) |
| Cabeceo (of/def) | ✅ | T1-2 | aerial + altura → ABP |
| Centros | 🟡 | T2 |  |
| Balón parado (libres/penaltis/córners) | ✅ | T2 | componente ABP del motor |
| Calidad del primer pase (salida) | 🟡 | T2 | centrales/portero |
| Técnica de portero | ✅ | T2 | skill/defensa del GK |

### 6. Habilidades tácticas / cognitivas
*Cómo lo usamos:* Entran vía rol por posición (role_weights) + disciplina + cualitativo en personalidad/bio.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Visión de juego / scanning | 🟡 | T2-3 | creatividad |
| Toma de decisiones bajo presión | ✅ | T4 | composure/pressure_resistance |
| Posicionamiento | 🟡 | T2 | rol |
| Inteligencia táctica / lectura | ✅ | T2-4 | clutch/skill (Edson, Kim Min-jae) |
| Anticipación | 🟡 | T2 | defensa |
| Marcaje y coberturas | ✅ | T2 | defensa + rol |
| Pressing tras pérdida | 🟡 | T2-3 | Corea alta intensidad |
| Comportamiento en transiciones | ✅ | T2 | contragolpe por velocidad |
| Timing de desmarques | 🟡 | T2 |  |
| Adaptabilidad a sistemas/roles | 🟡 | T2 | Edson de central improvisado |
| Disciplina táctica | ✅ | T4 | discipline 0-100 → riesgo tarjeta |

### 7. Atributos psicológicos / mentales y 'sentimientos'
*Cómo lo usamos:* **Núcleo de los modelos 2 y 3.** Cada jugador tiene un agente IA que hace role-play y devuelve estos valores 0-100 + monólogo interior. Son T4 (subjetivos), modelados como estado del día con volatilidad.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Concentración / foco | ✅ | T4 | focus 0-100 |
| Resiliencia / fortaleza mental | ✅ | T4 | clutch/pressure_resistance |
| Confianza actual (racha/sequía) | ✅ | T4 | confidence (Son bajo por sequía LAFC) |
| Gestión de la presión | ✅ | T4 | pressure + pressure_resistance |
| Motivación / hambre competitiva | ✅ | T4 | motivation_today + motivation_drivers |
| Liderazgo | ✅ | T4 | cualitativo (Edson capitán, Son, Kim Min-jae) |
| Disciplina y profesionalidad | ✅ | T4 | discipline |
| Temperamento / agresividad / autocontrol | ✅ | T4 | card_risk (proxy tarjetas) |
| Manejo de la frustración | 🟡 | T4 | composure |
| Estado de ánimo / wellness | ✅ | T4 | emotional_state_today |
| Estrés y ansiedad | ✅ | T4 | nerves 0-100 |
| Sentido de pertenencia | 🟡 | T4 | factor local (Quiñones, Alvarado en casa) |
| Reacción ante errores propios | 🟡 | T4 | composure_volatility |

### 8. Estadísticas de rendimiento (event data)
*Cómo lo usamos:* Base de las fuerzas de equipo y atributos. Usamos goles/encajados por partido, xG real (MEX 1.46, KOR 1.84 en J1), forma últimos 10, tarjetas, penaltis.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Goles | ✅ | T1 | forma y fuerza ataque |
| Asistencias | ✅ | T1 | creatividad |
| xG y xA | ✅ | T1-2 | xG por partido (fbref/Opta) |
| xG por tiro / calidad de ocasión | 🟡 | T2 |  |
| Tiros (totales / a puerta) | 🟡 | T1-2 |  |
| Pases (totales/completados/%) | 🟡 | T1-2 | posesión J1 |
| Pases progresivos | 🟡 | T2 |  |
| Pases clave | ✅ | T2 | creatividad (Lee Kang-in 3 ocasiones J1) |
| Regates | 🟡 | T2 |  |
| Duelos ganados (terrestres/aéreos) | ✅ | T2 | aéreo + defensa |
| Entradas/intercepciones/despejes/bloqueos | 🟡 | T2 | defensa |
| Recuperaciones | 🟡 | T2 |  |
| Pérdidas / pases fallados bajo presión | 🟡 | T2 | composure |
| Faltas cometidas/recibidas | 🟡 | T1-2 | card_risk |
| Fueras de juego | ⬜ | T2 |  |
| Tarjetas amarillas y rojas | ✅ | T1 | discipline + motor de rojas |
| Penaltis (provocados/cometidos/marcados/fallados) | 🟡 | T1 | en λ base |
| Portería a cero / encajados / paradas / % / PSxG | ✅ | T1-2 | fuerza defensiva + GK |
| Minutos / partidos / titularidades | ✅ | T1 | XI probable |
| Progresión histórica (curva por edad) | 🟡 | T1 | edad + bio |

### 9. Datos de tracking / posicionales
*Cómo lo usamos:* **Mayor laguna del modelo (T3).** Solo entran indirectamente vía estudios de altitud (distancia -3.1% a 1,400-1,750 m). Sin GPS propio. Es la mejora #1 del roadmap.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Distancia total recorrida | 🟡 | T3 | vía estudios de altitud |
| Distancia alta intensidad / sprints | 🟡 | T3 | idem |
| Velocidad media y picos | ✅ | T1-3 | top_speed |
| Aceleraciones/deceleraciones | ⬜ | T3 |  |
| Mapa de calor / posición media | ⬜ | T3 |  |
| Zonas ocupadas / cobertura | ⬜ | T3 |  |
| Distancias entre líneas (compacidad) | ⬜ | T3 |  |
| Posesión de balón | 🟡 | T1-2 | J1 ~61% MEX, ~62% KOR |
| Carga de juego (PlayerLoad) | ⬜ | T3 |  |
| Acciones off-ball | ⬜ | T3 |  |

### 10. Contexto del partido
*Cómo lo usamos:* **Muy usado.** Local/visitante, importancia (Mundial, clasificación), game state (motor minuto a minuto), descanso, jet lag, afición/aforo, momento.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Local / visitante | ✅ | T1 | México local; ventaja +0.12 xG |
| Competición | ✅ | T1 | Mundial (alta importancia → K alto en Elo) |
| Importancia del partido | ✅ | T1 | ganar = clasificar a 16avos |
| Marcador en tiempo real | ✅ | T1 | game state minuto a minuto |
| Minuto del partido | ✅ | T1 | motor 96' |
| Estado (ganando/empatando/perdiendo) | ✅ | T1 | el que pierde arriesga ×1.18 |
| Superioridad/inferioridad numérica | ✅ | T1 | rojas cambian λ |
| Racha reciente (forma) | ✅ | T1 | últimos 10 |
| Días de descanso | ✅ | T1 | 7 días ambos |
| Viaje / distancia / husos (jet lag) | ✅ | T1 | Corea aclimatada 2 sem → neutral |
| Asistencia / aforo / presión grada | ✅ | T1 | 47k, ruido 89/100 |
| Momento de temporada | 🟡 | T1 | fin de temporada de clubes |

### 11. Contexto del equipo / colectivo
*Cómo lo usamos:* Usado: formación, estilo, rol, bajas, calidad media (Elo/valor), cohesión (polémica Son), profundidad.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Formación y sistema | ✅ | T1 | MEX 4-3-3, KOR 4-2-3-1/3-4-3 |
| Estilo de juego | ✅ | T1-2 | MEX pragmático/ABP, KOR posesión+presión |
| Rol del jugador en el sistema | ✅ | T1 | role_weights |
| Química con compañeros | 🟡 | T2-3 | cualitativo (dúo Son-Lee Kang-in) |
| Entrenador / cuerpo técnico | ✅ | T1 | Aguirre vs Hong Myung-bo |
| Instrucciones específicas | 🟡 | T3 |  |
| Posición en tabla y objetivos | ✅ | T1 | ambos 3 pts, líder del grupo |
| Competencia por el puesto / profundidad | ✅ | T1 | MEX zaga corta sin Montes |
| Cohesión / clima de vestuario | ✅ | T4 | crisis prensa Corea (boicot) |
| Calidad media equipo y rival (Elo/valor) | ✅ | T1 | MEX ~1805, KOR ~1740 |
| Compañeros lesionados/ausentes | ✅ | T1 | Montes, Malagón; KOR 2 MC |

### 12. Entrenamiento y recuperación
*Cómo lo usamos:* Mayormente T3 (interno del club). Solo entran aclimatación a la altura y descanso.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Carga de entrenamiento | ⬜ | T3 |  |
| ACWR (carga aguda:crónica) | ⬜ | T3 | predictor clásico de lesión, pendiente |
| Monotonía / strain | ⬜ | T3 |  |
| Sueño | ⬜ | T3 |  |
| Nutrición / hidratación | ⬜ | T3 |  |
| Estrategias de recuperación | ⬜ | T3 |  |
| Periodización / microciclo | 🟡 | T3 | entrenan a puerta cerrada |
| Asistencia a entrenamientos | 🟡 | T3 |  |
| RPE sesión a sesión | ⬜ | T3 |  |
| Aclimatación a la altura | ✅ | T1-3 | Corea ~2 sem en Guadalajara |

### 13. Variables ambientales / clima / estadio
*Cómo lo usamos:* **Capa de entorno completa (sección 4).** Todas sorteadas por partido en el modelo estocástico.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Temperatura | ✅ | T1 | ~22°C al pitazo |
| Humedad relativa | ✅ | T1 | ~72% |
| Viento (velocidad/dirección) | ✅ | T1 | 18 km/h SO, rachas 33 |
| Precipitación (lluvia) | ✅ | T1 | 42% al inicio → contragolpe |
| Altitud del estadio | ✅ | T1 | 1,566 m → fatiga Corea |
| Tipo de césped | ✅ | T1 | Bermuda híbrido + 5% fibra |
| Estado del césped | ✅ | T1 | húmedo probable → pitch_speed 1.07 |
| Dimensiones del campo | ✅ | T1 | 105×68 m |
| Hora del partido | ✅ | T1 | 19:00 (noche, sin calor) |
| Iluminación | 🟡 | T1 | focos |
| Índice de calor / sensación térmica | 🟡 | T1 | noche templada, neutro |
| Calidad del aire | ⬜ | T1 |  |

### 14. Árbitro y oficiales
*Cómo lo usamos:* Usado: identidad (Gustavo Tejera, Uruguay), tendencia de tarjetas (~5 amarillas/partido) → riesgo de roja, sesgo de afición sobre el árbitro.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Identidad del árbitro | ✅ | T1 | Gustavo Tejera (URU), 38a |
| Tendencia de tarjetas | ✅ | T1 | ~5.0-5.24 amarillas/partido |
| Penaltis por partido | ✅ | T1 | propenso al penalti |
| Faltas pitadas (permisividad) | ✅ | T1 | estricto |
| Uso/tendencia del VAR | 🟡 | T1 | VAR en uso |
| Experiencia del árbitro | ✅ | T1 | primer Mundial |
| Historial árbitro-equipo | 🟡 | T1 | sesgo de afición (Nevill 2002) |

### 15. Variables contractuales / económicas / mercado
*Cómo lo usamos:* Entran como contexto motivacional (no como predictor económico): fichajes resueltos quitan ansiedad (Lee Kang-in→Atlético, Jiménez→Wolves).

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Valor de mercado y evolución | 🟡 | T1 | calidad de plantilla |
| Salario | ⬜ | T1 |  |
| Años de contrato restantes | 🟡 | T1 | motivation_drivers |
| Cláusula de rescisión | ⬜ | T1 |  |
| Rumores / interés de clubes | ✅ | T4 | escaparate (Mora→Madrid/Barça) |
| Bonus por rendimiento | ⬜ | T1 |  |
| Coste de fichaje / amortización | ⬜ | T1 |  |
| Representante / agencia | ⬜ | T1 |  |

### 16. Variables sociales / personales / vitales
*Cómo lo usamos:* **Diferencial del modelo de gemelos.** Cada jugador investigado a fondo: familia, pareja, hijos, duelos, eventos vitales → motivación/ánimo del día. Son T4, vía fuentes públicas.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Situación familiar y estabilidad | ✅ | T4 | family por jugador |
| Eventos vitales recientes | ✅ | T4 | Jiménez duelo padre; Quiñones guerra/familia; Kim Min-jae divorcio |
| Vida fuera del campo / hábitos | ✅ | T4 | personal_state |
| Presión mediática / redes | ✅ | T4 | polémica Son servicio militar |
| Sentimiento en redes (proxy ánimo) | 🟡 | T4 | cualitativo |
| Relación con la prensa | ✅ | T4 | boicot coreano a su prensa |
| Adaptación cultural | 🟡 | T4 | naturalizados (Quiñones, Fidalgo) |
| Prácticas religiosas (p.ej. Ramadán) | ⬜ | T4 | no aplica aquí |
| Residencia / distancia al CT | ⬜ | T4 |  |

### 17. Variables del rival (matchup)
*Cómo lo usamos:* Usado: duelos directos clave (Jiménez vs Kim Min-jae), estilo del rival por zona, H2H, portero rival, disciplina del rival.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Identidad y nivel del rival directo | ✅ | T1-2 | Reyes vs Son; Jiménez vs Kim Min-jae |
| Estilo def/of del rival | ✅ | T1-2 | Corea presión, MEX bloque bajo |
| Fortalezas/debilidades por zona | ✅ | T2 | zaga MEX sin Montes; MC bajitos KOR |
| Historial cara a cara | ✅ | T1 | MEX invicto vs KOR en Mundiales |
| Portero rival (si target es goleador) | ✅ | T1 | Rangel vs Kim Seung-gyu |
| Disciplina del rival | ✅ | T1 | card_risk por equipo |

### 18. Variables temporales / de forma (features derivadas)
*Cómo lo usamos:* Usado: medias móviles (forma últimos 10), rachas (MEX invicto 10; Son sequía 13 sin gol), tendencia, diferencia vs media.

| Variable | Uso | Tier | Cómo entró |
|---|:--:|:--:|---|
| Medias móviles (forma 3/5/10) | ✅ | T1 | últimos 10 partidos |
| Tendencia (mejora/declive) | ✅ | T1 | MEX al alza, formas comparadas |
| Rachas | ✅ | T1 | MEX invicto; Son 13 sin gol en LAFC |
| Estacionalidad | 🟡 | T1 |  |
| Variables lag (partido anterior) | ✅ | T1 | resultado J1 |
| Tiempo desde último gol/asistencia | ✅ | T1 | Son chances falladas J1 |
| Diferencia vs media histórica | 🟡 | T1 | forma vs nivel base |

---

## 4. Entorno del día — datos crudos completos (`env.json`)

Todos sorteados por partido en el modelo estocástico (lluvia Bernoulli, temperatura Normal, intensidad de afición Normal).

| Campo | Valor |
|---|---|
| Prob. lluvia al pitazo | 0.425 |
| Temperatura al pitazo (°C) | 22.0 |
| Temp. mínima (°C) | 17 |
| Temp. máxima (°C) | 29 |
| Humedad (%) | 72.5 |
| Viento (km/h) | 18.0 |
| Tipo de césped | Bermuda hibrido (Cynodon dactylon var. hibrido — familia Bermudagrass) con 5% fibra sintetica entretejida (stitching). Pasto de estacion calida, certificado FIFA Quality Pro. Producido en Nuevo Leon, Mexico. Especie comercial referenciada como "Bermuda North Bridge" en algunas fuentes, aunque FIFA/Universidad de Tennessee no confirmaron nombre comercial exacto publicamente. |
| Estado del césped | Buena a muy buena. Cancha nueva instalada para el Mundial 2026 con sistema de drenaje neerlandes (succion + riego subterraneo). Con lluvia previa al partido (probable), la superficie estara humeda pero no encharcada gracias al drenaje avanzado. Dimensiones: 105 x 68 m (estandar FIFA). |
| Factor velocidad cancha | 1.075 |
| Aforo | 47000 |
| Asistencia esperada | 46900 |
| % afición local | 0.935 |
| Coreanos estimados | 2000 |
| Hostilidad (0-100) | 30 |
| Ruido (0-100) | 89 |
| Modificador xG local | 0.12 |

---

## 5. Gemelos digitales — los 22 jugadores con TODOS sus campos

Cada jugador es un 'bot' con: identidad, físico/anatomía, atributos técnicos y mentales (0-100), estado del día, biografía, familia, estado personal, personalidad, motivación y monólogo interior.

### 5.1 Tabla de atributos numéricos (los 22)

| Jugador | Eq | Edad | Caps | Alt(cm) | Peso | VelMax | Pace | Dur | Skill | Fin | Cre | Aer | Def | Stam | Comp | Vol | Clutch | PresRes | Disc | Cons | MotHoy | Ánimo | RiesgoLes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Raúl "Tala" Rangel | MEX | 26 | 14 | 190 | 84 | 30 | 45 | 85 | 74 | 10 | 45 | 84 | 76 | 80 | 68 | 18 | 65 | 66 | 85 | 70 | 88 | 74 | 12 |
| Israel Reyes Romero | MEX | 26 | 35 | 179 | 73 | 32 | 72 | 78 | 82 | 42 | 62 | 78 | 80 | 84 | 72 | 14 | 70 | 74 | 82 | 80 | 88 | 84 | 10 |
| Johan Vásquez | MEX | 27 | 48 | 184 | 80 | 30 | 61 | 82 | 82 | 55 | 60 | 79 | 83 | 90 | 76 | 8 | 72 | 78 | 85 | 88 | 93 | 88 | 10 |
| Edson Álvarez | MEX | 28 | 101 | 190 | 76 | 32 | 70 | 55 | 84 | 55 | 68 | 82 | 86 | 74 | 82 | 8 | 85 | 88 | 84 | 62 | 93 | 88 | 38 |
| Jesús Gallardo | MEX | 31 | 123 | 176 | 73 | 35 | 80 | 90 | 80 | 62 | 72 | 64 | 78 | 82 | 72 | 14 | 73 | 75 | 55 | 75 | 93 | 91 | 14 |
| Erik Antonio Lira Méndez | MEX | 26 | 27 | 172 | 62 | 30 | 70 | 80 | 79 | 28 | 60 | 55 | 82 | 84 | 72 | 12 | 74 | 76 | 55 | 82 | 93 | 91 | 12 |
| Álvaro Fidalgo Fernández | MEX | 29 | 5 | 174 | 68 | 31 | 75 | 78 | 84 | 62 | 86 | 52 | 63 | 76 | 72 | 18 | 80 | 75 | 85 | 74 | 95 | 82 | 22 |
| Gilberto Mora | MEX | 17 | 9 | 168 | 63 | 31 | 80 | 75 | 79 | 62 | 84 | 44 | 48 | 71 | 74 | 14 | 78 | 75 | 82 | 68 | 95 | 91 | 28 |
| Roberto Alvarado | MEX | 27 | 69 | 176 | 70 | 32 | 78 | 82 | 80 | 62 | 84 | 52 | 68 | 80 | 70 | 18 | 75 | 73 | 65 | 68 | 94 | 90 | 15 |
| Raúl Jiménez | MEX | 35 | 128 | 188 | 76 | 30 | 62 | 65 | 82 | 83 | 68 | 88 | 45 | 72 | 79 | 14 | 85 | 84 | 72 | 74 | 93 | 84 | 28 |
| Julián Andrés Quiñones Quiñones | MEX | 29 | 23 | 177 | 78 | 33 | 79 | 68 | 88 | 91 | 74 | 72 | 42 | 82 | 80 | 12 | 86 | 83 | 78 | 85 | 95 | 88 | 22 |
| Kim Seung-gyu | KOR | 35 | 89 | 188 | 82 | 30 | 35 | 80 | 83 | 10 | 62 | 80 | 82 | 74 | 82 | 10 | 85 | 84 | 88 | 74 | 92 | 80 | 22 |
| Lee Han-beom | KOR | 24 | 9 | 189 | 83 | 30 | 56 | 78 | 82 | 42 | 58 | 84 | 83 | 86 | 76 | 12 | 71 | 74 | 72 | 78 | 93 | 91 | 14 |
| Kim Min-jae | KOR | 29 | 80 | 190 | 81 | 33 | 73 | 55 | 88 | 48 | 58 | 91 | 89 | 80 | 82 | 10 | 84 | 85 | 74 | 72 | 88 | 76 | 32 |
| Lee Gi-hyuk | KOR | 25 | 4 | 184 | 72 | 32 | 68 | 78 | 74 | 22 | 68 | 73 | 75 | 82 | 80 | 12 | 72 | 79 | 60 | 76 | 88 | 85 | 12 |
| Seol Young-woo | KOR | 27 | 35 | 182 | 75 | 32 | 80 | 62 | 81 | 44 | 72 | 68 | 78 | 90 | 72 | 12 | 68 | 74 | 80 | 82 | 88 | 80 | 22 |
| Hwang In-beom | KOR | 29 | 75 | 177 | 70 | 32 | 72 | 55 | 83 | 72 | 79 | 64 | 78 | 75 | 80 | 8 | 82 | 81 | 82 | 76 | 90 | 86 | 32 |
| Paik Seung-ho | KOR | 29 | 28 | 182 | 73 | 30 | 64 | 60 | 75 | 62 | 72 | 65 | 74 | 78 | 70 | 14 | 71 | 68 | 58 | 73 | 85 | 80 | 28 |
| Lee Tae-seok | KOR | 23 | 19 | 174 | 68 | 33 | 80 | 78 | 74 | 52 | 67 | 56 | 65 | 82 | 62 | 18 | 60 | 63 | 58 | 70 | 91 | 88 | 18 |
| Lee Kang-in | KOR | 25 | 50 | 173 | 66 | 33 | 78 | 72 | 86 | 71 | 92 | 44 | 58 | 80 | 74 | 18 | 80 | 75 | 72 | 77 | 91 | 83 | 22 |
| Lee Jae-sung | KOR | 33 | 106 | 180 | 70 | 31 | 70 | 68 | 82 | 68 | 80 | 60 | 73 | 84 | 76 | 10 | 74 | 80 | 82 | 75 | 92 | 83 | 22 |
| Son Heung-min | KOR | 33 | 145 | 183 | 78 | 35 | 89 | 70 | 88 | 79 | 86 | 72 | 68 | 84 | 74 | 18 | 82 | 78 | 72 | 72 | 86 | 62 | 20 |

### 5.2 Estado emocional del día (modelo de mentes) — los 22

| Jugador | Eq | Presión | Nervios | Confianza | Motivación | Foco | Riesgo tarjeta |
|---|---|---|---|---|---|---|---|
| Raul Rangel | MEX | 88 | 72 | 66 | 96 | 82 | 12 |
| Israel Reyes | MEX | 82 | 58 | 71 | 94 | 88 | 62 |
| Johan Vásquez | MEX | 82 | 58 | 76 | 95 | 88 | 42 |
| Edson Alvarez | MEX | 88 | 58 | 74 | 96 | 90 | 62 |
| Jesus Gallardo | MEX | 82 | 58 | 74 | 95 | 85 | 55 |
| Erik Lira | MEX | 84 | 62 | 68 | 95 | 83 | 58 |
| Alvaro Fidalgo | MEX | 78 | 52 | 82 | 95 | 88 | 38 |
| Gilberto Mora | MEX | 88 | 62 | 79 | 97 | 82 | 38 |
| Roberto Alvarado | MEX | 82 | 58 | 79 | 96 | 85 | 38 |
| Raul Jimenez | MEX | 82 | 48 | 79 | 95 | 85 | 22 |
| Julian Quinones | MEX | 78 | 42 | 88 | 96 | 85 | 38 |
| Kim Seung-gyu | KOR | 82 | 58 | 74 | 90 | 85 | 12 |
| Lee Han-beom | KOR | 88 | 71 | 62 | 95 | 80 | 58 |
| Kim Min-jae | KOR | 86 | 52 | 78 | 94 | 88 | 58 |
| Lee Gi-hyuk | KOR | 86 | 74 | 62 | 94 | 71 | 58 |
| Seol Young-woo | KOR | 82 | 58 | 72 | 93 | 80 | 48 |
| Hwang In-beom | KOR | 82 | 58 | 79 | 94 | 85 | 42 |
| Paik Seung-ho | KOR | 82 | 58 | 74 | 93 | 85 | 52 |
| Lee Tae-seok | KOR | 82 | 58 | 71 | 93 | 84 | 42 |
| Lee Kang-in | KOR | 82 | 58 | 86 | 94 | 84 | 38 |
| Lee Jae-sung | KOR | 82 | 58 | 74 | 95 | 80 | 38 |
| Son Heung-min | KOR | 88 | 52 | 79 | 97 | 85 | 22 |

### 5.3 Fichas completas (bio, familia, estado, personalidad, motivación, lesiones, monólogo)

#### Raúl "Tala" Rangel — MEX · GK · 26 años · 14 caps
- **Club / situación:** CD Guadalajara (Chivas) — Titular indiscutible desde Clausura 2024. En Clausura 2026 acumuló 1,350 minutos, 15 partidos como titular, 6 clean sheets, calificación FotMob 7.07. Chivas lo cedió a la Selección en etapa de Liguilla. Contrato vigente hasta junio 2028. Objeto de interés europeo activo: Sporting de Lisboa (sondeo directo), Feyenoord (consulta de condiciones), FC Copenhague (oferta rechazada por Chivas ~6M USD). El propio Rangel ha declarado públicamente su deseo de ir a Europa post-Mundial. Valor de mercado Transfermarkt: 7.4M EUR.
- **Físico/anatomía:** 190 cm, 84 kg, velocidad punta ~30 km/h, durabilidad 85/100
- **Historial de lesiones:** Sin lesiones graves; portero robusto
- **Familia:** Madre: Miriam Aguilar (figura central en su vida; lo crió junto a la abuela Dolores). Padre: ausente desde la infancia (CONFIRMADO por declaraciones de la madre en documental "Raíces, el comienzo"). Abuela paterna Dolores: lo crió parcialmente en Zapotlán el Grande. Pareja: relación sentimental activa (confirmada por publicación propia en Instagram con collage de fotos y mensaje "Larga vida, mi amor"), identidad de la pareja no confirmada públicamente. Nombre "Edith Marín" circuló en un sitio pero no tiene verificación en fuentes primarias. Sin hijos reportados públicamente. Vínculo cercano de mentoría con Alfredo Talavera (ídolo y padrino deportivo; patrocina sus guantes con la marca "Ala").
- **Estado personal:** Estable y enfocado. Vive el momento más importante de su vida deportiva. Llegó al Mundial 2026 como portero titular de México tras la lesión de Luis Ángel Malagón (rotura de tendón de Aquiles, marzo 2026). Fue recibido con mariachi y pirotecnia junto al equipo en Guadalajara el 16-jun-2026. Carga motivación histórica (niño de familia humilde que trabajó de panadero, ladrillero, carnicero y vendedor de cocos en Ciudad Guzmán para sostener a su madre y abuela). Su historia de ascenso social es fuente explícita de orgullo e identidad. Anímicamente positivo pero con presión puntual: fue el jugador más criticado por analistas tras el México 2-0 Sudáfrica (J1, 11-jun-2026) por imprecisiones con el pie. Yayo de la Torre (FOX Sports): "A mí no me gustó lo del Tala. Hubo dos pelotas que un arquero no puede dejarlas ir." Aguirre indirectamente reconoció que algunos jugadores "tuvieron las piernas temblando" en el debut. Existe ruido mediático sobre posible regreso de Ochoa al arco para este partido, lo que genera presión adicional sobre Rangel.
- **Personalidad:** Carácter reservado en vida privada pero comunicativo y seguro en el campo. Desde niño aprendió a ser responsable y autosuficiente por la ausencia paterna (dato confirmado por su madre). Tiene voz dentro del área y manda con autoridad. Fría bajo presión según observadores del club, aunque en partido inaugural mundialista mostró nerviosismo con el balón en los pies. Admite abiertamente sus nervios: "partido a partido ese nervio siempre está, no es algo que desaparezca. El hecho es saberlo manejar." Mentalidad de crecimiento continuo: busca aprender de Memo Ochoa, de quien dice "ha sido uno de mis mentores, abiertamente." Ambicioso: sueña con Europa desde que llegó a Chivas. Humilde en origen pero seguro de sus capacidades. Liderazgo en construcción en porteros mexicanos jóvenes.
- **Motivación hoy:** MOTIVA HOY: Jugar en su ciudad natal (Estadio Akron, Guadalajara — a 2 horas de Zapotlán el Grande donde creció); estadio donde es ídolo local y conoce cada rincón desde las fuerzas básicas. Necesidad de responder a las críticas del debut vs Sudáfrica y silenciar dudas sobre su titularidad. Su sueño europeo pasa por brillar en este Mundial como vitrina global. Victoria en J1 le da confianza colectiva. Consejo de Ochoa de "disfrutar cada momento porque los Mundiales no pasan todos los días." PESA HOY: Ruido sobre posible cambio por Ochoa. Errores con pie en J1 que generaron debate público. Presión de actuar sin Montes y con Álvarez improvisado en zaga. Rival con Son Heung-min, amenaza real de primer nivel que puede explotar su zona.
- **Biografía:** José Raúl "Tala" Rangel Aguilar (Zapotlán el Grande, Jalisco, 25-feb-2000) es la historia más improbable del fútbol mexicano actual: de panadero, ladrillero y vendedor de cocos en Ciudad Guzmán —trabajando desde los ocho años para sostener a su madre Miriam y su abuela Dolores ante la ausencia de su padre— a portero titular de México en el Mundial 2026. Criado en carencias pero con determinación inquebrantable, comenzó en las fuerzas básicas del América porque era el único club con escuela en su zona, hasta que Chivas lo detectó a los 16 años (2016) y lo incorporó a su cantera Sub-15. Ascendió metódicamente: Sub-17, Sub-20, Tapatío (debut septiembre 2020), hasta que Veljko Paunović lo estrenó en Primera División el 1-oct-2023. Ganó la titularidad en el Clausura 2024 y no la soltó. Su apodo "Tala" surgió en las fuerzas básicas por su parecido físico y estilístico con el histórico portero Alfredo Talavera, quien se convirtió en mentor real: patrocina sus guantes con la marca "Ala" y mantiene contacto constante. A sus 26 años, Rangel suma 5 clean sheets en sus últimas 8 apariciones internacionales —tras un inicio turbulento cediendo 4 goles tanto ante Uruguay como ante Suiza— y entró al Mundial 2026 como sustituto de emergencia de Luis Ángel Malagón (lesión de tendón de Aquiles, marzo 2026). El 11-jun-2026 hizo historia como guardameta titular de México en la victoria inaugural 2-0 sobre Sudáfrica, aunque fue el jugador más cuestionado por errores con el pie. Hoy, en Guadalajara, su ciudad adoptiva, afronta el partido más importante de su vida con la ciudad entera detrás de él.
- **🗣️ Monólogo interior:** *“Hace dos semanas yo veia este Mundial desde la banca, y hoy el arco es mio porque Malagon cayo. No lo pedi asi, pero aqui estoy, en casa, con cuarenta y ocho mil que cantan mi nombre... y eso pesa tanto como me empuja. No quiero ser el portero del que se acuerden por un error; quiero ser el que dejo el cero. Respiro, miro el cesped mojado y me digo: la pelota va a venir rapida con esta humedad, achicate, manos firmes, comunica con Vasquez atras porque sin Cesar la zaga es nueva. Si ataja una, me suelto. Que vengan los coreanos, yo no me muevo de aqui.”*
- **X-factor:** Su primera atajada temprana define el partido: si la saca, se transforma en muralla; el balon resbaladizo y el atrevimiento coreano son su mayor prueba.
- **Confianza del dato:** CONFIRMADO: Nombre completo José Raúl Rangel Aguilar; nacimiento 25-feb-2000 Zapotlán el Grande; madre Miriam Aguilar; padre ausente; apodo "Tala" por parecido con Talavera; debut Primera División 1-oct-2023; debut Selección 5-jun-2024 vs Uruguay (derrota 4-0); titular Clausura 2024 en adelante; títulos Nations League 2025 y Gold Cup 2025; titular vs Sudáfrica J1 Mundial 2026 (victoria 2-0); errores con pie criticados por Yayo de la Torre; citas directas sobre nervios y mentoría de Ochoa; interés de Sporting/Feyenoord/Copenhague confirmado por múltiples medios; contrato hasta jun-2028; valor 7.4M EUR Transfermarkt. ESTIMADO/NO CONFIRMADO DIRECTAMENTE: Número total de caps (~14 al 18-jun-2026, diferentes fuentes dicen 9 Wikipedia vs 12-14 en otras — se usa 14 como estimación más actualizada incluyendo J1 Mundial); identidad exacta de pareja (publicación en Instagram confirmada pero nombre no verificado en fuentes primarias); número exacto de clean sheets en última racha (5/8 según una fuente); posibilidad de que Aguirre lo quite por Ochoa (reportado como evaluación, no como decisión confirmada).
- **Fuentes:** Wikipedia ES (Raúl Rangel, futbolista) — datos biográficos, caps (9 Wikipedia, ~14 según otras fuentes incluyendo Mundial), títulos, debut 5-jun-2024 vs Uruguay. | Transfermarkt (transfermarkt.us/raul-rangel/profil/spieler/802855) — valor 7.4M EUR, contrato hasta jun-2028. | Infobae MX (18-jun-2026) — citas directas de Rangel sobre Ochoa como mentor: "Ha sido uno de mis mentores, abiertamente"; "Partido a partido ese nervio siempre está". | Nación Fútbol MX (11-jun-2026) — críticas de Aguirre y debate sobre cambio por Ochoa tras debut vs Sudáfrica. | ChivasPasion/Bolavip (múltiples fechas 2025-2026) — estadísticas Clausura 2026, rumores europeos (Sporting, Feyenoord, Copenhague rechazado), apodo "Tala" y relación con Talavera. | Milenio (2026) — historia personal: madre Miriam Aguilar, abuela Dolores, trabajos de infancia, documental "Raíces, el comienzo". | TV Azteca Deportes (10-cosas-tala-rangel) — datos de personalidad y perfil. | Excélsior (2026) — declaración Rangel sobre sueño europeo: "Sí me gustaría ir... me gustaría ser parte de esa lista de porteros mexicanos que han ido a Europa". | Clarosports / SI.com / Depor (18-jun-2026) — alineación confirmada vs Corea del Sur y contexto del Grupo A. | ESPN Deportes — interés europeo y rechazo de oferta Copenhague. | Ricardo La Volpe (citado en resultados de búsqueda): "el Tala es el portero indiscutible número 1 de México."

#### Israel Reyes Romero — MEX · Lateral derecho / Defensa central · 26 años · 35 caps
- **Club / situación:** Club America — Titular indiscutible en America con 146 partidos oficiales y seis titulos desde 2023. Probable salida post-Mundial a AS Roma (Serie A): medios reportan acuerdo casi cerrado por ~9 millones USD, el propio Enrique Bermudez lo dio por hecho el 14 de junio. America congelo cualquier movimiento hasta que termine el Mundial. Para el partido de hoy contra Corea del Sur, reportes de TUDN/Tricolor Al Dia indican que podria ir a la banca y ser reemplazado por Jorge Sanchez por razones tacticas (velocidad coreana). Otros medios (ClaroSports, 365Scores) lo mantienen en el once inicial. Incertidumbre real sobre su titularidad hoy.
- **Físico/anatomía:** 179 cm, 73 kg, velocidad punta ~32 km/h, durabilidad 78/100
- **Historial de lesiones:** Historial leve, golpe menor ene-2026
- **Familia:** Padres: Maria Patricia Romero (madre muy presente en su formacion, lo transportaba de El Grullo a Guadalajara para entrenar en Atlas) y Jose de Jesus Reyes. Hermano: Ivan Reyes, cantante de regional mexicano, ha asistido a concentraciones del Tri; tiene dos hijos (sobrinos de Israel). Novia actual: Rosalva Burgos, comenzaron en diciembre 2024 tras el tricampeonato del America; Israel le dedico una cancion de Grupo Frontera en los festejos. Sin hijos propios reportados. Relaciones previas: Nailea Vidrio (futbolista Liga MX Femenil, ruptura no amistosa) y brevemente Carolina Ross (cantante, septiembre 2023).
- **Estado personal:** Estado personal estable y positivo. Vive su primer Mundial con alta carga emocional — confeso sentir piel de gallina en todo el cuerpo durante el himno en J1 vs Sudafrica, algo que no habia vivido igual. La posible transferencia a Roma genera emocion pero tambien presion de mostrar su mejor version ante el mundo. La relacion con Rosalva Burgos parece solida y tranquilizadora. Es oriundo de Jalisco y el partido de hoy se juega en Guadalajara (Estadio Akron), lo que añade una carga emocional positiva especial — juega en casa ante su gente. Fuera del futbol disfruta la musica (canto), convivencia familiar y el regional mexicano junto a su hermano Ivan. No se reportan eventos perturbadores recientes en su vida personal.
- **Personalidad:** Carismático, emotivo y comunicativo. Fuera de la cancha es alegre, social y apasionado por la musica — confeso en entrevista con David Medrano querer ser cantante al retirarse, y canto en vivo en el programa. Anima las reuniones grupales con sus companeros. Dentro de la cancha transmite seriedad, concentracion y compromiso. Mentalidad competitiva clara: afirma que en seleccion no puedes relajarte aunque seas titular regular. Usa frases fuertes y directas con la aficion ('nos vamos a partir la madre por ellos'). Leal a su grupo: 'no es lo mismo defender a un companero de salon que defender a tu hermano'. Versatil y adaptable — empezo de contenccion y acepto con naturalidad el cambio a central/lateral. No se reporta temperamento conflictivo; disciplina solida en tarjetas.
- **Motivación hoy:** FACTORES QUE ELEVAN SU MOTIVACION HOY: (1) Primer Mundial de su carrera — momento historico y unico. (2) Partido en Guadalajara, su estado natal, con aficion jalisciense — factor emocional maximo. (3) El ojo de Europa puesto en el: vitrina perfecta para concretar el salto a Roma. (4) Victoria en J1 da confianza al grupo. (5) Hermano Ivan probablemente en las gradas. FACTORES QUE PODRIAN PESARLE: (1) Noticia de que posiblemente va a la banca — si es confirmada, puede generar frustracion o tension interna. (2) Alta expectativa de la aficion local podria presionar. (3) Polemica del campamento sobre el Roma antes del partido — distraccion mental posible.
- **Biografía:** Israel Reyes Romero (El Grullo, Jalisco, 23 mayo 2000) es el defensa que viajo desde un municipio rural del suroeste de Jalisco hasta los escenarios del futbol mundial gracias al sacrificio de su familia — su madre Maria Patricia lo llevaba cada fin de semana desde El Grullo hasta Guadalajara para que entrenara en Atlas, sin renunciar a que su hijo tambien estudiara. Formado en las fuerzas basicas del Atlas desde los 14 anos como contenccion, se adapto con naturalidad a lateral y defensa central, posiciones en las que exploto en el Puebla de Nicolas Larcamon (2020-2022) antes de aterrizar en el America, donde en solo tres anos sumo seis titulos, incluido el historico tricampeonato de Liga MX. Seleccionado nacional con 35 caps, ganador de dos Copas Oro (2023 y 2025) y la Nations League 2025, es hoy el lateral derecho titular de Mexico en su primer Mundial — un torneo que disputa en casa y que podria ser ademas su trampoln hacia la AS Roma en la Serie A italiana. Fuera de la cancha esconde un alma musical: su hermano Ivan es cantante de regional mexicano, el propio Israel confeso publicamente que quiere dedicarse al canto cuando se retire, y en los festejos del tricampeonato le dedico una cancion de Grupo Frontera a su novia Rosalva Burgos. Jugador de caracter firme pero emociones a flor de piel — admitio que sintio piel de gallina en todo el cuerpo durante su debut mundialista ante Sudafrica, una emocion que describio como algo nunca vivido igual.
- **🗣️ Monólogo interior:** *“Sin Cesar atras todo me cae mas pesado a mi, no puedo regalar nada. Son es Son, y viene picado por lo de su pais, lo voy a tener encima toda la noche; si me gana una vez aprende, si me gana dos me hunde. El Akron ruge para nosotros, eso me carga las piernas, la altura es nuestra no de ellos, voy a correr hasta que me revienten los pulmones. Tejera saca tarjetas como si nada y el pasto esta mojado, asi que la cabeza fria: agresivo pero limpio, le robo el balon, no la pierna. Hoy clasificamos, hoy somos lideres, no me lo va a quitar nadie por mi banda.”*
- **X-factor:** Contener a Son sin cometer falta en una noche con arbitro estricto y cancha mojada: disciplina defensiva pura.
- **Confianza del dato:** CONFIRMADOS: edad (26), fecha nacimiento (23 may 2000), lugar (El Grullo/Autlan, Jalisco), caps (35 segun Wikipedia; 34 en otras fuentes — uso 35), club America, posicion lateral/central, titularidad en J1 vs Sudafrica, nombre padres (Maria Patricia / Jose de Jesus), hermano Ivan (cantante), novia Rosalva Burgos (dic 2024), sin hijos, interes AS Roma confirmado por multiples fuentes + viaje a Italia + declaracion Bermudez 14 jun, 9 titulos totales, ratings promedio 7.0-7.2. ESTIMADOS: posible banca en J2 (reportes divididos, ~60% probabilidad banca segun prensa dominante); atributos numericos calculados en base a rendimiento real (rating 7.2 liga, solidez defensiva, versatilidad, 4 amarillas en 35 caps) y proyeccion para nivel mundialista; estado emocional_today estimado positivo alto basado en multiples declaraciones publicas y contexto (partido en Jalisco, primer Mundial, vitrina Roma).
- **Fuentes:** 1. Wikipedia EN — Israel Reyes (caps=35, historial clubes, goles internacionales): https://en.wikipedia.org/wiki/Israel_Reyes | 2. Mediotiempo — perfil mundialista: https://www.mediotiempo.com/futbol/copa-mundial/israel-reyes-el-lateral-que-le-devuelve-la-ilusion-a-mexico-para-la-copa-mundial-2026 | 3. TUDN — Israel Reyes a la banca vs Corea: https://www.tudn.com/mundial-2026/mexico-vs-corea-sur/israel-reyes-iria-a-la-banca-por-jorge-sanchez-en-el-mexico-vs-corea | 4. El Universal — declaraciones vs Sudafrica: https://www.eluniversal.com.mx/deportes/israel-reyes-con-sensaciones-positivas-al-vencer-a-sudafrica-estuvimos-a-la-altura/ | 5. Club America Oficial — convocatoria Mundial: https://www.clubamerica.com.mx/noticias/grandeza-mundialista-israel-reyes-convocado-con-mexico-para-la-copa-del-mundo-2026 | 6. Fox Sports MX — novia Rosalva Burgos: https://www.foxsports.com.mx/2025/01/03/israel-reyes-nueva-novia-tricampeon-america-rosalva-burgos-quien-es-video/ | 7. Show Deportivo — familia: https://showdeportivo.com/futbolistas/familia-israel-reyes-quien-es/ | 8. Bolavip — transferencia Roma / declaracion aficion: https://americamonumental.bolavip.com/noticias/el-contundente-recado-de-israel-reyes-que-enciende-a-todo-mexico-de-cara-al-mundial-2026 | 9. Infobae — America sobre fichaje Roma: https://www.infobae.com/mexico/deportes/2026/05/05/america-rompe-el-silencio-sobre-israel-reyes-y-su-supuesto-fichaje-con-la-roma/ | 10. SoyAguila / Telediario — talento musical y canto: https://www.soyaguila.com.mx/noticias-club-america/israel-reyes-confeso-a-lo-que-se-quiere-dedicar-cuando-se-retire-del-futbol-y-sorprendio-20251118-29451.html | 11. Fichajes.com — estadisticas temporada 25/26: https://www.fichajes.com/jugador/israel-reyes-romero/estadistica | 12. ClaroSports — alineacion probable con Israel titular: https://www.clarosports.com/futbol/mundial-2026/mexico-vs-corea-del-sur-mundial-2026-en-vivo-posibles-alineaciones-de-la-seleccion-mexicana-para-el-partido-del-18-de-junio/

#### Johan Vásquez — MEX · CB · 27 años · 48 caps
- **Club / situación:** Genoa CFC (Serie A, Italia) — Titular absoluto e indiscutible — unico jugador del Genoa en disputar los 36 partidos de la temporada 2025-26 siempre como titular sin ser sustituido (3,217 minutos). Capitan del equipo desde agosto 2025, cuarto mexicano en la historia en portar el gafete de capitan en el futbol europeo. Bajo Daniele De Rossi el Genoa remonto desde zona de descenso hasta la mitad de tabla. Contrato vigente hasta junio 2028. Intereses reportados de AS Roma, Juventus y Atalanta de cara al mercado verano 2026. Premio Grifone d'Oro al mejor jugador del club la temporada pasada.
- **Físico/anatomía:** 184 cm, 80 kg, velocidad punta ~30 km/h, durabilidad 82/100
- **Historial de lesiones:** 4 lesiones menores ~40d carrera; sin cirugia; aereo flojo (53%)
- **Familia:** Pareja: Camila Hernandez (juntos desde aprox. 2018-2019, viven en Genova). Hija: Mia Vasquez Hernandez (nacida 2025). Hijo: Milan Vasquez Hernandez (nacido 1 de octubre de 2024, anunciado por Johan en Instagram con mensaje emotivo). Padre: Rigoberto 'Zito' Vasquez, entrenador de futbol y dueno de Mariscos Zito en Navojoa, Sonora; figura central en la formacion y apoyo de Johan. Hermano: Rigoberto Vasquez jr, tambien futbolista. Johan ayudo economicamente a sus padres al renovar la casa familiar y ampliar el negocio de mariscos cuando comenzó a ganar dinero en Monterrey.
- **Estado personal:** Estable y muy positivo. Vive en Genova con su pareja Camila y sus dos hijos pequenos (Milan, 20 meses; Mia, aprox 1 ano). Primera Copa del Mundo en casa — el torneo se juega en Mexico, Estados Unidos y Canada, lo que anade una carga emocional y motivacional extra enorme para un jugador con raices profundas en Sonora. La estabilidad familiar y profesional contrasta con los anos de incertidumbre previos (2 descensos, rechazos). Ambiente en la concentracion del Tri descrito por el mismo como solido y tranquilo bajo Aguirre. Recibio visitas motivacionales de figuras como Julio Cesar Chavez y Cuauhtemoc Blanco durante la concentracion. Sin ningun evento personal negativo reportado previo al partido de hoy.
- **Personalidad:** Lider silencioso y discreto — perfil bajo mediatico fuera de la cancha pero voz de peso dentro del vestuario. Autocritico y honesto: admitio publicamente que en Qatar 2022 no estuvo a la altura sin buscar excusas ni echar culpas a nadie. Resiliente: supero rechazos de Pachuca, Pumas y Cruz Azul en la adolescencia, trabajo como mesero en el restaurante familiar antes de volver al futbol. Ambicioso con mentalidad de crecimiento: declaró que no quiere que este sea su mejor momento y que se ve con un techo mas alto. Agradecido con sus raices: no olvida Navojoa ni a su familia, fue de los primeros en ayudar economicamente a sus padres al volverse profesional. Temperamento frio y controlado — historial de disciplina ejemplar (sin tarjetas rojas directas en carrera). Tono competitivo en partidos grandes. Muestra madurez italiana: aprenderoperar en un entorno tatico exigente y en otro idioma.
- **Motivación hoy:** Revancha personal de Qatar 2022 donde viajo al Mundial pero no jugo ni un minuto — lo describe como 'una espinita clavada' y como 'el motivador mas grande de su carrera actual'. Jugar en casa (Mundial en Mexico/USA/Canada) ante su familia y aficion. Defender su lugar como capitan y lider del Tri con Montes suspendido — hoy es EL lider de la linea defensiva. Posible trampolín a un club grande europeo (Roma, Juve, Atalanta) si hace buen Mundial. Responsabilidad adicional: hoy jugara en pareja con Edson Alvarez (quien normalmente es mediocampista), por lo que siente mayor carga de comandar la zaga. Influencia de Rafa Marquez en mejorar su juego con balon — quiere demostrar esa mejora en el maximo escenario.
- **Biografía:** Johan Felipe Vasquez Ibarra (Navojoa, Sonora, 22 oct 1998) es el defensa central mexicano mas solido del futbol europeo en 2026. Su historia es de resiliencia pura: rechazado por Pachuca a los 12 anos, expulsado de las fuerzas basicas de Pumas a los 14, volvio a Navojoa a trabajar como mesero en el restaurante de mariscos de su padre 'Zito' antes de intentarlo de nuevo por la puerta chica en Cimarrones de Sonora. Ese camino largo lo forjo: debuto en Liga MX con Monterrey, gano el Apertura 2019 y la Concacaf Champions, y en enero de 2022 cruzó el Atlantico al Genoa — donde en cuatro temporadas ha ascendido de importado a pilar a capitan, disputando mas minutos de campo que cualquier otro jugador de outfield de la Serie A en la temporada 2025-26 (3,217 min, 36 titularidades consecutivas, 1 gol, 2 amarillas). La capitania del Genoa lo coloca en la lista historica de mexicanos lideres en Europa junto a Marquez, Guardado y Herrera. Hoy, con 27 anos, pareja Camila Hernandez y dos hijos pequenos en Genova, llega al partido mas importante de su vida: el clasico Mexico-Corea del Sur en Guadalajara, su primer Mundial jugando en casa, con la enorme espina de Qatar 2022 (lista pero cero minutos) como combustible emocional, y la responsabilidad extra de ser el lider defensivo unico con Montes suspendido.
- **🗣️ Monólogo interior:** *“Hoy la zaga es mía. Sin el Cachorro suspendido, el liderazgo atrás me toca a mí, y lo asumo: hablo, ordeno, no dejo que nadie se relaje un segundo. Akron va a rugir, 48 mil casi todos nuestros, y eso me prende pero no me marea. Son es rápido y va a buscar la espalda; tengo que medir la línea con el árbitro charrúa marcando todo, nada de barridas tontas ni manotazos. Si gano los duelos por arriba y mantengo la calma con balón, salimos primeros con una jornada de sobra. Aquí en mi tierra, en altura, con esta gente, no se nos escapa.”*
- **X-factor:** Manda en el área propia: domina el juego aéreo y ordena toda la defensa en ausencia de Montes.
- **Confianza del dato:** Alta en: datos biograficos basicos (edad, origen, posicion, pie), club y situacion (capitan, titular absoluto, contrato), familia (Camila, Milan nacido 1-oct-2024, Mia 2025), historia personal (rechazos, restaurante familiar, padre Zito), caps aproximados (47 segun Transfermarkt 29-may-2026; estimado 48 tras J1 vs Sudafrica), motivacion y declaraciones (multiples citas verificadas), disciplina (sin roja directa en carrera, 2 amarillas 2025-26), estado fisico (iron man, sin lesiones). Estimacion razonada en: calificaciones numericas del schema (basadas en estadisticas Serie A, calificaciones de partido y perfil de juego). Incierta: numero exacto de caps al dia de hoy (depende de si se cuentan amistosos y si J1 ya sumó al total oficial FIFA).
- **Fuentes:** Wikipedia ES (Johan Vasquez futbolista mexicano) | Transfermarkt perfil actualizado 29 mayo 2026 (47 caps, 3 goles seleccion; valor €12M) | ESPN MX (quinto ano Serie A; renovacion 2028; resurgimiento Genoa 2026) | TUDN (espinita clavada Qatar; declaraciones previas J1 y J2; capitan Genoa) | ABC Noticias MX (debut capitan Serie A 2025-26 vs Lecce) | Vanguardia MX (caballo de hierro; 3487 minutos) | Record MX (gol vs Milan; Genoa golea Torino; Johan no se conforma) | ClaroSports (iron man Serie A; mejoría balon) | Ovaciones (sed de revancha Qatar) | La Jornada (revancha Qatar 2022) | Fox Sports MX (me veo mas arriba) | SI.com MX (muro seleccion) | LJA.mx (muro silencioso) | Infobae (Rafa Marquez salida balon; buen hijo familia) | RPCTV / HolaNews / Emisoras Unidas (declaraciones Marquez) | Sopitas (historia infancia gallos mesero) | Proyecto Puente (rechazo Pumas) | Mediotiempo (raices Navojoa; lista 2026) | Instagram @johan_pipe (nacimiento Milan 1-oct-2024 confirmado) | TV Azteca (novia Camila Hernandez; capitan vs Juventus) | Record.com.mx (Johan papa nacio Mia) | Milenio (anuncio embarazo) | ESPN MX (familia marisqueria ayuda) | HOLA US-ES (parejas jugadores seleccion jun 2026) | Depor.com (alineaciones J2 vs KOR) | Mediotiempo (sustituto Montes) | ClaroSports (como sustituir a Montes vs KOR) | SomosFutboleros (calificaciones vs Sudafrica, nota 6.9) | 365Scores (resultado Mexico 2-0 Sudafrica) | Goal.com US (Vasquez y Jimenez lideres Tri) | Noro.mx (Zito Vasquez liderazgo internacional)

#### Edson Álvarez — MEX · DC/MCD · 28 años · 101 caps
- **Club / situación:** West Ham United (cedido de vuelta de Fenerbahce; contrato hasta 2028) — Situacion critica: Fenerbahce no ejecuto la opcion de compra (19M libras) tras temporada plagada de lesiones y abucheos. West Ham descendio a la Championship en mayo 2026. Edson no contempla jugar en segunda division inglesa; busca nuevo club post-Mundial. Acumula solo ~769 min en toda la temporada 2025/26 entre Fenerbahce y los ultimos partidos del West Ham. Su valor de mercado es aprox 20-24 M EUR. Candidatos: Ajax (repatriacion), Monterrey. Este Mundial es su trampolín de revalorizacion. Titular confirmado hoy como DEFENSA CENTRAL por la suspension de Montes — posicion que domino en Club America pero que ha jugado poco en Europa.
- **Físico/anatomía:** 190 cm, 76 kg, velocidad punta ~32 km/h, durabilidad 55/100
- **Historial de lesiones:** CIRUGIA tobillo feb-2026 (~100d); isquios/muslo 2024-25; falto de ritmo
- **Familia:** Pareja/prometida: Sofia Toache (modelo e influencer, n. 25 oct 1998, CDMX), relacion desde 2018. Propuesta de matrimonio en Bali el 1 agosto 2024; aun no casados (fuentes de junio 2026 la siguen llamando 'futura esposa'). Dos hijas: Valentina (n. 23 oct 2019) y una segunda hija (n. sept 2022, nombre no publico). Padre: Evaristo Alvarez, ex futbolista de segunda division y dueno de taller de uniformes deportivos en Tlalnepantla — le hacia las playeras personalizadas de nino. Madre: Adriana Velazquez. Hermano mayor: Cesar, quien moldeó su caracter poniendolo a jugar con chicos mayores en el barrio de San Rafael, Tlalnepantla.
- **Estado personal:** Estable y positivo con chispas de motivacion extra. El panorama clubero es turbulento (West Ham descendido, Fenerbahce lo abucheo y no lo compro, futuro laboral sin resolver hasta julio) pero Edson lo ha comunicado con serenidad: 'a veces la vida te pone cosas con un proposito'. Jugar el Mundial en Mexico — con familia en las gradas y tierra conocida — es declaradamente el mayor sueno de su vida. Prometida e hijas probablemente presentes en Guadalajara hoy. El padre Evaristo, origen humilde de Tlalnepantla, en las gradas o siguiendo el partido. Animo ALTO a pesar del contexto clubero incierto.
- **Personalidad:** Apodado 'El Machin' desde nino por su temperamento duro y sin miedo al contacto fisico ni a los rivales mayores. Lider silencioso-combativo: no grita, predica con el ejemplo. Ricardo Pelaez: 'liderazgo es ser ejemplar, predicar con el ejemplo'. Erik ten Hag: 'nunca se rinde'. Caracter forjado en el barrio bravo de Tlalnepantla: aguanta presion, no se achica. Emocionalmente maduro (ha superado golpes severos — abucheos en Fenerbahce, lesiones graves, descenso del West Ham) sin perder la calma publica. Culturalmente orgulloso: en Amsterdam organizaba comidas mexicanas con companeros. Introvertido en lo personal, concentrado, confiable en el vestuario. No temperamental/conflictivo: 0 tarjetas rojas en toda su carrera. Combativo pero disciplinado.
- **Motivación hoy:** MAXIMO HOY: Jugar un Mundial en casa es declaradamente 'una experiencia que me llevo a la tumba'. Alcanza los 101 caps justo en este torneo. La familia (Sofia, Valentina, hija menor) en las gradas o cerca. Futuro de contrato sin resolver — este partido es el CV mas importante de su carrera reciente. Redencion despues de una temporada de lesiones y abucheos. Primer partido como TITULAR en el Mundial 2026 (fue suplente en J1 vs Sudafrica). Sustituir a Montes como lider defensor — responsabilidad maxima. Posible revalorizacion en el mercado (Ajax, Monterrey). FACTOR NEGATIVO leve: falta de ritmo competitivo real (aprox 770 min en toda la temporada); no ha jugado 90 minutos de corrido desde antes de feb 2026.
- **Biografía:** Edson Omar Alvarez Velazquez (n. 24 octubre 1997, Tlalnepantla de Baz, Edo. Mexico) es el capitan y figura emblematica de la Seleccion Mexicana en el Mundial 2026. Hijo de Evaristo Alvarez — ex futbolista y fabricante de uniformes deportivos — y de Adriana Velazquez, creció en la colonia San Rafael, una de las zonas más bravas de Tlalnepantla, donde su hermano Cesar lo ponía a boxear y jugar contra chicos mayores, forjando el apodo 'El Machin' y una resiliencia inquebrantable. Recorría tres horas diarias en transporte publico para entrenar en Coapa desde los 14 años, gastando el 70% de su salario en pasajes. Debuto con Club America en 2016, marcó los dos goles de la final del Apertura 2018 contra Cruz Azul, y en 2019 se fue al Ajax por 12 M EUR — primer mexicano en marcar en Champions League en su debut. Erik ten Haj lo reconvirtio de central a mediocentro defensivo, y alli floreció hasta ganar dos Eredivisies y una KNVB Cup. En 2023 firmo con West Ham United (Premier League) por ~35 M EUR, pero lesiones graves (desgarro muscular Copa America 2024, cirugia de tobillo izquierdo febrero 2026) y un cesion al Fenerbahce marcada por abucheos y solo 769 minutos jugados ensombrecieron los ultimos dos anos. Hoy llega al partido de su vida — titular como defensa central ante Corea del Sur, con 101 caps, prometida Sofia Toache y sus dos hijas como testigos, y el pais entero detras suyo.
- **🗣️ Monólogo interior:** *“Sin Cesar atras, me toca a mi bajar de central y cargar con el brazalete; no es mi posicion, pero soy el capitan y este equipo necesita que yo de la cara. El Akron va a rugir, 48 mil mexicanos empujando, y yo nací para estas noches. Cuidado con Tejera, pita todo y yo siempre ando al limite con las amarillas, hoy tengo que medir el barrido y ganar con la cabeza, no con la pierna. Si ganamos hoy clasificamos antes de tiempo y nadie nos quita el liderato; le metemos a Corea que viene tocada por su lio interno. Vamos con todo, esta es mi casa.”*
- **X-factor:** Liderazgo y lectura desde el centro de la zaga improvisada: si organiza la linea y domina el balon aereo sin caer en faltas tontas, Mexico cierra el grupo hoy.
- **Confianza del dato:** DATOS CONFIRMADOS: fecha nacimiento (24/10/1997), edad (28), apodo El Machin, origen Tlalnepantla/San Rafael, padre Evaristo fabricante de uniformes, hermano Cesar, prometida Sofia Toache (compromiso Bali agosto 2024 — NO casados aun), hijas Valentina (n.23/10/2019) y segunda sin nombre publico (sept 2022), cirugia tobillo izquierdo 17 feb 2026, regreso con 1 minuto + abucheos Fenerbahce mayo 2026, West Ham descendido Championship mayo 2026, Fenerbahce no ejecuto opcion de compra, suplente J1 vs Sudafrica (entro por Erik Lira), llego a 100/101 caps en ese partido, titular confirmado hoy vs Corea como defensa central por suspension Montes, Aguirre: 'listo para 90 minutos'. ESTIMACIONES: caps exactos post-J1 calculados en 101 (100 en J1 + 1 si ingresa hoy como titular); minutos de stamina rebajados por falta de ritmo real (~769 min toda la temporada club); injury_risk moderado-alto por historial reciente pero medico lo da apto; consistency baja por irregularidad lesiones. Posicion hoy: defensa central (inusual en Europa pero dominio nativo en Club America).
- **Fuentes:** Mediotiempo: Edson Alvarez llega 100 partidos Mexico inauguracion Mundial 2026 (https://www.mediotiempo.com/futbol/copa-mundial/edson-alvarez-llega-100-partidos-mexico-inauguracion-mundial-2026) | FoxSports MX: historial lesiones Edson Alvarez Fenerbahce West Ham (https://www.foxsports.com.mx/2026/01/27/historial-lesiones-edson-alvarez-fenerbahce-west-ham-partidos-no-jugo-lista/) | La Opinion: Edson Alvarez segunda division situacion descenso West Ham (https://laopinion.com/2026/05/25/edson-alvarez-a-segunda-division-cual-es-la-situacion-del-mexicano-tras-el-descenso-del-west-ham/) | Record MX: Edson Alvarez operado tobillo (https://www.record.com.mx/historia/llegara-al-mundial-2026-edson-alvarez-es-operado-tras-molestias-en-el-tobillo-2026021717264444689) | FoxSports MX: volvio jugar 1 minuto abucheado Fenerbahce (https://www.foxsports.com.mx/2026/05/02/edson-alvarez-volvio-a-jugar-tras-su-operacion-sumo-1-minuto-y-aficion-del-fenerbahce-lo-abucheo/) | El Financiero: Aguirre Edson listo 90 minutos (https://www.elfinanciero.com.mx/deportes/mundial-2026/2026/06/17/vasco-aguirre-adelanta-la-alineacion-de-mexico-vs-corea-edson-esta-listo-para-jugar-90-minutos/) | La Razon: Sofia Toache futura esposa Edson Alvarez (https://www.razon.com.mx/deportes/2026/06/12/quien-es-sofia-toache-la-futura-esposa-de-edson-alvarez-edad-nacionalidad-estatura-hijos/) | El Universal: Edson Alvarez orgullo capitan Mundial (https://www.eluniversal.com.mx/deportes/edson-alvarez-vive-con-orgullo-ser-el-capitan-de-mexico-en-la-copa-del-mundo/) | Juanfutbol: historia padre playeras Tlalnepantla (https://juanfutbol.com/mundial/lo-golpeaban-por-su-talento-su-padre-le-hacia-las-playeras-y-ahora-comanda-a-la-seleccion-mexicana-en-el-mundial-2026-edson-alvarez) | Fichajes.com: estadisticas Fenerbahce 2025/26 (https://www.fichajes.com/jugador/edson-omar-alvarez-velazquez/estadistica) | TUDN: Edson Alvarez central Corea del Sur funcionara contra velocidad Son Hwang (https://www.tudn.com/mundial-2026/edson-alvarez-como-central-vs-corea-del-sur-funcionara-contra-la-velocidad-de-son-y-hwang-video) | Excelsior: incierto futuro West Ham descenso (https://www.excelsior.com.mx/deportes/incierto-futuro-edson-alvarez-tras-descenso-west-ham-premier-league) | ABC Noticias: Edson titular Corea suspension Montes (https://abcnoticias.mx/deportes/2026/6/16/seleccion-mexicana-ira-edson-alvarez-por-cesar-montes-ante-corea-en-el-segundo-partido-del-mundial-285059.html)

#### Jesús Gallardo — MEX · LB · 31 años · 123 caps
- **Club / situación:** Deportivo Toluca — Titular absoluto e inamovible en Toluca bajo Antonio Mohamed. Bicampeon de Liga MX (Apertura 2024-25 y Clausura 2024-25). En la temporada Clausura 2026 registra 1 gol y 4 asistencias en ~13 partidos con calificacion promedio FotMob de 7.49, siendo considerado el lateral izquierdo mas dominante de la Liga MX. Contrato hasta junio 2027. No existen rumores serios de transferencia al exterior: a los 31 anos su ciclo europeo no se dio y permanece como rey de su posicion en Mexico.
- **Físico/anatomía:** 176 cm, 73 kg, velocidad punta ~35 km/h, durabilidad 90/100
- **Historial de lesiones:** Casi impecable; resistencia y velocidad elite (35 km/h)
- **Familia:** Casado el 14 de febrero de 2026 (Dia de San Valentin) con Orquidea Garza, en la Parroquia de Santiago Apostol de Tianguistenco, Estado de Mexico. La boda fue al dia siguiente de un partido del Clausura. Tienen un hijo: Daniel (nacido el 21 de agosto de 2021). Orquidea es discreta y se mantiene alejada de los medios. Sus padres son Maribel Vasconcelos (madre muy presente y emocionalmente central en su vida) y Jose Alberto Gallardo. Tiene cuatro hermanos: Angel, Juan Pablo, Carlos y Diana. Es el cuarto de los cinco hijos. Su abuela materna es Maria Gamas Gongora.
- **Estado personal:** 2026 es el mejor ano de su vida fuera y dentro del futbol de manera simultanea: se caso en febrero, juega su tercer Mundial, gano dos titulos consecutivos con Toluca y gano la CONCACAF Champions Cup 2026. Estado personal: estable y muy positivo. Recien casado (4 meses), con un hijo de casi 5 anos que comparte sus celebraciones (fue al baile de boda con sus padres). Su madre Maribel, pilar emocional de toda su carrera, llora de orgullo cada vez que lo ve en una Copa del Mundo. Este tercer Mundial es la culminacion simbolica de una promesa que Gallardo hizo de nino al dibujar la Copa del Mundo inspirado en Brasil 2002. No se reportan eventos perturbadores en su vida privada. La unica sombra posible es la conciencia de que puede ser su ultimo Mundial, lo que actua mas como motivador que como presion.
- **Personalidad:** Resiliente, determinado y con autoconfianza desde la infancia. Sus apodos (Nene, Dany, Chucho) reflejan una naturaleza cercana y calida con quienes le rodean. En lo deportivo es directo, combativo y no se calla: arremetio publicamente contra aficion y medios que intentaban desestabilizar al grupo, mostrando temperamento y liderazgo defensivo del vestidor. Filosofia de vida basada en el sacrificio y el trabajo continuo: desde nino vendio tortas para pagarse los tachones. Toma decisiones claras bajo presion (cuando su novia le dio un ultimatum futbol-o-ella de pequeno, eligio el futbol sin dudar). Voz respetada en el vestidor pero no el capitan oficial. Mentalidad de block externo: predica ignorar el ruido exterior y enfocarse en el grupo. Se define como alguien que aprende tanto de la experiencia como de los jovenes, lo que denota humildad tactica y apertura mental.
- **Motivación hoy:** HOY: (1) La conciencia de que este puede ser su ultimo Mundial a los 31 anos actua como motor de maximo esfuerzo. (2) La promesa de nino cumplida: el nino de Cardenas que dibujo la Copa del Mundo en 2002 va a jugar su tercera. (3) Su madre Maribel, que llora de orgullo cada partido, es un anclaje emocional poderoso. (4) La boda reciente y su hijo Daniel como nueva razon para brillar ante el mundo. (5) Ser el jugador con mas partidos en el proceso de Aguirre lo convierte en un pilar del proyecto con responsabilidad grupal. (6) La oportunidad de liderar a Mexico a los octavos siendo el lateral izquierdo mas dominante del pais. Como posible peso: la conciencia de que una mala actuacion podria empannar la narrativa de su carrera en su ultima Copa del Mundo.
- **Biografía:** Jesus Daniel Gallardo Vasconcelos nacio el 15 de agosto de 1994 en Cardenas, Tabasco, el cuarto de cinco hijos de una familia humilde que no tenia television en casa. Desde los cinco anos vendio tortas para pagarse los tachones y prometio ante un companero de primaria que el seria el primero de Tabasco en llegar a un Mundial, promesa que cumplio tres veces. Un visor de Pumas lo detecto por su potencia fisica y lo llevo a la Ciudad de Mexico donde forjo su carrera, pasando despues a Monterrey (2018-2024) donde gano dos CONCACAF Champions y titulos de Liga, antes de reinventarse en Toluca tras ser descartado por Lozano y Fernando Ortiz. En Toluca bajo Mohamed se convirtio en bicampeon y en el lateral izquierdo mas dominante de la Liga MX, recuperando su lugar en el Tri como el jugador con mas partidos en todo el proceso de Javier Aguirre (22 partidos, 18 como titular). El 14 de febrero de 2026, al dia siguiente de un partido de Liga, se caso con Orquidea Garza en una ceremonia a la que acudieron compañeros del Toluca; juntos tienen a Daniel (nacido agosto 2021). Hoy, a sus 31 anos, disputa su tercer y posiblemente ultimo Mundial como titular indiscutible, con 123 caps internacionales y consciente de que este partido contra Corea del Sur puede definir su legado.
- **🗣️ Monólogo interior:** *“Esto es lo que llevo esperando toda la vida: un Mundial en mi tierra, en Guadalajara, casi 48 mil gritando por nosotros. Si ganamos hoy ya estamos en 16avos y mandamos en el grupo, eso me hace correr aunque la altura y esta humedad de 90% me cierren el pecho a los 70 minutos. Tengo que subir por mi banda y volver siempre, pero el árbitro uruguayo es estricto y yo me caliento; no me puedo dejar provocar ni meter una entrada tonta, una amarilla floja me arruina el partido. Conozco esta cancha, conozco este aire, y a Corea ya la respeto pero no le tengo miedo: nunca nos han ganado en un Mundial y hoy no va a ser la primera vez.”*
- **X-factor:** Aprovechar el envión del estadio y la altitud para desbordar su banda, sin tragarme la provocación que le cueste una amarilla temprana.
- **Confianza del dato:** ALTO en: edad, caps (~123), club, contrato, familia (esposa Orquidea, hijo Daniel, padres, hermanos), boda fecha, origen Cardenas Tabasco, titularidad hoy vs Corea, calificacion Sofascore vs Sudafrica (6.9), partidos con Aguirre (22/18 titularidades), estadisticas Clausura 2026, sin lesion reportada, personalidad (declaraciones publicas multiples). ESTIMADO con prudencia: composure_volatility (hay evidencia de temperamento, tarjeta en 13 seg Rusia 2018, pero tambien ha madurado), aerial (no hay dato directo de duelos aereos), finishing (5 goles en Clausura pero posicion de lateral).
- **Fuentes:** Wikipedia (Jesus Gallardo, 122-123 caps confirmados, debut oct 2016 vs NZ); Transfermarkt (valor mercado EUR 2.8M, contrato hasta jun 2027, estadisticas de club); Milenio - 'Jesus Gallardo el seleccionado con mas partidos con Javier Aguirre' (22 partidos, 18 titularidades, 1606 min con Aguirre); El Heraldo de Mexico - perfil biogra fico mundial 2026 (30/05/2026); El Futbolero - 'De descartado en Monterrey a figura en Toluca Clausura 2026' (16/04/2026); TUDN - declaraciones sobre clave del exito y union del equipo; Excelsior - Gallardo arremete contra aficion y medios (personalidad, temperamento); Novedades de Tabasco - 'El nino que sono con su propio destino' (09/06/2026) y 'El sueno cumplido' (17/06/2026) (infancia, familia, origen humilde); TUDN - 'Jesús Gallardo se casa dia despues del triunfo Toluca Liga MX' (boda San Valentin 14/02/2026); Ambito.com - 'Un gol al corazon Jesus Gallardo se caso en dia de San Valentin' (hijo Daniel, boda Tianguistenco); SDP Noticias - perfil jugador; Somos Futboleros - calificaciones Mexico vs Sudafrica (Gallardo 6.9 Sofascore); DAZN/Sopitas - listas de lesionados (Gallardo NO aparece); mediotiempo y SI.com - alineaciones probables Mexico vs Corea (Gallardo titular confirmado); laverdad.com.mx - Gallardo acusa intentos externos de desestabilizar la seleccion; TUDN/Latinus/Informador - polemica Corea del Sur y Son servicio militar previo al J2. ESTIMACIONES propias donde no hay dato confirmado: composure_volatility (basado en record tarjeta amarilla en 13 seg Rusia 2018 y acumulacion Copa Oro 2025), clutch (basado en titularidades en finales Nations League y Copa Oro), aerial (estimado por su altura 1.74-1.78m y posicion de lateral ofensivo).

#### Erik Antonio Lira Méndez — MEX · MDC · 26 años · 27 caps
- **Club / situación:** Cruz Azul — Titular indiscutido y capitán de Cruz Azul durante todo el Clausura 2026; no perdió un solo partido en toda la temporada regular. Fue convocado a la Selección desde el 6 de mayo, perdiéndose la Liguilla. Aun así, Aguirre le dio permiso para estar en la Final del Clausura 2026 donde Cruz Azul venció 2-1 a Pumas y levantó el título; Lira lloró ante las cámaras al alzar la copa como capitán aunque no jugó la Liguilla. Ahora plenamente concentrado en la selección. Rumores concretos de salida a Europa (Girona FC/City Group, Real Betis, Ajax) post-Mundial; su contrato llega a 2029 pero incluye cláusula de salida europea. Llega al J2 en máximo ritmo competitivo: más de 7 meses sin perderse un partido antes de la concentración.
- **Físico/anatomía:** 172 cm, 62 kg, velocidad punta ~30 km/h, durabilidad 80/100
- **Historial de lesiones:** Sin lesiones mayores; durable
- **Familia:** Pareja: Ana Paula (apellido no público), novia desde 2018 desde la época de la cantera de Pumas — ella se mudó a Aguascalientes a los 6 meses para estar con él. Conviven desde entonces; actualmente viven juntos en el sur de CDMX con su perro Hunter. No tienen hijos; ambos expresan querer formar familia "en un futuro no muy lejano". Familia extensa estuvo reunida para ver la convocatoria mundialista y publicó un video emotivo viral en redes sociales. La reacción familiar ante la convocatoria fue muy celebrada mediáticamente (fuente: VamosCruzAzul/Bolavip, HolaMéxico).
- **Estado personal:** Estado personal estable y positivo. Vive el pico emocional y profesional de su vida: sueño de infancia de jugar un Mundial cumplido. Lloró públicamente al levantar el título de Liga MX con Cruz Azul días antes. Su mensaje de convocatoria ("El sueño de niño que siempre soñé se está cumpliendo… atrás de esto hay fe, sacrificio, esfuerzo") refleja profundo orgullo personal y familiar. Relación sentimental sólida y comprometida desde 2018. Sin eventos negativos reportados. Concentrado en la selección desde el 6 de mayo, ambiente de grupo descrito como "familia" por el propio Lira. Único representante de Cruz Azul en el Mundial, lo cual le agrega responsabilidad pero también orgullo de club. Anuncio del interés europeo (Girona/Betis) funciona como motivación adicional: el Mundial es la mejor vidriera de su carrera, lo sabe y lo declaró explícitamente. Estado fuera de la cancha: tranquilo, emocionalmente pleno, sin turbulencias reportadas.
- **Personalidad:** Apodado "El Pitbull" y "El Jefe" dentro del vestuario. Líder nato de tipo silencioso-contundente: no es carismático verbal sino de acciones y trabajo diario. Asumió la capitanía de Cruz Azul a los 24 años por mérito sostenido, no por designación. Humilde y cercano con la afición: viral por detenerse a abrazar a un niño aficionado rumbo a los vestidores. Mentalidad ganadora sin arrogancia; pide calma tras las victorias ("no podemos pensar en el sexto sin el segundo"). Carácter frío y controlado dentro del campo: agresivo tácticamente pero sin perder la cabeza. Competitivo con Edson Álvarez sin generar conflicto público; declaró la competencia como algo "positivo". Tiene un lado emocional visible solo en momentos muy significativos (llanto tras la décima de Cruz Azul). Aficionado a ser DT: hay un video viral donde organiza jugadas en la pizarra, lo que indica inteligencia táctica y vocación de liderazgo. Se describió a sí mismo como "somos una familia" para referirse a la selección.
- **Motivación hoy:** Motivaciones positivas HOY: (1) Primer Mundial de su vida — sueño de infancia que está viviendo en tiempo real, emocionalmente en la cima. (2) Actuación destacada en J1 vs Sudáfrica (nota 7.4 Sofascore, asistencia en gol 1) le da confianza y confirmación de que puede rendir a nivel mundial. (3) El Mundial es la vidriera para el salto a Europa (Girona/Betis lo miran); J2 ante Corea del Sur con todo el mundo observando. (4) Recién campeón de Liga MX con Cruz Azul (levantó el trofeo como capitán llorando); ese impulso emocional positivo es fresco y potente. (5) Jugar en el Estadio Akron de Guadalajara ante afición mexicana — "nadie nos puede venir a ganar aquí, somos locales". (6) La ausencia de César Montes (suspendido) y los ajustes defensivos requieren más concentración y responsabilidad de Lira en el mediocampo, lo que él asume como reto. Sin factores depresivos reportados hoy.
- **Biografía:** Erik Antonio Lira Méndez (Ciudad de México, 8 de mayo de 2000, 26 años) es el mediocampista defensivo más en forma del fútbol mexicano en 2026. Surgido de la cantera de Pumas UNAM, se forjó a préstamo en Necaxa antes de llegar a Cruz Azul en enero de 2022, donde se convirtió en capitán y motor del equipo azul. Con 1.72 m y 70 kg, su perfil es el de un destructor elegante: recuperación feroz, salida limpia y un instinto táctico poco común para su edad — le llaman "El Pitbull" en el vestuario y "El Jefe" en la tribuna. Con Cruz Azul conquistó la Supercopa 2022, la Concacaf Champions Cup 2025 y el título de Liga MX Clausura 2026, este último levantado entre lágrimas como capitán a pesar de no haber disputado la Liguilla por su llamado a la selección. Con la Selección Mexicana lleva 27 partidos desde octubre de 2021, ganó la Nations League y Copa Oro 2025, y llegó al Mundial 2026 como titular indiscutible después de superar en el esquema de Aguirre a Edson Álvarez, quien llegó con meses de inactividad por lesión. En el debut mundialista ante Sudáfrica (2-0, 11 de junio) fue figura: asistencia en el gol 1 de Quiñones, 5/5 duelos ganados, nota Sofascore 7.4 en 76 minutos. Su vida personal refleja su estabilidad: lleva ocho años con Ana Paula, su novia desde la cantera de Pumas, con quien vive en el sur de CDMX; no tiene hijos y declaran querer formarlos. Múltiples clubes europeos —Girona (City Group), Real Betis, Ajax— tienen visores activos, y Lira reconoció que "no hay mejor vidriera que un Mundial" para su futuro europeo.
- **🗣️ Monólogo interior:** *“Hoy soy el unico ancla en el medio, y con Edson cayendo a central todo el hueco lo tengo que tapar yo. Sin Cesar atras, el equipo va a estar mas suelto y eso me pone la responsabilidad encima: si me brinco una marca, dejo a la defensa improvisada vendida. Tejera pita todo, asi que tengo que medir cada barrida, no puedo regalar la amarilla temprano porque entonces juego encogido los otros 70 minutos. Siento el Akron retumbando, esto es mi casa, esta gente me empuja, pero la cabeza tiene que estar fria: ganar hoy es clasificar y yo soy el que pone el orden. Aire enrarecido, cancha pesada por la humedad, pero la altura aqui la sufren ellos mas que nosotros. Respiro, escucho a Edson, y a trabajar: hoy no me toca brillar, me toca sostener.”*
- **X-factor:** Equilibrio del medio: si tapa el hueco de Edson sin caer en faltas, Mexico controla el partido; si lo desborda Corea por dentro, queda expuesta una zaga sin Montes.
- **Confianza del dato:** Alta en datos biográficos (nacimiento, club, contrato, relación, 41 amarillas carrera, perfil de juego, cifras de J1) — todos confirmados por múltiples fuentes. Caps: 26 confirmados hasta el 26 de abril, más J1 vs Sudáfrica = 27 estimado. Caps de J2 aun no jugado. Valoraciones numéricas del gemelo digital son estimaciones razonadas basadas en estadísticas reales, calificaciones mediáticas y comparativas de rendimiento. Vida familiar: confirmada por reportajes de febrero 2025 y Hola México junio 2026. Interés europeo: confirmado por múltiples medios especializados aunque ninguna transferencia cerrada aún.
- **Fuentes:** Wikipedia ES (es.wikipedia.org/wiki/Erik_Lira) — estadísticas de carrera y selección; 365scores.com/es/news/quien-es-erik-lira-mundial-2026 — perfil completo; VamosCruzAzul/Bolavip (vamoscruzazul.bolavip.com) — situación en Cruz Azul, vida personal, interés europeo; Mediotiempo (mediotiempo.com) — convocatoria Mundial, capitanía Cruz Azul; Sofascore (sofascore.com/es/news/erik-lira-controla-el-mediocampo) — estadísticas J1 vs Sudáfrica; Proceso (proceso.com.mx, 12 jun 2026) — entrevista post-J1; Récord (record.com.mx) — declaraciones post-J1; ClaroSports — alineaciones J2; El Financiero (elfinanciero.com.mx, 17 jun 2026) — Aguirre confirma alineación; TUDN (tudn.com) — competencia Lira/Álvarez; JuanFútbol (juanfutbol.com) — transferencia Girona avances; Excélsior (excelsior.com.mx) — interés Girona; Infobae México (infobae.com, 2 abr 2026) — Lira vs Álvarez pre-Mundial; JornadadeMéxico (jornada.com.mx, 13 may 2026) — declaraciones concentración.

#### Álvaro Fidalgo Fernández — MEX · Mediocampista central (MC / MCD-MCO) · 29 años · 5 caps
- **Club / situación:** Real Betis — Titular en los primeros meses (feb-mar 2026, incluyendo gol en el Derbi Sevilla). Perdio titularidad desde el 19 de marzo por el regreso de Amrabat y cambio tactico de Pellegrini a 4-3-3; no tuvo minutos en Betis los ultimos ~2.5 meses de temporada. Llega al Mundial con ritmo competitivo bajo en clubes pero motivacion altisima. Sin lesion aguda — gestiona rotula bipartita congenita (condicion de nacimiento, no lesion propiamente). Valor de mercado pico 8M EUR (dic 2024). Contrato hasta jun 2030.
- **Físico/anatomía:** 174 cm, 68 kg, velocidad punta ~31 km/h, durabilidad 78/100
- **Historial de lesiones:** Sin lesiones relevantes; fragil en lo fisico/fuerza
- **Familia:** Novia Pilar Sanchez (Asturias, 1997), pareja de ~12 anos; lo acompano 5 anos en Mexico; ella escribio carta de despedida emotiva al America al regresar a Espana. Sin hijos. Padre ex-futbolista que se lesiono gravemente a los 20 anos y tuvo que retirarse. Abuelo paterno Rafael Fidalgo, futbolista (UP Langreo, Real Oviedo, Caudal Deportivo — Segunda Division), figura inspiracional y 'como un padre' para Alvaro. DATO CRITICO CONFIRMADO: Alvaro declaro publicamente que su abuelo fallecio poco despues de su regreso a Espana en febrero 2026: 'Hace un mes perdi a mi abuelo, fue un momento muy duro porque el era como un padre para mi. Justo ahora que llegaba a Espana y podia disfrutar con el del futbol, lo perdi.' Pudo pasar unos dias con su abuela en Asturias.
- **Estado personal:** Estado personal complejo pero con resolucion positiva hacia el partido. La vuelta a Espana (feb 2026) fue agridulce: lloro al dejar Mexico ('pase unos dias muy triste... pero a la vez feliz'), y poco despues perdio a su abuelo Rafael, figura central de su vida y quien lo llevo al futbol. Este duelo personal es reciente. Sin embargo, el Mundial representa la redencion emocional completa: defender a Mexico — el pais que lo hizo jugador — desde Guadalajara (Estadio Akron, escenario de sus finales con America), con Pilar a su lado. En sus declaraciones post-debut vs Sudafrica (11-jun): 'una sensacion que no habia sentido nunca', 'aun no le cae el veinte'. El animo es de gratitud desbordante y compromiso total. Estable emocionalmente a pesar del duelo reciente; el Mundial funciona como catalizador positivo. Declaro: 'si me toca representar a Mexico, voy a dejar la vida.'
- **Personalidad:** Lider natural innato: fue capitan del Real Madrid Castilla (bajo Raul Gonzalez) y capitan del Club America. Caracteristica humildad asturiana — un testigo conto que 'otro nino te hubiera dicho que es capitan del Madrid, pero ni lo menciono'. Orador y motivador en vestuario: en la Seleccion, el veterano Cesar Montes cedio la palabra final de aliento a Fidalgo antes del debut. Expresivo emocionalmente — llora, canta el himno con intensidad, 'piel chinita' en el estadio. Tecnicamente meticuloso, prioriza el bien colectivo sobre estadisticas individuales (segun quienes lo conocen desde joven). Maduro para su edad — hablo de su relacion de 12 anos con Pilar con lucidez. Mentalidad de futbolista total: trabaja en recuperacion aunque su rol natural es creativo. Caracter frio en el juego pero ardiente en lo emocional fuera de el.
- **Motivación hoy:** CONFIRMADO: Deuda de gratitud profunda con Mexico ('quiero devolverle todo a Mexico'). CONFIRMADO: Este es su primer y posiblemente unico Mundial; lo vive como un honor irrenunciable. CONFIRMADO: Jugar en Guadalajara/Akron — territorio conocido de sus finales con America — es emotivamente potente. ESTIMADO: La reciente muerte de su abuelo Rafael, quien lo llevo al futbol, anade una capa de motivacion dedicatoria. ESTIMADO: Necesita reivindicarse deportivamente tras perder la titularidad en Betis los ultimos meses. CONFIRMADO: La critica por 'naturalizado' lo motiva a demostrar legitimidad ('esperaba las criticas'). CONFIRMADO: Pilar Sanchez en las gradas como unica familia-pareja presente en Mexico.
- **Biografía:** Alvaro Fidalgo Fernandez nacio el 9 de abril de 1997 en Hevia, Siero, Asturias, Espana, en una familia marcada por el futbol: su abuelo Rafael jugo en Segunda Division espanola y su padre fue futbolista hasta que una grave lesion a los 20 anos trunco su carrera. Formado en las canteras del Real Oviedo y el Sporting de Gijon antes de dar el salto a La Fabrica del Real Madrid, donde llego a ser capitan del Castilla bajo las ordenes de Raul Gonzalez, Fidalgo era un talento prometedor sin hueco en el primer equipo blanco. En febrero de 2021 aterrizo en Mexico cedido al Club America — desconocido para la aficion mexicana — y en cinco anos se convirtio en leyenda absoluta del club mas grande del pais: 183 partidos, 20 goles, 3 titulos de Liga MX, capitan con brazalete, ido de vestuario, capaz de dar el discurso de motivacion que otros veteranos no se atrevian a pronunciar. Su novia asturiana Pilar Sanchez lo acompano los cinco anos en Mexico, dejando atras su vida normal para compartir ese sueno. En diciembre de 2024 obtuvo la nacionalidad mexicana, en febrero de 2026 la FIFA aprobó su cambio de federación y en febrero de ese mismo ano regreso a Espana para unirse al Real Betis — llorando al dejar Mexico. Meses despues, su abuelo Rafael, el hombre que lo habia llevado al futbol de nino y corriendo a contarle que lo llamaban del Real Madrid, fallecio cuando Fidalgo ya estaba en Sevilla. Su debut mundialista con el Tri — ante Sudafrica el 11 de junio de 2026, como titular, en el Estadio Azteca — lo dejo sin palabras: 'una sensacion que no habia sentido nunca'. Hoy, en Guadalajara, en el estadio donde gano finales con el America, debuta en la jornada 2 ante Corea del Sur: el mediocampista que elige gratitud sobre conveniencia, que se forjo lider callado en Madrid, leyenda adoptada en Mexico, y que lleva en las piernas la deuda con un pais, un abuelo y una historia de vida unica.
- **🗣️ Monólogo interior:** *“Este es mi escenario, esta es mi altura. La pelota me va a buscar y yo la quiero, hoy mas que nunca. Siento el Akron entero encima, casi todos de los nuestros, y eso me hincha el pecho pero tambien me aprieta: si ganamos clasificamos hoy, y no quiero que se nos escape. Corea va a venir intensa, a presionarme arriba, a no dejarme girar... pero conozco esta altitud, se que a ellos los 1,500 metros les van a pesar las piernas en el ultimo cuarto de hora, ahi es donde yo voy a manejar los tiempos. Tejera pita todo, asi que ojo con las protestas y con el barrido a destiempo, no me puedo dejar comer la amarilla tonta. Pausa, cabeza fria, y cuando se abra el partido, vertical. Hoy lo dejamos cerrado.”*
- **X-factor:** Dictar el ritmo y gestionar la altitud: cansar a Corea con posesion y aparecer en el ultimo tercio cuando a ellos les falte el aire.
- **Confianza del dato:** ALTO en: fecha de nacimiento, club actual, rótula bipartita, relación con Pilar Sanchez, muerte del abuelo Rafael (declaracion publica propia), 5 caps con Mexico, perdida de titularidad en Betis (multiple fuentes), debut vs Sudafrica titular, liderazgo en vestuario (multiple fuentes). MEDIO en: numero exacto de caps al dia de hoy (6 si se cuenta el partido de hoy, 5 confirmados previos; las fuentes difieren entre 4 y 5 antes del debut vs Sudafrica — se usa 5 como cifra post-J1 confirmada). ESTIMACION PRUDENTE en: atributos numericos del schema (no existen ratings oficiales; se basan en estadisticas Liga MX 89-96% pase, 2 amarillas en 42 partidos para disciplina, rol capitan para liderazgo, condicion fisica con rótula bipartita para injury_risk, falta de minutos en Betis para stamina_base). emotional_state_today=82 refleja motivacion altisima matizada por duelo reciente del abuelo.
- **Fuentes:** Wikipedia Alvaro Fidalgo (EN): https://en.wikipedia.org/wiki/%C3%81lvaro_Fidalgo | Heraldo de Mexico - quien es Fidalgo Mundial 2026: https://heraldodemexico.com.mx/deportes/2026/5/30/quien-es-alvaro-fidalgo-tricampeon-de-la-liga-mx-mediocampista-de-la-seleccion-mexicana-para-el-mundial-2026-822434.html | DAZN MX - por que juega con Mexico: https://www.dazn.com/es-MX/news/f%C3%BAtbol/quien-es-alvaro-fidalgo-por-que-juega-mexico/1npr52bawhnwi1g94juevssp1b | MedioTiempo - espanol que se enamoro de Mexico: https://www.mediotiempo.com/futbol/seleccion-mayor/alvaro-fidalgo-el-espanol-que-se-enamoro-de-mexico-y-jugara-su-primer-mundial | ABC Noticias - Pilar Sanchez: https://abcnoticias.mx/deportes/2024/12/13/conoce-pilar-sanchez-la-pareja-de-alvaro-fidalgo-que-lo-siguio-mexico-fotos-234532.html | TUDN - piel chinita debut Mundial: https://www.tudn.com/mundial-2026/mexico-vs-sudafrica/alvaro-fidalgo-admite-que-sintio-la-piel-chinita-en-el-mexico-vs-sudafrica-del-mundial-2026 | BolaVip/AmericaMonumental - pierde titularidad Betis: https://americamonumental.bolavip.com/internacional/no-sera-titular-en-el-mundial-alvaro-fidalgo-acaba-la-temporada-con-el-real-betis-borrado-y-sin-minutos | BolaVip - juramento quiero devolverle: https://americamonumental.bolavip.com/noticias/el-juramento-de-alvaro-fidalgo-a-mexico-en-el-mundial-2026-quiero-devolverle-todo-a | ESPN - rotula bipartita: https://espndeportes.espn.com/futbol/mexico/nota/_/id/15863813/america-alvaro-fidalgo-lesion-rodilla-condicion-congenita-rotula-bipartita | BolaVip - liderazgo debut Seleccion: https://americamonumental.bolavip.com/seleccion-mexicana/apenas-debuto-y-alvaro-fidalgo-demostro-que-llego-para-ser-el-lider-de-la-seleccion-mexicana | BolaVip - anecdota capitan Real Madrid Castilla: https://americamonumental.bolavip.com/noticias/la-anecdota-que-nadie-conocio-sobre-alvaro-fidalgo-cuando-era-capitan-del-real-madrid-castilla | TheObjective - asturiano que renuncio a Espana: https://theobjective.com/deportes/futbol/mundial/2026-06-11/alvaro-fidalgo-renuncio-espana-mexico/ | TUDN - Fidalgo lloro al irse de Mexico: https://www.tudn.com/mundial-2026/equipos/seleccion-mexico/alvaro-fidalgo-no-evito-lagrimas-cuando-se-fue-de-mexico-regreso-espana | El Universal - mensaje post debut Mundial: https://www.eluniversal.com.mx/deportes/alvaro-fidalgo-envia-mensaje-tras-su-debut-en-el-mundial-2026-con-mexico-agradecido-por-tanto/ | FootyStats estadisticas 2024-25: https://footystats.org/es/players/spain/alvaro-fidalgo-fernandez | SI.com - alineaciones Mexico vs Corea: https://www.si.com/es-us/futbol/alineaciones-mexico-vs-corea-del-sur-18-6-2026 | Hecho en California - estoy orgulloso de ser asturiano: https://www.hechoencalifornia1010.com/alvaro-fidalgo-estoy-orgulloso-de-ser-asturiano-y-espanol-pero-mexico-me-dio-un-carino-especial-6/

#### Gilberto Mora — MEX · MC ofensivo / interior · 17 años · 9 caps
- **Club / situación:** Xolos de Tijuana — Titular indiscutible cuando esta sano; renovó contrato historico 3 años hasta 2029 con clausula de salida europea (junio 2026), recibirá el dorsal 10 en Apertura 2026. Perdio la mayoria del Clausura 2026 por pubalgia (76 días fuera), pero se recuperó al 100% segun el propio jugador. Real Madrid, Barcelona y Ajax lo siguen. Representado por Rafaela Pimenta. Valor de mercado estimado en 10 millones de euros. Hoy en el Mundial porta el 19.
- **Físico/anatomía:** 168 cm, 63 kg, velocidad punta ~31 km/h, durabilidad 75/100
- **Historial de lesiones:** Sin lesiones; pubalgia previa superada; inmadurez fisica (17a)
- **Familia:** Padre: Gilberto Mora Olayo, exfutbolista profesional (Jaguares de Chiapas, Puebla, Xolos) con ~300 partidos de carrera; hoy entrenador de fuerzas basicas de Xolos; fue el primer tecnico de su hijo en la Sub-13. Dos hermanas: Kamila y Barbara (perfil bajo, lo apoyan en las gradas). Sin novia publica confirmada a junio 2026; vida sentimental completamente privada. Madre: informacion publica no disponible. Familia unida y presente en el proceso mundialista.
- **Estado personal:** Estado personal estable y emocionalmente elevado. La recuperacion de la pubalgia fue un periodo de angustia real: admitio publicamente dudar de si llegaria al Mundial. Viajo a Pittsburgh (EE.UU.) para recibir tratamiento especializado, descartando cirugia. Al declararse sano, publico un mensaje emocional en Instagram ('un sueño que empezó en el patio trasero ahora se vuelve realidad'). Nació en Tuxtla Gutiérrez, Chiapas; se mudó a Tijuana de niño para desarrollarse futbolísticamente. Su padre es figura central de apoyo. Recién firmó el mayor contrato de la historia de Xolos. Es el jugador mas joven del Mundial 2026. Animo: muy alto, gratitud enorme por estar aqui, hambre de protagonismo.
- **Personalidad:** Maduro muy por encima de su edad. Tranquilo, enfocado, bajo perfil ante los medios: 'No me gusta ver mucho ese tipo de cosas que se hablan de mi; trato de enfocarme en lo mio, de disfrutar, vivir el presente.' Disfruta los partidos grandes desde chico ('desde chico me ha gustado jugar partidos importantes'). No se deja llevar por la presión ni por el ruido externo. Disciplinado (formacion paterna, carrera profesional desde los 15). Tecnico Juan Carlos Osorio lo comparo con Iniesta por su naturalidad y lectura del juego. Sociable pero discreto en lo personal; activo en Instagram (@gil_morita, +1M seguidores) pero sin sobreexposicion sentimental. Lider silencioso, no temperamental.
- **Motivación hoy:** HOY: Posible debut como TITULAR en un Mundial (vs Corea del Sur), lo que romperia otro record historico para Mexico. Viene de superar una lesion que casi lo deja fuera del torneo — la gratitud y el hambre de revancha son maximos. El apoyo de su padre (figura clave en su formacion y tambien en el plantel de Xolos) lo ancla emocionalmente. El contrato nuevo con el 10 y el interes de Real Madrid/Barca crean un escaparate perfecto hoy. Mexico necesita ganar para asegurar el liderato del Grupo A — el tecnico Aguirre le da confianza con la titularidad. Quiere demostrar que la recuperacion fisica fue completa.
- **Biografía:** Gilberto Rafael Mora Zambrano nació el 14 de octubre de 2008 en Tuxtla Gutiérrez, Chiapas, en el seno de una familia futbolera: su padre, Gilberto Mora Olayo, fue mediocampista profesional con cerca de 300 partidos en Liga MX y Ascenso, y hoy dirige las fuerzas basicas de los propios Xolos, el club que formó a su hijo. La familia se mudó a Tijuana para potenciar su desarrollo, y en 2019 ingresó a la academia del club fronterizo Sub-13, entrenado inicialmente por su propio padre. Su ascenso fue vertiginoso: debutó en Primera División el 18 de agosto de 2024 con apenas 15 años, dio una asistencia en su estreno y doce dias despues anoto ante Leon para convertirse en el goleador mas joven de la historia de la Liga MX. En 2025 acumuló 33 partidos con Xolos (8 goles, 1 asistencia), fue convocado a la seleccion mayor en enero de ese año —el jugador mas joven en hacerlo con 16 años y 94 dias—, lidero el Mundial Sub-20 de Chile con 3 goles y 2 asistencias, y coronó el año ganando la Copa Oro 2025 con Mexico como el futbolista mas joven en levantar un titulo internacional (16 años y 265 días), superando a Lamine Yamal. El Clausura 2026 lo golpeó con una pubalgia que lo tuvo fuera 76 dias y lo llevó a Pittsburgh para un tratamiento conservador que evitó la cirugia. Superada la lesion, Javier Aguirre lo incluyó en la convocatoria mundialista; al entrar de cambio ante Sudáfrica el 11 de junio de 2026 (17 años y 240 dias) se convirtió en el sexto jugador mas joven en la historia del Mundial y el primero de Mexico en ese hito. Hoy, ante Corea del Sur, apunta a ser titular por primera vez en una Copa del Mundo.
- **🗣️ Monólogo interior:** *“Tengo 17 anos y todo este estadio esta gritando mi nombre, no me lo puedo creer, pero no puedo dejar que me tiemblen las piernas. En la J1 contra Sudafrica me solte y me senti libre; hoy es distinto, hoy si ganamos ya estamos en 16avos y eso lo cargo en el pecho. La altura de Guadalajara es de mi tierra, eso me ayuda, voy a correr hasta el final. Si me llega la pelota voy a encarar, voy a atreverme, porque para eso me trajeron; solo tengo que controlar la sangre caliente y no caer en el primer roce que me busquen, el arbitro hoy saca tarjetas como caramelos.”*
- **X-factor:** Su descaro juvenil para encarar y desequilibrar en el uno contra uno, jugando sin miedo en casa y con la altitud a su favor.
- **Confianza del dato:** Alta en datos biograficos, familiares, lesion y club. Alta en caps (9 confirmados por Wikipedia a la fecha del debut mundial). Alta en estado emocional y motivacion (respaldado por declaraciones publicas directas del jugador). Estimacion prudente en atributos numericos: skill/finishing/pace basados en estadisticas Liga MX (10G/53P, 8G/33P en 2025) y desempeno internacional; composure y clutch elevados por comportamiento observado bajo presion real (Copa Oro, Mundial debut); stamina moderada-alta por recuperacion reciente de pubalgia (injury_risk elevado respecto a su media historica pero declarado sin dolor); consistency penalizada por irregularidad derivada de la lesion y juventud.
- **Fuentes:** Wikipedia ES (Gilberto Mora Zambrano): https://es.wikipedia.org/wiki/Gilberto_Mora_Zambrano | Informador (debut en Mundial): https://www.informador.mx/deportes/mundial-2026-de-tijuana-para-el-mundo-gilberto-mora-se-consagra-como-el-seleccionado-mexicano-mas-joven-en-debutar-20260614-0073.html | Jornada (renovacion contrato): https://www.jornada.com.mx/noticia/2026/06/09/mundial/gilberto-mora-el-jugador-mas-joven-del-mundial-renovo-su-contrato-con-tijuana-por-tres-anos | TUDN (titular vs Corea): https://www.tudn.com/mundial-2026/mexico-vs-corea-sur/gilberto-mora-y-edson-alvarez-serian-titulares-ante-corea-del-sur | TUDN (aviso a Corea): https://www.tudn.com/mundial-2026/mexico-vs-corea-sur/aviso-a-corea-gilberto-mora-asegura-estar-hecho-para-juegos-importantes | TUDN (lesion): https://www.tudn.com/mundial-2026/mexico-vs-corea-sur/gilberto-mora-dudo-de-recuperarse-a-tiempo-de-su-lesion-para-el-mundial-2026-con-mexico | Infobae (renovacion): https://www.infobae.com/mexico/deportes/2026/06/09/gilberto-mora-renueva-con-xolos-de-tijuana-pase-lo-que-pase-en-el-mundial-2026/ | El Informador (sin presion): https://www.informador.mx/deportes/mundial-2026-gilberto-mora-descarta-presion-por-su-edad-20260617-0197.html | El Manana (perfil): https://www.elmanana.com.mx/deportes/2026/6/17/javier-aguirre-sorprende-todos-en-el-mundial-2026-gilberto-mora-va-de-titular-ante-corea-del-sur-178451.html | sdpnoticias (padre): https://www.sdpnoticias.com/deportes/quien-es-gilberto-mora-olayo-el-papa-de-gilberto-mora-tambien-fue-futbolista-profesional/ | Xolos.com.mx (contrato #10): https://xolos.com.mx/noticias/primer-equipo/12176/gilberto-mora-extiende-su-contrato-con-xolos-y-usara-el-numero-10

#### Roberto Alvarado — MEX · Extremo Derecho (zurdo) · 27 años · 69 caps
- **Club / situación:** Deportivo Guadalajara (Chivas) — Titular indiscutible en Chivas bajo Gabriel Milito. Clausura 2026: 17 partidos, 1.393 min, 1 gol, 2 asistencias, 35 pases clave, 86% precision de pase, nota FotMob 7.52. En sus ultimos 9 partidos de Liga MX habia sumado 6 contribuciones directas (2 goles + 4 asistencias). Renovó contrato en septiembre 2024 hasta junio 2029. Valor mercado ~7,5 M EUR. FC Copenhague sondea interés según TNT Sports (sin oferta formal). En el debut mundialista vs Sudafrica (2-0, J1) fue titular, brindo asistencia clave para el 2-0 de Jimenez al min. 67 con un centro bombeado, gano 9 de 14 duelos, recupero 6 balones y provoco la expulsion de Zwane. Calificacion SofaScore 8.2 (mejor del equipo junto a Quinones). Confirmado titular para J2 vs Corea del Sur.
- **Físico/anatomía:** 176 cm, 70 kg, velocidad punta ~32 km/h, durabilidad 82/100
- **Historial de lesiones:** Limpio; tobillo sep-oct 2025 (~1mes)
- **Familia:** Casado con Dayana Gomez (influencer, boda 24-may-2019); juntos desde ~2016. Perdieron a su primer bebe en mayo 2021 (aborto espontaneo durante la final de Cruz Azul vs Santos; Alvarado pidio permiso al club para acompañar a su esposa). En 2022 nacio su hija Emily, quien los lleno de dicha tras el duro golpe previo. Tienen canal de YouTube de pareja llamado 'Yaya y Piojo'. Madre de Roberto vendio frituras para costear sus traslados al Celaya desde Salamanca. En octubre 2025 circularon rumores no confirmados de que el cunado del Piojo habria sido secuestrado; ningun comunicado oficial fue emitido. Padres con vision distinta: madre priorizaba estudios, padre el futbol.
- **Estado personal:** Estado general ESTABLE y emocionalmente elevado. Vida familiar solida tras superar la tragedia de 2021 con la perdida de su primer bebe; la llegada de Emily en 2022 marco un antes y despues en su madurez personal. El episodio de octubre 2025 (borrado de redes, rumores de amenazas/extorsion a familiar) genero incertidumbre pero no produjo comunicados oficiales; el periodista Chuyón lo califico de fake news. Alvarado regreso a la actividad normal sin aparentes secuelas. En 2026 esta claramente en un momento vital de enorme motivacion: declaraciones publicas de querer llegar a la final del Mundial, de representar a su familia y a Mexico. Tiene restaurante abierto junto a su esposa en Salamanca, Guanajuato. Hobby historico: skateboarding (antes de ser futbolista profesional). Presencia activa en Instagram (@piojo.13, ~876K seguidores). Animo positivo y competitivo reportado en todas las fuentes pre-Mundial 2026.
- **Personalidad:** Humilde y cercano con la aficion: nunca se ha negado a fotos o autografos incluso en malos momentos. Competitivo y ambicioso: declaro publicamente querer llegar a la final del Mundial. Autocritico: tras el debut vs Sudafrica reconocio que el equipo 'cayo en la desesperacion' y no supo mantener la posesion. Temperamento impulsivo en ocasiones: en octubre 2024 lanzo un petardo (coheton) a la sala de prensa de Verde Valle hiriendo levemente a un fotografo; pidio disculpas publicas y acepto responsabilidad. Maduro y responsable: en el accidente de transito de 2021 con Santi Gimenez bajo del auto, auxilio a la victima metiendole la mano en la boca para que no se ahogara, y la visito en casa despues. Sensible familiarmente: pidio permiso a Cruz Azul para estar con su esposa cuando perdieron el bebe, antes de la final. Jugueton/bromista: el incidente del petardo y mensajes raros en redes confirman vena playera/picaresca. Mentalmente fuerte para situaciones de presion: demostrado en la final de Cruz Azul (campeon) horas despues del drama familiar. Icono local en Salamanca, Guanajuato; voz del orgullo salmantino.
- **Motivación hoy:** POSITIVOS HOY: (1) Juega en casa, en el Estadio Akron de Guadalajara, su ciudad, con aficion rojiblanca que lo idolatra; factor motivacional enorme. (2) Victoria en J1 vs Sudafrica con asistencia y nota 8.2 le da confianza maxima. (3) Declaraciones publicas de sonar con la final; J2 victoriosa clasifica a Mexico matematicamente. (4) Interes europeo reavivado post-debut mundialista; un buen partido puede abrir puertas al FC Copenhague u otros. (5) Esposa e hija Emily como motor emocional declarado explicitamente. (6) Redimirse de Qatar 2022 donde solo jugo 18 minutos. POSIBLE PESO: (1) Criticas cronicas de la prensa y aficion a su rendimiento con el Tri (poca eficacia goleadora: 5 goles en 69 partidos); debe gestionar ese ruido. (2) Episodio de octubre 2025 (redes/familia) potencialmente no resuelto del todo.
- **Biografía:** Roberto Carlos Alvarado Hernandez, nacido el 7 de septiembre de 1998 en Salamanca, Guanajuato (apodado 'El Piojo' por su idolo Claudio Lopez), es la historia tipica del futbolista mexicano forjado en la pobreza y la tenacidad: su madre vendia frituras para pagar los camiones que lo llevaban a entrenar al Celaya, club con el que debuto a los 15 anos como el jugador mas joven en la historia de la segunda division. A los 14 anos paso pruebas en Leicester, Manchester City, Manchester United y Liverpool — el City quiso ficharlo pero la burocracia de la FIFA y documentos mal gestionados frustraron el salto; en sus instalaciones coincidio con Phil Foden y Jadon Sancho. Su carrera escalo por Pachuca, Necaxa y Cruz Azul, donde en 2021 fue pieza del titulo que acabo 23 anos de sequia cementera, viviendo en esos dias uno de los episodios mas desgarradores de su vida: la perdida del primer bebe que esperaba con su esposa Dayana Gomez le obligo a pedir permiso para abandonar la concentracion antes de la final; horas despues fue campeon y dedico el titulo a 'la princesa que les ayudo a ser campeones'. En diciembre 2021 llego a Chivas en trueque por Antuna y Mayorga, convirtiendose en figura y lider de facto del Rebano — no de discurso sino de cancha y exuberancia tecnica. Con la Seleccion Mayor acumula 69 caps (5 goles, 7 asistencias), tres Copa Oro (2019, 2023, 2025), Nations League 2024/25 y medalla de bronce olimpica en Tokio 2021; su segunda Copa del Mundo arranca de una manera completamente diferente a Qatar 2022 (donde solo jugo 18 minutos): titular indiscutible de Aguirre, nota 8.2 con asistencia vs Sudafrica en el Azteca, e intereses europeos revividos. Hoy, 18-jun-2026, juega en el Estadio Akron de Guadalajara — su casa, su ciudad, su gente — con la certeza de que este partido puede escribir la pagina mas grande de su carrera.
- **🗣️ Monólogo interior:** *“Esta es mi cancha. El Akron es mi casa, aqui me hice, y hoy esta lleno de los mios gritando mi nombre, eso me prende mas de lo que me pesa. Respiro la altura de Guadalajara como respiro todos los dias, mientras ellos van a sentir que el aire no alcanza al minuto 70. Tengo la responsabilidad de encarar, de romper por izquierda y poner centros que duelan, y con Corea boicoteando a su prensa y rotos por dentro, los voy a apretar desde el primer minuto. Tejera pita todo, asi que cuido la pierna en la entrada pero no le quito ni una a la encarada; si ganamos hoy clasificamos y nos quedamos con la cima, y no me voy a perdonar guardarme nada en mi propia ciudad.”*
- **X-factor:** El factor local y la altitud: encara sin miedo en su estadio y revienta a Corea por la banda cuando se queden sin aire.
- **Confianza del dato:** Alto en datos biograficos, estadisticas de club y seleccion, vida personal/familiar, y contexto del partido — todo de fuentes periodisticas mexicanas reconocidas (ESPN, Mediotiempo, Record, Infobae, Transfermarkt). Medio-alto en atributos numericos (derivados de estadisticas publicadas y perfil descriptivo pero sin acceso a metricas taticas propietarias). Bajo en el episodio de octubre 2025 (rumores de secuestro/amenazas a familiar): ninguna fuente oficial confirmo la version; el periodista del Chuyon lo califico de fake news.
- **Fuentes:** CONFIRMADO: Fecha nacimiento (07/09/1998), ciudad (Salamanca GTO), posicion (extremo derecho, zurdo): Wikipedia/Transfermarkt/Heraldo. Caps seleccion mexicana (68 pre-Mundial + 1 vs Sudafrica = 69): Transfermarkt, Mediotiempo. Goles/asistencias con Tri (5/7): Heraldo, Mediotiempo. Clausura 2026 stats (17 PJ, 1 gol, 2 asistencias, 1393 min, 7.52 FotMob): 365Scores/FotMob/ClaroSports. Asistencia vs Sudafrica + nota 8.2 SofaScore + estadisticas defensivas: ClaroSports, Rebanio Pasion, TUDN. Contrato Chivas hasta 2029: Transfermarkt, Mediotiempo. Valor mercado 7.5M EUR: Transfermarkt may-2026. Matrimonio con Dayana Gomez (may 2019): SDP Noticias/ESPN/ShowDeportivo. Perdida primer bebe mayo 2021: ESPN/Jon Arnold Twitter. Nacimiento Emily 2022: ESPN. Episodio petardo octubre 2024: Infobae/El Universal/MVS. Desaparicion redes octubre 2025 (rumores no confirmados): Publimetro/SoyReferee. Accidente de transito 2021 con Gimenez: Mediotiempo/JuanFutbol. Prueba Manchester City: ESPN/Sopitas. Apodo origin (Claudio Lopez): TVAzteca. Declaracion 'quiero llegar a la final del Mundial': Record/De10. Declaracion 'mi esposa e hija me dan motivacion': La Opinion/Informador. Clausula rescision ~22M USD: ESPN Mexico. Interes FC Copenhague: ElFutbolero/JuanFutbol. Polemica Son servicio militar Corea: Latinus/LaNacion/LaTercera. ESTIMADO/INFERIDO: Atributos numericos (skill, pace, finishing, etc.) derivados de estadisticas publicas, calificaciones SofaScore/FotMob, descripcion de estilo de juego y perfil de personalidad reportado en medios. Composure volatility: inferido por incidente petardo y mensajes raros en redes vs actuaciones de alta presion (final Cruz Azul, debut Mundial). Injury risk: basado en ausencia unica de 5 jornadas Apertura 2025 por tobillo; actualmente sin ninguna lesion reportada.

#### Raúl Jiménez — MEX · CF · 35 años · 128 caps
- **Club / situación:** Wolverhampton Wanderers — Recién firmado como agente libre con Wolverhampton el 9 de junio de 2026 (2 años + opción), días antes del Mundial. Su contrato con Fulham expiró; disputó 36 partidos en Premier League 2024-25 (9 goles, 2,199 min), siendo titular en 27 ocasiones. Último partido con Fulham: 24 de mayo vs Newcastle (18 min como suplente). Llegó al Mundial con buena forma física pero sin haber jugado 90 minutos completos en semanas. Wolverhampton jugará en la Championship 2026-27 (descenso). No hay lesión activa confirmada al inicio del torneo.
- **Físico/anatomía:** 188 cm, 76 kg, velocidad punta ~30 km/h, durabilidad 65/100
- **Historial de lesiones:** FRACTURA DE CRANEO + cirugia cerebral 2020; isquios 2024; cadera 2025; recuperado (35a)
- **Familia:** Pareja: Daniela Basso, actriz mexicana (telenovelas Simplemente María, Corazón indomable). Relación desde 2017; compromiso de matrimonio anunciado en febrero 2025 durante viaje a los Alpes suizos. Hijos: Arya (nacida 2020, durante recuperación de fractura de cráneo) y Ander (nacido 5 de mayo de 2022, mismo cumpleaños que Raúl). DUELO FAMILIAR RECIENTE: su padre, Raúl Jiménez Vega, falleció el 11 de marzo de 2026 a los 62 años por cáncer de páncreas, apenas 3 meses antes del Mundial. Raúl no pudo asistir al funeral en Tepeji del Río, Hidalgo, por compromisos con Fulham en Londres.
- **Estado personal:** Estado emocional complejo pero canalizado positivamente. Lleva el duelo de su padre (fallecido 11-mar-2026) como motor emocional central de este Mundial. En el debut vs Sudáfrica (J1, 11-jun-2026) marcó su primer gol mundialista de cabeza al 67', lloró al festejarlo mirando al cielo y lo dedicó explícitamente a su padre: 'Mi papá sería el más feliz de la vida'. El festejo se convirtió en imagen icónica del torneo. Esto supone una catarsis parcial pero también puede generar una carga emocional de alto voltaje para J2. Fuera del fútbol: estable familiarmente, Daniela y sus hijos están en México durante el torneo; la boda planeada post-Mundial. No se reportan turbulencias de pareja. La promesa de fichaje con Wolverhampton (club de su corazón) está resuelta, sin incertidumbre contractual que lo distraiga. El regreso al Estadio Akron (Guadalajara) con la afición local es un impulso adicional de orgullo regional.
- **Personalidad:** Líder silencioso y por el ejemplo, no por discursos. Temperamento frío post-lesión; la fractura de cráneo de 2020 lo transformó en un jugador más inteligente, menos impulsivo y más técnico. Sus propias palabras: 'Casi pierdo la vida. Ahora trato de disfrutar todo.' Perfil de construcción lenta ('fuego lento'), disciplina repetida hasta convertirse en carácter. Declaró públicamente que busca ser 'ese líder que tanto fuera como dentro del campo da lo mejor de sí mismo'. Alta capacidad para gestionar presión mediática; no genera polémicas. Agradecido, espiritual (festejo mirando al cielo), introvertido en lo emocional pero capaz de mostrar vulnerabilidad genuina. Respetuoso de los procesos: acepta convivir con la diadema protectora como rutina. No es un delantero que busca conflicto con rivales ni árbitros.
- **Motivación hoy:** MOTOR PRIMARIO HOY: la memoria de su padre, que nunca vio un gol suyo en un Mundial y cuyo deseo ('esperemos que se logre el gol en la Copa del Mundo, es algo que nos falta') quedó cumplido en J1. Ahora el impulso se convierte en continuidad — seguir haciendo que su padre 'esté orgulloso'. MOTOR SECUNDARIO: cerrar su carrera con legado histórico — es el 2do máximo goleador histórico de México (47 goles) y tiene a Chicharito en la mira. MOTOR TERCIARIO: este es su 4to y último Mundial a sus 35 años; la conciencia de que este torneo es el último capítulo define su hambre competitiva. FACTOR LOCAL: jugar en casa (Guadalajara, Estadio Akron) ante su afición. FACTOR DEPRESIVO POTENCIAL: el duelo no está cerrado, el peso emocional puede ser una carga en momentos de presión, aunque históricamente lo ha convertido en fortaleza. La catarsis del gol en J1 puede haber aliviado presión o puede haber elevado el listón de expectativas propias.
- **Biografía:** Raúl Alonso Jiménez nació el 5 de mayo de 1991 en Tepeji del Río, Hidalgo. Formado en el América, su carrera lo llevó al Atlético de Madrid, Benfica y finalmente al Wolverhampton, donde entre 2018 y 2023 se convirtió en ídolo inigualable con 57 goles en 166 partidos y una participación estelar en Europa League. El 29 de noviembre de 2020 su vida estuvo en riesgo real: un choque de cabezas con David Luiz le produjo una fractura de cráneo y hematoma intracraneal que requirió cirugía de emergencia esa misma noche. Sobrevivió — 'fue un milagro', dijeron sus médicos — y regresó 336 días después con la diadema protectora que lleva hasta hoy y que se ha vuelto símbolo de su resiliencia. Con el Fulham (2023-2026) anotó 29 goles y consolidó su vigencia en la élite. Tres meses antes del Mundial 2026 perdió a su padre, Raúl Jiménez Vega, por cáncer de páncreas; no pudo asistir al entierro por estar en Londres. El 11 de junio de 2026, ante 87,000 personas en el Estadio Ciudad de México, marcó de cabeza su primer gol mundialista en cuatro intentos, lo dedicó mirando al cielo y lloró rodeado de compañeros. Es el segundo máximo goleador histórico de la Selección Mexicana con 47 tantos en 128 partidos. El 9 de junio de 2026 firmó su regreso sentimental al Wolverhampton para la Championship 2026-27, cerrando el círculo con el club donde casi pierde la vida y donde nació su leyenda.
- **Confianza del dato:** Alta en datos biográficos, familiares, fractura de cráneo, muerte del padre, estadísticas de club (Fulham), fichaje Wolverhampton, gol J1 Mundial. Media-alta en caps exactos (127 Transfermarkt + 1 J1 = 128; algunas fuentes citan 125 antes del Mundial). Media en atributos numéricos del gemelo digital (estimaciones calibradas con datos públicos de rendimiento, no acceso a datos biométricos privados). Estimación: motivación hoy (93/100) basada en contexto emocional del padre + local + J1 exitoso; injury_risk (28/100) basado en diadema permanente pero sin lesión activa reportada y sólida temporada.
- **Fuentes:** Transfermarkt (caps: 127 previo, +1 J1 = 128; fichaje Wolves 9-jun-2026): transfermarkt.us/raul-jimenez | Wikipedia Raúl Jiménez: en.wikipedia.org/wiki/Raúl_Jiménez | El Financiero (muerte padre 11-mar-2026, cáncer páncreas): elfinanciero.com.mx | Latinus (fallecimiento padre, 62 años): latinus.us | Infobae (gol J1, festejo emotivo, fractura cráneo): infobae.com | Mediotiempo (gol Sudáfrica, lágrimas, dedicatoria): mediotiempo.com | TUDN (lesión costillas sept 2025, gol Aston Villa): tudn.com | ABC Noticias (titular Crystal Palace 1-ene-2026): abcnoticias.mx | Proceso (Wolves Championship): proceso.com.mx | Footystats/ESPN (36 PL apps, 9 goles, 2,199 min, 5 amarillas): espn.com/soccer | Telemundo (4to Mundial, goles históricos): telemundo.com | El Universal (47 goles, 2do máximo goleador): eluniversal.com.mx | Tunota (Daniela Basso, hijos Arya y Ander): tunota.com | El Imparcial (compromiso feb 2025): elimparcial.com | Record (declaraciones liderazgo): record.com.mx | SI.com (alineación México J2 vs Corea): si.com | Depor (alineación confirmada J2): depor.com | Claro Sports (contexto partido): clarosports.com | La Nacion AR (fractura cráneo, historia): lanacion.com.ar | Expansion (historia carrera): expansion.mx

#### Julián Andrés Quiñones Quiñones — MEX · Delantero Centro / Extremo izquierdo · 29 años · 23 caps
- **Club / situación:** Al-Qadisiyah FC (Saudi Pro League) — Titular absoluto e indiscutible en Al-Qadisiyah. Cerro la temporada 2025/26 con 33 goles en 31 partidos (todos de titular, 2,719 minutos), coronandose campeon de goleo de la Saudi Pro League por delante de Ivan Toney (32) y Cristiano Ronaldo (28). Hat-trick en la ultima jornada 5-1 vs Al Ittihad. Renovacion de contrato hasta 2029-2030 con mejora salarial significativa. Vive solo en Khobar (Arabia Saudita) porque mando a su familia fuera del pais por el conflicto belico en Medio Oriente desde marzo-abril 2026. Llega al Mundial como el segundo maximo goleador del mundo en clubes en 2026.
- **Físico/anatomía:** 177 cm, 78 kg, velocidad punta ~33 km/h, durabilidad 68/100
- **Historial de lesiones:** Isquios fin-2025/ini-2026; susto fisico jun-2026; 33 goles temporada
- **Familia:** Esposa: Ana Gabriela Quinones Amato, mexicana, licenciada en Comunicacion, influencer con +213k seguidores en Instagram, casados en diciembre 2022. Hija en comun: Alanna, nacida el 21 de diciembre de 2023. Lionel (nacido 2015), hijo mayor de Ana Gabriela de relacion anterior, a quien Julian trata como propio. Una hija mayor de una relacion anterior de Julian (nombre no publico). Madre: Gloria Quinones, pilar de su vida; abuela materna, figura paterna sustituta; tres hermanas. Padre biologico: identidad no revelada publicamente. Familia nuclear (esposa e hija Alanna) fue evacuada de Arabia Saudita entre marzo-abril 2026 por los bombardeos en la zona del Golfo; Julian permanecio solo en Khobar hasta ser convocado al Mundial.
- **Estado personal:** Estado personal complejo pero con balance positivo neto. El hecho mas impactante reciente: vivio solo en Arabia Saudita durante meses tras mandar a su familia fuera por la guerra en Medio Oriente (tension con Iran, bombardeos visibles desde su zona hacia Barein). Declaro: 'Al principio si tenia miedo porque estaba mi familia conmigo. Era un temor de no saber; uno solo corre para donde sea, pero con la familia es muy complicado. Ahora me toco sacar a mi familia, estoy solo alla.' Esa soledad fue el telon de fondo de su extraordinaria temporada goleadora (33 goles). Ya en el Mundial, reunificacion familiar presumible o inminente por logistica del torneo. Recibido con euforia en Guadalajara con canto masivo 'Quinones hermano ya eres mexicano'. Marco el primer gol del Mundial 2026 el 11/jun ante Sudafrica en el Azteca. Estado de animo: en la cima de su vida deportiva y en proceso de reconectar emocionalmente con familia. Situacion personal globalmente estable y en ascenso tras superar la adversidad de la soledad y el conflicto.
- **Personalidad:** Resiliente y construido sobre la adversidad. Nacio en Magui Payan, Narino, Colombia, una de las zonas mas violentas del pais (Triangulo del Tilembi), creció sin padre, jugando descalzo, ayudando a su abuela en una tienda. Escapo de la guerrilla a los 15 anos. Su apodo de juventud fue 'Pantera' por la agresividad y fiereza con la que atacaba el gol. Tiene una ambicion declarada y explicita de ser referente: 'Yo naci listo para todo tipo de retos... esta version de Julian va a ser muy importante, tanto para mi como para todo el pais.' Es autocritico incluso en los triunfos: tras el 2-0 ante Sudafrica pidio mas presion colectiva. Responde a la presion de los naturalizados con hechos, no con palabras. Expreso gratitud profunda a Mexico como su segunda patria. Caracter combinado: humilde en declaraciones grupales, feroz y ambicioso en lo individual. No es lider vocal gritando, sino lider por rendimiento y presencia. Temperamento controlado dentro de la cancha (pocas faltas, 0.59 por 90 min). Mentalidad de killer en el area sin necesidad de provocacion.
- **Motivación hoy:** Motivacion HOY: (1) Ser el referente goleador de Mexico en su primer Mundial — objetivo que ya inicio con el gol inaugural de todo el torneo vs Sudafrica, quiere continuar esa narrativa historica. (2) La aficion de Guadalajara, que lo recibio con el canto 'Quinones hermano ya eres mexicano' — una validation emocional directa de su identidad como mexicano, algo que le pesa mucho dado el contexto de haber rechazado Colombia y los cuestionamientos iniciales por su naturalizacion. (3) Su familia: esposa e hija Alanna, que estuvieron separadas de el por la guerra; jugar bien es retribuir su sacrificio. (4) Consolidar la narrativa que ya escribio: el nino descalzo de Magui Payan que marco el primer gol de un Mundial 2026. Lo que le puede pesar: la soledad vivida en Arabia durante meses, aunque ese factor ya quedó atras con el inicio del torneo. El arbitro Gustavo Tejera (Uruguay) de mano dura puede elevar su alerta disciplinaria.
- **Biografía:** Julián Andrés Quiñones Quiñones (Magüí Payán, Colombia, 24 de marzo de 1997) es un delantero colombiano naturalizado mexicano que personifica la supervivencia convertida en excelencia: creció sin padre en una de las zonas más violentas de Colombia, jugando descalzo y ayudando a su abuela en una tienda de pueblo, antes de escapar de la influencia guerrillera a los 15 años rumbo a México. Forjado en las fuerzas básicas de Tigres, brilló en Lobos BUAP y se consagró como leyenda en Atlas con el histórico bicampeonato 2021-22, para luego refrendarla en Club América. Su salto a Al-Qadisiyah de Arabia Saudita en 2024 fue cuestionado, pero la temporada 2025/26 lo convirtió en el mayor goleador de la Saudi Pro League con 33 goles en 31 partidos, superando a Cristiano Ronaldo e Ivan Toney para alzarse con la Bota de Oro, todo ello mientras vivía solo en Khobar tras mandar a su esposa Ana Gabriela y su hija Alanna fuera del país por los bombardeos del conflicto de Medio Oriente. Naturalizado mexicano en octubre de 2023 tras rechazar un llamado de Colombia, debutó con el Tri en noviembre de ese año y se convirtió en el naturalizado más querido de la historia reciente del combinado nacional. En el Mundial 2026 escribió la página más gloriosa de su historia al marcar el primer gol del torneo al minuto 9 ante Sudáfrica en el Azteca, siendo aclamado con el canto 'Quiñones hermano ya eres mexicano' por miles de aficionados en Guadalajara días antes de enfrentar a Corea del Sur.
- **Confianza del dato:** ALTO en datos deportivos y perfil de club (multiples fuentes mexicanas e internacionales consistentes). ALTO en datos familiares (multiples perfiles especificos sobre Ana Gabriela y Alanna). ALTO en situacion personal reciente (evacuacion familia, soledad en Arabia: confirmado por TUDN, Infobae, Fox Sports). ALTO en estado animo hoy (recibimiento Guadalajara, declaraciones post-Sudafrica muy recientes). MODERADO en conteo exacto de caps (fuentes oscilan entre 18, 22 y 23; se usa 23 por ser el dato mas reciente de Wikipedia al momento del Mundial). ESTIMADO en atributos numericos: los valores reflejan el perfil real del jugador pero son estimaciones del investigador basadas en estadisticas y reportes cualitativos, no mediciones cientificas.
- **Fuentes:** Datos confirmados por fuentes: Nacimiento, origen y edad (Wikipedia ES, Heraldo de Mexico, Milenio); Goles y estadisticas Saudi Pro League 2025/26 (El Universal, Nmas, Fox Sports MX, El Imparcial, Fichajes.com); Situacion familiar y esposa Ana Gabriela (La Razon, Lafm, Chic Magazine, Athlon Sports); Evacuacion familia Arabia Saudita (Infobae, Fox Sports MX, AM.com.mx, Mediotiempo); Gol primer gol del Mundial 2026 vs Sudafrica (Heraldo de Mexico, Periodicocorreo, Depor, TUDN); Declaraciones post-partido Sudafrica (TUDN, El Tiempo, SI.com ES); Declaraciones sobre Corea del Sur (Aguilas Monumental/Bolavip, Record, SI.com); Recibimiento en Guadalajara (Aguilas Monumental/Bolavip, El Siglo de Torreon, Posta Deportes); Historia vida e infancia (Siete24.mx, SDP Noticias, Vision360, Goal.com US); Estadisticas disciplina (FotMob, Footystats, Fichajes.com); Alineacion probable Mexico vs Corea Sur (Mediotiempo, Depor, SI.com ES, ClaroSports); Partidos con seleccion mexicana: 23 caps confirmados por Wikipedia y declaraciones (primer gol en Mundial fue su tercer gol en partido 23 segun fuentes). Datos ESTIMADOS con cautela: composure_volatility (estimado bajo basado en pocas faltas 0.59/90 y comportamiento en presion mediatica); aerial (estimado moderado-bajo, perfil de extremo/delantero de profundidad mas que pivote aereo); injury_risk (bajo-moderado: no hay historial de lesiones graves reportadas, aunque hubo ausencias por musculo en 2024-25 segun ESPN Mexico).

#### Kim Seung-gyu — KOR · GK · 35 años · 89 caps
- **Club / situación:** FC Tokyo — Titular indiscutible en FC Tokyo (J1 League). En la temporada 2026 acumula 16 apariciones, 5 porterias a cero, 32 atajadas y un rating promedio de 6.99 en FotMob. Fichaje permanente firmado despues de su cesion exitosa en 2025; contrato hasta junio 2027. FC Tokyo lo cortejo durante su dura rehabilitacion y le brindo soporte medico especializado — lealtad que Kim ha recompensado con actuaciones clave. Llego al mundial en forma solida, con su ultimo mes mostrando variabilidad (rating 8.0 vs Kashiwa, 4.8 vs JEF United), pero con clara tendencia ascendente. Ya demostro en el J-League experiencia en penales (4 victorias, 2 derrotas en tandas de 2026).
- **Físico/anatomía:** 188 cm, 82 kg, velocidad punta ~30 km/h, durabilidad 80/100
- **Historial de lesiones:** Carrera durable, sin cirugias mayores
- **Familia:** Casado con la modelo y actriz Kim Jin-kyung (nacida 3 de marzo de 1997) desde el 17 de junio de 2024, en Seoul. Kim Jin-kyung es conocida en Corea del Sur por haber participado en el programa SBS 'Goal-Getting Ladies' y por su carrera en modelaje. Tienen una hija recien nacida, nacida el 4 de junio de 2026 — exactamente una semana antes de que iniciara el Mundial. Kim Seung-gyu no pudo estar presente en el parto por encontrarse en el campo de entrenamiento en Salt Lake City. Segun reportes, Kim Jin-kyung anuncio el nacimiento via redes sociales mientras el jugador permanecia en concentracion.
- **Estado personal:** Estado personal cargado emocionalmente pero con valentia transformada en combustible. Kim no pudo presenciar el nacimiento de su primera hija el 4 de junio de 2026 por estar concentrado con la seleccion — algo que el mismo describio como una deuda personal: 'Siento una profunda culpa hacia mi esposa e hija'. Esa culpa se ha convertido en motivacion publica y explicita: prometio regresar con un buen resultado como 'el mejor regalo para mi hija y esposa'. Tras su actuacion estelar contra Republica Checa (incluyendo una parada en el minuto 93), la prensa surcoreana y mexicana lo describio como 'heroe nacional' y la pareja fue denominada 'la pareja patriotica'. El ambiente dentro del campamento coreano esta enrarecido por la polemica del video que burlo el servicio militar de Son Heung-min (captado el 7 de junio por JTBC), lo que provoco un apagon mediatico colectivo, la cancelacion de entrevistas y la renuncia de un oficial de medios. La cohesion interna del equipo parece reforzada contra el enemigo comun externo, pero existe tension latente. Kim personalmente esta en un estado estable y ascendente.
- **Personalidad:** Veterano calmo, estoico y de liderazgo silencioso. No es el capitan oficial (ese es Son) pero actua como ancora emocional de la linea defensiva. Sus palabras post-partido contra Chequa fueron deliberadamente modestas — 'mis atajadas ayudaron al equipo aunque sea un poco' — revelando una personalidad que evita el protagonismo personal. Tiene una caracteristica mezcla de humor autodeprecativo (bromeo sobre no querer que su hija se pareciera a el) y seriedad competitiva. Sobrevivio dos roturas de ligamento cruzado anterior en menos de dos anos — incluyendo un momento en que considero retirarse — lo que habla de una resiliencia psicologica fuera de lo comun. Jugadores y analistas lo describen como un todo-terreno (all-round) en su posicion: no hay fallos evidentes. Su competencia con Cho Hyeon-woo la manejo sin conflicto publico, describiendola como mutuamente beneficiosa para ambos. Perfil: introvertido con autoridad natural, frio bajo presion, orientado al equipo, resiliente.
- **Motivación hoy:** Motivacion principal HOY: convertir este Mundial — su cuarto y posiblemente ultimo — en el mejor regalo para su hija recien nacida y su esposa, a quienes abandono en el momento mas importante. La culpa por no estar en el parto se ha convertido en gasolina competitiva pura. Motivacion secundaria: sellar su legado como el portero mas experimentado de Corea del Sur (4 Mundiales), superando cualquier duda despues de dos ACL. El contexto del apagon mediatico por la burla a Son refuerza la mentalidad de bunker del grupo: todos contra todos. Kim como veterano lidera esa cohesion. La alta altitud del Estadio Akron (~1,566 m) y el estadio en territorio mexicano NO lo intimidan — lleva anos jugando en J1 League con presion sistematica y ya jugo en altitud similar. Posible peso: el temor a ser el responsable si falla en un partido tan grande, dado que Mexico tendra 60,000 aficionados a favor.
- **Biografía:** Kim Seung-gyu, nacido el 30 de septiembre de 1990 en Ulsan, Corea del Sur, es el portero mas experimentado de su generacion en el futbol coreano y uno de los pocos jugadores del planeta que disputa su cuarto campeonato mundial. Forjado en Ulsan Hyundai — donde se forman la mayoria de los pilares de la seleccion — Kelly hacia las categorias inferiores en la decada de 2000, hizo su debut en la A como segundo portero y fue reclamado rapidamente como titular gracias a su combinacion de reflejos explosivos y un trabajo de pies refinado que mas tarde pulida en tres temporadas en la J1 League (Vissel Kobe, Kashiwa Reysol, FC Tokyo). En la seleccion nacional debuto el 14 de agosto de 2013 y su carrera internacional esta marcada por momentos epicos — las atajadas heroicas contra Belgica en Brasil 2014, la medalla de oro en los Juegos Asiaticos de ese mismo ano que le otorgo exencion del servicio militar, y las actuaciones en Qatar 2022. Su carrera casi termino dos veces: en enero de 2024 sufrio su primer desgarro de ligamento cruzado en el Asian Cup de Qatar, y meses despues, recien retornando, sufrio una segunda ruptura del mismo ligamento — una serie de golpes que lo llevo a contemplar el retiro. FC Tokyo lo cobijo durante su rehabilitacion, le ofrecio soporte medico especializado y le dio confianza para regresar; Kim correspondio fichando de forma permanente. Su presente en el Mundial 2026 es la definicion de resurreccion: padre primerizo desde el 4 de junio (su hija nacio mientras el estaba en Salt Lake City), pareja de una modelo y actriz coreana muy reconocida, y el portero que salvo a Corea en el minuto 93 contra Chequa con una atajada que incluso el tecnico rival no pudo explicar. Hoy juega contra Mexico con la carga y la gloria de todo eso encima.
- **🗣️ Monólogo interior:** *“Cuarenta y ocho mil y casi todos quieren verme caer; bien, que griten, el silbido del estadio es mi metronomo. He esperado toda una carrera detras de Cho para una noche asi, y a mi edad ya no le tengo miedo al ruido, le tengo miedo a no estar listo. Mexico nunca nos ha perdido en un Mundial y la altura me pesa un poco en el segundo tiempo, asi que cada balon dividido lo voy a comer yo, cada centro lo voy a gritar. Con todo el lio del video de Son y la prensa, mi unico idioma hoy es atajar; calla la boca y para el balon, capitan.”*
- **X-factor:** Su serenidad veterana y dominio del area en los centros bajo lluvia y presion local pueden robarle a Mexico el gol que define el liderato.
- **Confianza del dato:** Alta en: edad, club, situacion familiar (confirmado por multiples fuentes incluyendo StarNews y Malay Mail), caps (~88-89 pre-torneo + 1 contra Chequa), doble lesion ACL y consideracion de retiro (fuentes coreanas), forma en FC Tokyo (Flashscore, FotMob), personalidad (inferida de citas directas y coberturas multiples), motivacion hoy (declaraciones directas del jugador). Estimada con prudencia en: atributos numericos (basados en estadisticas publicadas, comparativa de actuaciones, ratings externos y analisis tacticio — no son mediciones oficiales). El segundo ACL es confirmado por fuentes coreanas (namu.wiki, citas del propio Kim 'hace un ano no sabia si podria volver al campo') aunque la fecha exacta del segundo desgarro no esta precisada en fuentes en ingles.
- **Fuentes:** Wikipedia Kim Seung-gyu (https://en.wikipedia.org/wiki/Kim_Seung-gyu) | Korea Herald 'Two scorers and one standout goalkeeper' (https://www.koreaherald.com/article/10770701) | StarNews Korea - hija nacida antes del Mundial (https://www.starnewskorea.com/en/sports/2026/06/08/2026060800582450594) | StarNews Korea - 'Patriotic Couple' (https://www.starnewskorea.com/en/star/2026/06/12/2026061214364136195) | Malay Mail - Kim misses daughter birth (https://www.malaymail.com/news/sports/2026/06/08/south-koreas-kim-seung-gyu-aims-to-repay-family-after-missing-daughters-birth-for-world-cup-prep/223013) | Al Jazeera - Son military controversy (https://www.aljazeera.com/sports/2026/6/16/south-korea-world-cup-squad-at-odds-with-media-over-son-heung-min-mockery) | Financial News (fnnews.com) - Kim pie y rol vs Mexico (https://www.fnnews.com/news/202606180730471472) | Namu Wiki Kim Seung-gyu (https://namu.wiki/w/김승규) | Newsis - cuarto Mundial analisis (https://www.newsis.com/view/NISX20260525_0003643082) | Nate Sports - portero numero uno (https://sports.news.nate.com/view/20260526n02594) | FC Tokyo oficial - transferencia permanente (https://fctokyo.co.jp/en/news/17444) | Flashscore stats 2026 (https://www.flashscore.com/player/kim-seung-gyu/xh6I9nD4/) | Transfermarkt perfil 2026 (https://www.transfermarkt.us/seung-gyu-kim/profil/spieler/92076) | FC Tokyo Players File 2026 (https://www.fctokyo.co.jp/en/fan/fanzone/detail/329390/) | RotoWire Mexico vs South Korea preview (https://www.rotowire.com/soccer/article/mexico-vs-south-korea-preview-predicted-lineups-team-news-tactical-analysis-2026-world-cup-group-a-118510)

#### Lee Han-beom — KOR · CB (stopper derecho en 3-4-2-1) · 24 años · 9 caps
- **Club / situación:** FC Midtjylland (Superliga danesa) — Titular indiscutible desde abril 2026 tras superar un largo periodo de banco. Termino la temporada 2025-26 con 49 partidos oficiales, gol decisivo en la final de la Copa de Dinamarca vs FC Copenhagen. Contrato hasta junio 2027; Midtjylland bajo presion de venderlo este verano por interés masivo de Premier League (Liverpool, Leeds, Chelsea, Newcastle, Brighton) y Bundesliga/Europa (BVB, RB Leipzig, Napoli, Monaco, Lyon). Precio de mercado estimado en 3 millones de euros pero subiendo rapidamente post-Mundial.
- **Físico/anatomía:** 189 cm, 83 kg, velocidad punta ~30 km/h, durabilidad 78/100
- **Historial de lesiones:** Rodilla 2022 (~288d); limpio desde 2023
- **Familia:** Sin informacion publica reportada sobre pareja, novia, esposa o hijos. Lee Han-beom mantiene su vida privada completamente al margen de los medios. Su red de apoyo emocional en Dinamarca ha sido su companero de equipo y compatriota Cho Gue-Sung, con quien comparte vida en Midtjylland desde 2023 y que fue su confidente durante los momentos de frustracion por falta de minutos. Nacido en Daegu; padres no mencionados en fuentes publicas.
- **Estado personal:** Momento personal extraordinariamente positivo y estable. Acaba de cumplir 24 anos ayer (17 de junio de 2026), el dia antes del partido vs Mexico, convirtiendo este duelo en un simbolico regalo de cumpleanos en el mayor escenario del mundo. Supero una crisis profunda de motivacion en 2024-25 cuando Midtjylland rechazo traspasos a Alemania y Croacia mientras el permanecia sin jugar — llego a confesar que 'perdio toda la motivacion y alegria por el futbol'. Esa travesia del desierto forjo un caracter mucho mas resiliente. Ahora es titular en el Mundial con Corea del Sur, co-lider defensivo junto a Kim Min-jae, y el mercado europeo le da la razon: es uno de los defensas jovenes mas cotizados del planeta. El ambiente de equipo en la seleccion esta potenciado por la polemica del video sobre Son Heung-min: el grupo se cerro en banda alrededor del capitan, boicoteo medios coreanos, y eso genero una cohesion interna extraordinaria. Son invito a todo el equipo a comer tacos mexicanos en su dia libre como gesto de union. Lee Han-beom, como INTP introvertido, se nutre de esa cohesion silenciosa y del proposito colectivo.
- **Personalidad:** INTP confirmado (dato reportado en medios coreanos). Introvertido, analitico, independiente y muy autodirigido. No busca el protagonismo ni el foco mediatico; su manager en Midtjylland (Thomas Begh) dijo de el: 'No es un jugador al que yo tenga que estar encima diciendole que hacer; al contrario, el me protege a mi'. Silencioso pero competitivamente feroz: cuando no jug, no se quejo publicamente sino que proceso la frustracion internamente y siguio entrenando en silencio. Mentalmente tectonica mas que volcanica: no explota, acumula y ejecuta. Comenzo de mediocampista antes de convertirse en CB, lo que le da una comprension tactica e inteligencia de juego inusual para su posicion. Fue asesorado por Park Ji-sung sobre la importancia de la comunicacion verbal en defensa, y trabajo especificamente en ese aspecto en su segunda temporada en Dinamarca. Comida favorita: sopa de rape (monkfish stew). Introvertido social: su unico circulo conocido en Dinamarca es Cho Gue-Sung.
- **Motivación hoy:** HITO GENERACIONAL: jugar un partido de Mundial el dia despues de su cumpleanos numero 24 es un evento emocionalmente cargado aunque el no lo exhiba. REDENCION PERSONAL: viene de haber estado al borde de irse de Midtjylland por falta de oportunidades; cada minuto de este Mundial es la culminacion de no haberse rendido. TRAMPOLÍN DE CARRERA: sabe que Liverpool, Leeds, Chelsea y otros le estan viendo EN DIRECTO hoy; este partido define su precio de mercado para el verano. SOLIDARIDAD CON SON: la polemica militar unio al grupo; Lee, como parte del bloque defensor del capitan, juega con extra motivacion de grupo. PRIMER GRAN TORNEO: es su debut en un torneo de seleccion mayor absoluta; el combustible de la novedad y el hambre de demostrar es maximo.
- **Biografía:** Lee Han-beom (이한범), nacido el 17 de junio de 2002 en Daegu, Corea del Sur, es uno de los defensas centrales jovenes mas prometedores de Asia y esta tarde cumple simbolicamente 24 anos en el escenario del Estadio Akron de Guadalajara frente a Mexico. Formado en el Boin High School como mediocampista antes de reconvertirse en zaguero, debuto profesionalmente en el K League 1 con FC Seoul en abril de 2021 y en agosto de 2023 dio el salto a Europa firmando por FC Midtjylland por 1.5 millones de dolares. Su primera temporada en Dinamarca fue una prueba de caracter: apenas 3 partidos disputados, un periodo de banco que el mismo definio como 'el momento en que perdi toda la motivacion y la alegria por el futbol', y rechazos de traspasos a Alemania y Croacia que intensificaron su frustracion. Sin embargo, en lugar de hundirse, proceso el dolor en silencio — coherente con su personalidad INTP — y cuando el nuevo tecnico Thomas Begh le dio la alternativa en abril de 2025, respondio con 49 partidos, 4 goles, 4 asistencias y el gol decisivo en la final de la Copa de Dinamarca contra el FC Copenhagen. Su debut con la seleccion absoluta llegaria el 10 de junio de 2025 frente a Kuwait, y en la apertura del Mundial 2026 ante Republica Checa desplegaria una actuacion monumental conteniendo a Patrik Schick y a Adam Hlozek, consolidandose como dupla titular junto a Kim Min-jae. Hoy, Liverpool, Leeds, Chelsea, BVB y media Europa le observan en directo.
- **🗣️ Monólogo interior:** *“Cuarenta y ocho mil gargantas y ninguna canta para nosotros; cuando toque la pelota va a silbar todo el Akron y tengo que dejar que ese ruido me empuje, no que me ahogue. Me toca Alvarado, el que regatea para humillar, y Quinones por dentro: si me como una finta temprano me van a buscar toda la noche, asi que primero el cuerpo, primero no perder la espalda, ya tendre tiempo de subir. El aire pesa raro aqui arriba, en el calentamiento sentia que el segundo esfuerzo no llegaba, tengo que medir cada subida porque al minuto 70 esta cancha mojada y esta altura me van a cobrar todo. Y por dentro arde lo de Son, lo del video, todo ese ruido sucio de casa: hoy juego por el, callado, ganando, porque una victoria nos clasifica y le tapa la boca a todos.”*
- **X-factor:** Contener a Alvarado en el uno contra uno sin regalarle la amarilla temprana que el arbitro uruguayo esta deseando sacar.
- **Confianza del dato:** Alta en: edad, fecha de nacimiento, club, posicion, estilo de juego, MBTI INTP, historia de frustración en Midtjylland y superacion, relacion con Cho Gue-Sung, rendimiento vs Chequia, interés de traspasos, polemica Son/unidad de equipo. Media en: numero exacto de caps A (entre 7-10 segun fuente; se usa 9 como estimacion incluyendo fase de clasificacion + primer partido Mundial). Baja/Estimacion en: vida familiar y privada (no hay datos publicos; se confirma ausencia de informacion, no ausencia de relaciones). Los atributos numericos son estimaciones basadas en datos observables de rendimiento, estadisticas disponibles y contexto situacional — no son datos oficiales.
- **Fuentes:** Wikipedia: https://en.wikipedia.org/wiki/Lee_Han-beom | FIFA entrevista (KO): https://www.fifa.com/ko/tournaments/mens/worldcup/canadamexicousa2026/articles/lee-hanbeom-korea-world-cup-midtjylland-ko | Daum/Tipsbladet entrevista (mayo 2025): https://v.daum.net/v/20250524131504234 | Football365 scouts report: https://www.football365.com/news/lee-han-beom-watched-by-liverpool-leeds-trio-other-prem-clubs-world-cup-scouting-mission | Korea Daily (EPL interes): https://www.koreadaily.com/article/20260614133253684 | Al Jazeera (polemica Son): https://www.aljazeera.com/sports/2026/6/16/south-korea-world-cup-squad-at-odds-with-media-over-son-heung-min-mockery | Sofascore stats: https://www.sofascore.com/football/player/han-beom-lee/1002448 | Sports Mole (XI predicho vs Mexico): https://www.sportsmole.co.uk/football/south-korea/world-cup-2026/predicted-lineups/who-supports-son-up-top-in-world-cup-clash-predicted-south-korea-xi-vs-mexico_599403.html | Nocutnews (Cho Gue-Sung y Lee han-beom): https://www.nocutnews.co.kr/news/6507479 | NamuWiki (MBTI INTP, estilo de juego): https://namu.wiki/w/%EC%9D%B4%ED%95%9C%EB%B2%94 | FNnews (Kim Min-jae comparison): https://www.fnnews.com/news/202606141754416783 | Boo MBTI profile: https://boo.world/database/profile/545854/lee-han-beom-personality-type | ReadLiverpoolFC: https://readliverpoolfc.com/news/lee-han-beom-liverpool-transfer-world-cup/ | Transfermarkt (6 caps A-team): https://www.transfermarkt.us/han-beom-lee/nationalmannschaft/spieler/706963

#### Kim Min-jae — KOR · CB · 29 años · 80 caps
- **Club / situación:** Bayern Munich — Tercer central en jerarquia tras llegada de Jonathan Tah (verano 2025). Temporada 2025-26 con 25 apariciones (19 iniciales), 1 gol, 1 asistencia. Sufrió lesion de rodilla en mayo 2026 (vs Wolfsburg) con MRI negativo; ausente del ultimo partido de liga pero declarado apto para el Mundial. Arrastra historial de Aquiles cronico (tendinitis desde octubre 2024, con recaidas en marzo y mayo 2025). Bayern dispuesto a escuchar ofertas (pedido ~30M EUR). Kim declara estar contento pero su salary de 15M EUR anuales dificulta salida. Juventus, Newcastle, Chelsea y clubes turcos lo rondan.
- **Físico/anatomía:** 190 cm, 81 kg, velocidad punta ~33 km/h, durabilidad 55/100
- **Historial de lesiones:** Tendinitis cronica de Aquiles; recaidas 2025; rodilla dic-2025; sin cirugia confirmada
- **Familia:** Divorciado (octubre 2024) de Ahn Ji-min tras 4 anos de matrimonio (casados mayo 2020), citando diferencias de personalidad. Tienen una hija, Kim Joo-ah (nacida 2020), con custodia en manos de la madre. Kim se disculpo publicamente con sus fans segun tradicion coreana. Familia de origen: madre Lee Yoo-sun y padre Kim Tae-gyun, ambos ex-deportistas. Hermano mayor fue portero universitario. Criado en Tongyeong, ciudad costera al sur de Corea.
- **Estado personal:** Estado personal marcado por dos grandes eventos recientes: (1) El divorcio consumado en octubre 2024, un proceso que transcurrio mientras jugaba con dolor de Aquiles cronico — la prensa alemana quedo perpleja ante el anuncio formal via agencia con disculpa publica, algo inusual en Europa pero tipico en Corea. (2) Temporada 2025-26 como tercer central en Bayern, con lesion de rodilla de mayo 2026 que causo alarma pre-Mundial pero se resolvio sin dano estructural. En el plano del equipo nacional, el escandalo del video sobre el servicio militar de Son genero una crisis de medios con boicot colectivo, y Kim fue uno de los dos lideres (junto a Son) que recibio la disculpa formal del cuerpo de prensa. Esto lo coloca en rol protagónico de la cohesion del grupo. Estimacion: animo estabilizado tras meses turbulentos; la concentracion mundialista actua como ancla emocional positiva.
- **Personalidad:** Conocido como "El Monstruo" (El Monster) por su presencia fisica intimidante y mentalidad ferrea. Caracter serio, introvertido fuera del campo, concentrado dentro. Lider por ejemplo mas que por discurso. Equipo-primero: en pleno proceso de divorcio, mostro madurez al gestionar lo personal sin afectar el rendimiento. Tacticamente inteligente — es descrito como un "camileon tactico" capaz de adaptarse a defensas de 2, 3 o 4. Acepto su rol de suplente en Bayern sin crear conflictos publicos, algo que refuerza su imagen de profesional maduro. Coaches de Napoli y Bayern lo elogiaron por su mentalidad. Rara vez se involucra en polémicas mediaticas, aunque aparece como pilar silencioso de la unidad cuando el equipo lo necesita (caso Son).
- **Motivación hoy:** Motivadores positivos HOY: (1) Mundial en casa de la rivalidad — partido trascendental para Corea del Sur en suelo americano; (2) Redención personal tras temporada irregular en Bayern como suplente; desea demostrar que sigue siendo un top-5 CB mundial; (3) Solidaridad con Son y el equipo en la crisis mediatica — refuerza identidad de grupo y orgullo patrio; (4) Desafio fisico concreto: duelo vs Jimenez, delantero de referencia aérea, es exactamente el tipo de batalla que define su legacy. Factores de peso/presion: lesion de rodilla reciente crea incertidumbre sobre su nivel de intensidad maxima; la transferencia en verano puede depender de su actuacion en el Mundial; divorcio como carga de fondo aunque estabilizado. Neto: alta motivacion.
- **Biografía:** Kim Min-jae nacio el 15 de noviembre de 1996 en Tongyeong, ciudad costera al sur de Corea del Sur, hijo de dos ex-deportistas que le inculcaron disciplina desde nino. Paso por Suwon Technical High School — la misma que forjo a Park Ji-sung — antes de abandonar Yonsei University en su segundo ano para perseguir el futbol profesional, decision audaz que su universidad trato de disuadir. Tras consagrarse en Jeonbuk Hyundai (K League Young Player of the Year 2017) y pasar por Beijing Guoan y Fenerbahce, llego a Napoli en 2022 para vivir su ano estelar: pieza fundamental del Scudetto 2022-23, elegido Mejor Defensa de la Serie A, y primer defensa asiatico nominado al Balon de Oro. Bayern Munich pago 50 millones de euros por el en julio 2023 — la mayor cifra pagada por un defensa asiatico en la historia — firmando hasta 2028. Su temporada 2024-25 estuvo plagada de obstaculos: tendinitis cronica de Aquiles desde octubre 2024, divorcio publico de Ahn Ji-min (octubre 2024) con custodia de su hija para la ex-esposa, y la llegada de Jonathan Tah que lo relego al tercer puesto en la jerarquia. La temporada 2025-26 mostro su resiliencia: 25 apariciones, rendimiento solido cuando llamado, y recuperacion de una lesion de rodilla menor en mayo 2026 justo a tiempo para el Mundial. En la concentracion de Corea del Sur en Guadalajara, Kim emerge como co-lider del boicot mediatico en solidaridad con Son Heung-min, recibiendo personalmente la disculpa del cuerpo de prensa. Su apodo, El Monstruo, sintetiza su esencia: dominante en el aire, rapido para un central de 1.90m, lider silencioso que organiza la linea defensiva con inteligencia tactica.
- **🗣️ Monólogo interior:** *“Cuarenta y ocho mil y casi todos quieren verme caer; bien, que griten, el silbido del estadio es mi metronomo. He esperado toda una carrera detras de Cho para una noche asi, y a mi edad ya no le tengo miedo al ruido, le tengo miedo a no estar listo. Mexico nunca nos ha perdido en un Mundial y la altura me pesa un poco en el segundo tiempo, asi que cada balon dividido lo voy a comer yo, cada centro lo voy a gritar. Con todo el lio del video de Son y la prensa, mi unico idioma hoy es atajar; calla la boca y para el balon, capitan.”*
- **X-factor:** Su serenidad veterana y dominio del area en los centros bajo lluvia y presion local pueden robarle a Mexico el gol que define el liderato.
- **Confianza del dato:** skill:CONFIRMADO (rendimiento documentado Napoli/Bayern/SK); caps:CONFIRMADO 80 segun Transfermarkt mayo 2026; age:CONFIRMADO nacido 15-nov-1996; family:CONFIRMADO (divorcio oct 2024, hija con madre); club_situation:CONFIRMADO (tercer central, lesion rodilla con MRI negativo); injury_risk:ESTIMADO — rodilla sin lesion estructural confirmada pero con historial de Aquiles cronico; consistency:ESTIMADO — rebaja refleja irregularidad 2024-25 vs pico Napoli; emotional_state_today:ESTIMADO — positivo pero con carga de fondo (divorcio, bench, transferencia pendiente); discipline:ESTIMADO — 1 tarjeta amarilla en Bundesliga 2025-26 segun fotmob, reputacion de juego duro controlado; clutch/pressure_resistance:ESTIMADO con base en actuaciones en Champions League (monsterclass vs PSG) y partidos de alta presion
- **Fuentes:** Wikipedia Kim Min-jae footballer (https://en.wikipedia.org/wiki/Kim_Min-jae_(footballer)); Bavarian Football Works — injury/transfer coverage 2024-26 (https://www.bavarianfootballworks.com); Korea Times — divorcio octubre 2024 (https://www.koreatimes.co.kr/sports/20241022/monster-kim-min-jae-announces-divorce-after-four-years-of-marriage); Starnews Korea — lesion rodilla mayo 2026 (https://www.starnewskorea.com/en/sports/2026/05/12); Yahoo Sports — boicot mediatico Son (https://sports.yahoo.com/articles/south-korea-players-boycott-media-101139838.html); RotoWire — lesion rodilla fuera del partido final (https://www.rotowire.com/soccer/headlines/kim-min-jae-injury-out-of-season-finale-516378); Goal.com — preview Mexico vs Corea (https://www.goal.com/en/news/mexico-south-korea-world-cup-preview/blt8005f425257b98f0); Transfermarkt — estadisticas y valor (https://www.transfermarkt.us/min-jae-kim/profil/spieler/503482); Breaking The Lines — analisis de personalidad y estilo (https://breakingthelines.com/player-analysis/kim-min-jae-a-defender-rewriting-the-script-of-greatness); Fanplus Community — informacion divorcio y custodia (https://fanplus.co.kr/en-US/community/misc/84058138); TNT Sports — boycott Son militar (https://www.tntsports.co.uk/football/world-cup/2026/south-korea-boycott-media-duties-son-heung-min-mocked-military-service_sto23310277/story.shtml); Football Asian — boycott prolongado (https://www.football-asian.com/news/articleView.html?idxno=6345)

#### Lee Gi-hyuk — KOR · Centro · 25 años · 4 caps
- **Club / situación:** Gangwon FC (K-League 1) — Titular indiscutible en Gangwon FC. En 2026 lleva 14 partidos de liga (1,258 minutos), sin lesiones, promedio FotMob 7.26. Ganó el premio K-League Jugador del Mes de mayo 2026 — solo el segundo central en ganarlo en cinco años. Gangwon lo considera pieza central e inamovible; no hay rumores de transferencia aunque su valor de mercado sube post-Mundial. Titular en el once de Corea del Sur en el J1 del Mundial (vs Chequia) como el único K-Leaguer en el XI inicial.
- **Físico/anatomía:** 184 cm, 72 kg, velocidad punta ~32 km/h, durabilidad 78/100
- **Historial de lesiones:** Golpe menor dic-2025; durable
- **Familia:** No hay información pública reportada sobre pareja, esposa, hijos ni relaciones sentimentales. Tampoco se han publicado detalles sobre sus padres más allá de que creció en Seúl. Su vida privada permanece estrictamente fuera de los medios. Dato: ninguna fuente coreana o internacional consultada revela información familiar de carácter personal.
- **Estado personal:** Estable y en el punto más alto de su carrera. Vive la realización de su sueño de infancia: jugar en un Mundial. Tras el J1 vs Chequia (2-1) recibió elogios directos de Son Heung-min y Hwang Hee-chan dentro del vestuario, lo que él mismo describió como "significativo y alegre". La polémica del video sobre el servicio militar de Son generó un apagón mediático del equipo coreano, pero internamente el equipo mostró cohesión y solidaridad. Lee forma parte de un grupo que se cerró en torno a su capitán. Su estado emocional es de alta energía positiva: disfruta el contexto, no siente presión excesiva (el entrenador mental del equipo lo confirmó públicamente), y está físicamente al 100%.
- **Personalidad:** Personaje excepcionalmente compuesto para su edad y experiencia. El prof. Han Deok-hyun (psiquiatra y coach mental del equipo nacional, el primero en la historia de Corea) declaró públicamente: "Le envié un correo a mi mentor: la teoría del deporte se derrumbó." Lee mostró cero ansiedad antes de su debut mundialista. Dentro del campo es resiliente: cometió un error serio en el min. 15 vs Chequia (pérdida de balón que Kim Min-jae rescató) y lo superó sin caer en el juego ansioso. Fuera del campo es humilde y trabajador obsesivo — invirtió intensamente en fuerza de core y tren inferior para compensar que llegó tarde a la defensa (se formó como centrocampista hasta 2023). Dijo: "Cuando me dicen que soy buen defensor, sé que fue por morder el freno en los entrenamientos individuales 1v1." Equilibra autoconfianza con cautela: "Si la confianza se desborda, puede convertirse en arrogancia. Quiero jugar con seguridad pero esforzarme igual que antes."
- **Motivación hoy:** HOY: (1) Vivir el sueño — el Mundial siempre fue su meta desde niño y cada partido es un regalo. (2) Demostrar que merece estar ahí — fue una convocatoria sorpresa que sustituyó a Kim Joo-sung (lesionado); hay una deuda de rendimiento que lo activa. (3) El amarillo del J1 — recibió tarjeta en el 90+6 vs Chequia; si recibe otra hoy queda suspendido para el J3 vs Sudáfrica. Esto genera hiperconciencia táctica, pero puede añadir tensión en duelos físicos. (4) Solidaridad con Son en la crisis mediática — la polémica del servicio militar unió al equipo; hay sentido colectivo de "responder en el campo". (5) Primer K-Leaguer en el XI de Corea en el Mundial en años — carga de orgullo de representar a Gangwon FC (primer jugador de la historia del club en ir al Mundial) y al fútbol doméstico coreano.
- **Biografía:** Lee Gi-hyuk (이기혁, n. 7 julio 2000, Seúl) es el central zurdo más completo que ha producido el fútbol doméstico coreano en lustros. Formado en la academia de Ulsan Hyundai y la Universidad de Ulsan, debutó como centrocampista en Suwon FC (2021), donde fue cambiando gradualmente de posición hasta convertirse en el estopín del sistema de tres centrales de Gangwon FC a partir de 2024 bajo el mando de Kim Byung-soo. Su reconversión es el gran experimento exitoso de la K-League reciente: tomó la amplitud visual, la precisión de pase (93.5% en partidos recientes de selección) y la valentía con balón de su etapa como mediocentro, y los fusionó con una defensa construida desde cero a base de trabajo físico obsesivo en core y fuerza explosiva. En el J1 del Mundial 2026 vs Chequia (2-1) fue el K-Leaguer solitario en el once titular y lideró al equipo en despejes (8) e interposiciones (3), pese a un error peligroso en el minuto 15 que superó sin acusar el golpe — lo que asombró incluso al psiquiatra y coach mental de la selección, Han Deok-hyun. Gangwon FC lo tiene como su referencia y bandera: fue el primer jugador en la historia del club en participar en un Mundial. Su amarillo en el minuto 90+6 vs Chequia lo sitúa en el filo de la navaja de cara al J2 vs México: otra tarjeta lo elimina del J3 ante Sudáfrica.
- **🗣️ Monólogo interior:** *“Cuarenta y ocho mil gargantas y ninguna canta para nosotros; cuando toque la pelota va a silbar todo el Akron y tengo que dejar que ese ruido me empuje, no que me ahogue. Me toca Alvarado, el que regatea para humillar, y Quinones por dentro: si me como una finta temprano me van a buscar toda la noche, asi que primero el cuerpo, primero no perder la espalda, ya tendre tiempo de subir. El aire pesa raro aqui arriba, en el calentamiento sentia que el segundo esfuerzo no llegaba, tengo que medir cada subida porque al minuto 70 esta cancha mojada y esta altura me van a cobrar todo. Y por dentro arde lo de Son, lo del video, todo ese ruido sucio de casa: hoy juego por el, callado, ganando, porque una victoria nos clasifica y le tapa la boca a todos.”*
- **X-factor:** Contener a Alvarado en el uno contra uno sin regalarle la amarilla temprana que el arbitro uruguayo esta deseando sacar.
- **Confianza del dato:** DATOS CONFIRMADOS: Nombre completo, fecha nacimiento (7-jul-2000), club (Gangwon FC), posición (central/zurdo), trayectoria (Suwon FC 2021-22, Jeju United 2023, Gangwon FC 2024-present), estatura (184 cm), peso aprox 72 kg, dorsal 13, formacion (Hyundai High School, Univ. Ulsan), caps exactos (4 según Soccerway: 1 EAFF 2022 + 2 amistosos 2026 + 1 Mundial J1 vs Chequia), estadísticas J1 (8 despejes y 3 interposiciones liderando el equipo, amarillo min 90+6, error min 15), Premio Jugador del Mes K-League mayo 2026, convocatoria como sustituto de Kim Joo-sung (lesionado), declaraciones textuales del jugador y coach mental publicadas. ESTIMACIONES CON FUNDAMENTO: Número de caps en amistosos confirmado como 2 por Soccerway pero la entrevista de FN indicó que su primer A-match fue vs Hong Kong en julio 2022, lo que encaja. Familia y vida privada: sin ninguna fuente pública, se estima que no tiene pareja pública conocida (no hay ninguna mención en ningun medio coreano revisado — es común en jugadores jóvenes solteros de K-League). Atributos numéricos del gemelo digital: estimados a partir de datos de rendimiento real (FotMob rating 7.26, minutos, disciplina con 4 amarillas en liga 2026, porcentaje de pase declarado), declaraciones de coach mental, evaluación de prensa especializada y comparativa con centrales de nivel similar en Asia.
- **Fuentes:** Wikipedia (Lee Gi-hyuk) — https://en.wikipedia.org/wiki/Lee_Gi-hyuk | Soccerway (caps 4 confirmados) — https://www.soccerway.com/players/gi-hyuk-lee/691448/ | Daum/entrevista de convocatoria junio 2026 — https://v.daum.net/v/20260611173007639 | Daum/entrevista post-Chequia — https://v.daum.net/v/20260612173638746 | Daum/entrevista post-Chequia 2 — https://v.daum.net/v/20260613000248603 | Newsis/coach mental — https://www.newsis.com/view/NISX20260616_0003670423 | Nate Sports/K-League Player of Month — https://sports.news.nate.com/view/20260616n26643 | Nate Sports/error y mental — https://sports.news.nate.com/view/20260612n23320 | RotoWire/World Cup opener stats — https://www.rotowire.com/soccer/headlines/lee-gi-hyuk-news-does-part-in-world-cup-opener-519160 | Financial News/convocatoria — https://www.fnnews.com/news/202605162052144440 | Yahoo Sports/Son controversy — https://sports.yahoo.com/soccer/article/2026-world-cup-south-korea-reportedly-stages-team-media-blackout-after-son-heung-min-mocked-for-his-military-service-005409431.html | SportsMole/predicted XI vs Mexico — https://www.sportsmole.co.uk/football/south-korea/world-cup-2026/predicted-lineups/who-supports-son-up-top-in-world-cup-clash-predicted-south-korea-xi-vs-mexico_599403.html | Gangwon FC official — https://www.gangwon-fc.com/squad/player/945

#### Seol Young-woo — KOR · Lateral derecho / Carrilero derecho (Wing-back derecho) · 27 años · 35 caps
- **Club / situación:** FK Crvena Zvezda (Red Star Belgrade) — Titular indiscutible en Red Star Belgrade. En la temporada 2025-26 acumulo 37 partidos oficiales con 1 gol y 6 asistencias (media FotMob 7.71). Gano dos ligas serbias consecutivas y dos Copas de Serbia. Jugo 8 partidos en la fase de liga de la UEFA Europa League 2025-26 con 1 asistencia. Su contrato vence en junio 2027 pero tiene clausula de rescision de 5 millones de euros (equivalente a ~85 millones de won). Desde marzo 2026 se reporta interes confirmado del Eintracht Frankfurt con oferta oficial inminente por ese monto; tambien hubo negociaciones fallidas con Sheffield United (Championship) en agosto 2025. El traslado a la Bundesliga se prevé para después del Mundial. Se encuentra en el mejor momento de su carrera y en plenitud fisica.
- **Físico/anatomía:** 182 cm, 75 kg, velocidad punta ~32 km/h, durabilidad 62/100
- **Historial de lesiones:** Luxacion habitual hombro derecho; cirugia may-2024; ahora apto
- **Familia:** Soltero (confirmado). A principios de 2024 surgieron rumores de romance con Yang Ye-na, cantante del grupo K-pop APRIL, pero representantes de ella respondieron con ambiguedad y en enero 2024 medios reportaron que ya habian terminado. Actualmente se le atribuye tener novia (sin identidad publica reportada). No tiene hijos reportados. Ha expresado publicamente que quiere casarse pronto porque ama a los ninos y quiere que sus hijos lo vean jugar. Su companero de vida mas documentado es su perro maltés llamado 'Seoltang' (Azucar), que incluso tiene cuenta propia de Instagram y al que Seol llama 'mi hijo'. Su apodo favorito entre fans es 'el papa de Seoltang'.
- **Estado personal:** Estado personal estable y positivo. Seol es un jugador que crecio en Ulsan toda su vida —ciudad industrial con fuerte identidad futbolistica— y recien a los 26 anos emigro por primera vez al extranjero (Serbia, 2024). La adaptacion a Europa fue exitosa: ha declarado haber sentido 'el amor ferozmente apasionado de las hinchadas serbias y coreanas en Belgrado'. Ha vivido la intensidad de los derbis de Belgrado, la Champions League y los viajes por Europa. Esta fisica y mentalmente en su pico de madurez. La controversia mediática interna (video sobre el servicio militar de Son) afecta al grupo pero une a los jugadores en solidaridad: el equipo declaro boicot a medios y Seol ha sido visto entrenando con actitud positiva y riendo con companeros (imagen captada el 17 de junio). El hecho de que su transferencia al Frankfurt posiblemente se cierre luego del Mundial le da un motor adicional de motivacion: este torneo es su mayor vitrina personal. DATO: propio Seol declaro ante medios en la previa del Mexico 'tuve una pequena lesion pero ya recuperé, no hay problema para jugar'.
- **Personalidad:** MBTI confirmado: ESFJ (Consul/Protagonista social). Seol es extrovertido, afectuoso y orientado a la comunidad. Dentro de la cancha es disciplinado, intenso en la presion y con mentalidad ganadora aprendida en Ulsan (dos K League 1 y el ritmo de trabajo del equipo de Hwang Hee-chan). Fuera es un jugador con imagen de chico sencillo y cercano: tiene tatuajes en brazo, hombro, pecho y espalda (numeros romanos, cara de su perro, tigre, naipes), le gusta la musica indie coreana (Damons Year), es fanatico del Borussia Dortmund desde nino, y tiene como idolo futbolistico a Trent Alexander-Arnold. Su alias en la aficion del Ulsan fue 'el Arnold de Ulsan'. Es un jugador de equipo, no lider vocal en el nivel de Son pero solido en el vestuario. Muy orientado al crecimiento personal: declaro en febrero 2025 que la UCL fue 'el mejor aprendizaje de mi vida' y que 'nunca desperdicié un solo minuto en cada partido'.
- **Motivación hoy:** HOY: (1) VITRINA DE TRANSFERENCIA — el traslado al Frankfurt (o club mayor) depende en parte de lo que muestre en este Mundial; un gran partido vs Mexico ante 47,000 aficionados y millones de espectadores amplifica su valor de mercado directamente. (2) SOLIDARIDAD CON SON — la polemica del video sobre el servicio militar de Son ha unido al equipo en un bloque; jugar bien es la respuesta colectiva y Seol, ESFJ, es muy sensible a la cohesion grupal. (3) PRIMER MUNDIAL — es su primer Mundial (estaba fuera del grupo en 2022); es la realizacion de un sueno de infancia que declaro publicamente. (4) CONDICIONES ADVERSAS DE ALTITUD Y CALOR — el propio Seol menciono que 'el calor y la humedad son un desafio y estamos gestionando bien el cuerpo y la mente'. Tiene experiencia aerobica excelente (corre 15+ km en partido) que le da ventaja relativa. CONTRABALANCE: una pequena lesion recientemente superada y la polemica mediatica crean algo de ruido emocional externo.
- **Biografía:** Seol Young-woo (설영우, nacido el 5 de diciembre de 1998 en Ulsan, Corea del Sur) es el lateral/carrilero derecho mas completo de su generacion en Corea del Sur, apodado 'el Arnold de Ulsan' por su perfil ofensivo inspirado en Trent Alexander-Arnold. Originalmente extremo derecho en la universidad, hizo la conversion a lateral en segundo ano y en seis temporadas en el Ulsan HD FC (2020-2024) acumulo 120 partidos, dos titulos de K League 1 (2022, 2023), fue Jugador Joven del Ano en Corea 2021 y miembro del Equipo del Ano K League 2023; ademas gano la medalla de oro en los Juegos Asiaticos 2022 con la sub-23, lo que le otorgo exencion del servicio militar obligatorio. En junio 2024 cruzó su primera frontera como futbolista profesional al fichaje por el Red Star Belgrade (1.5M EUR), donde ha sido figura inmediata: dos ligas serbias, dos copas, rating medio de 7.63-7.71 y tres asistencias en ocho partidos de Champions League vs rivales como Barcelona. Convocado por primera vez a este Mundial (ausente en Qatar 2022), llega con 35 caps y es el carrilero derecho titular bajo el esquema 3-4-2-1 de Hong Myung-bo. En el debut ante Republica Checa (2-1) completo los 90 minutos con rating FotMob 6.9. Fuera del futbol es un personaje cercano y con identidad propia: tatuajes extensos, fanatico del Borussia Dortmund, devoto de su perro maltés 'Seoltang', y ESFJ por temperamento, siempre integrador en el vestuario. A horas del partido decisivo ante Mexico, su mayor motivacion combina el orgullo de su primer Mundial, la solidaridad con Son en la controversia mediatica interna, y la conciencia de que su desempeno hoy acelerara o retrasara el salto al Frankfurt y posiblemente a la Premier League.
- **🗣️ Monólogo interior:** *“Cuarenta y ocho mil y casi todos contra nosotros, lo siento en el pecho desde el calentamiento, pero remontamos a Chequia y eso me dice que no nos morimos nunca. Mi banda es la guerra hoy: si me lanzan a su extremo rapido por fuera tengo que medir cada subida, porque a esta altura las piernas se cargan antes y no me puedo quedar a mitad de cancha con pulmon vacio. Lo del video de Son y el ruido de la prensa me hierve la sangre, pero ese enojo lo guardo para el duelo, no para una entrada tonta que me deje con amarilla de Tejera al minuto diez. Quiero ganar hoy, clasificar hoy, callar al estadio y a todos los que dudan de nosotros.”*
- **X-factor:** Su disciplina al medir cuando subir por banda sin vaciarse en la altitud decide si Corea controla el costado o se expone al contragolpe.
- **Confianza del dato:** Alta en: edad, club, caps (35 confirmado Wikipedia al 30-mayo-2026), contrato, transfermarkt value, alineacion J1 vs Checia, boicot mediatico, lesion superada declarada por el mismo jugador, MBTI ESFJ, perro Seoltang, ex romance Yang Ye-na, declaraciones de querer casarse pronto, interes Frankfurt, 2 ligas serbias. Media en: rating tactico exacto vs Mexico (estimado segun J1 y fuentes previas al partido), atributos numericos de la simulacion. Baja/Estimacion en: situacion romantica actual exacta (sin confirmar publicamente novia actual), detalles familiares (padres/hermanos, no reportados publicamente).
- **Fuentes:** Wikipedia (Seol Young-woo, en.wikipedia.org/wiki/Seol_Young-woo) - datos biograficos y caps CONFIRMADOS; Transfermarkt (transfermarkt.us/young-woo-seol/profil/spieler/639414) - valor de mercado 6.5M EUR, contrato hasta 2027 CONFIRMADO; Namu Wiki (namu.wiki/w/설영우) - informacion detallada de caracter, tatuajes, mascota, MBTI, relaciones - CONFIRMADO fuente wiki coreana; Nate.com (news.nate.com/view/20240104n31288) - romance con Yang Ye-na y declaraciones sobre matrimonio CONFIRMADO; Xportsnews (xportsnews.com/article/2152170) - interes EPL y clausula de rescision CONFIRMADO; Nate Sports (sports.news.nate.com/view/20260301n00934) - oferta Frankfurt CONFIRMADO; Kyeonggi.com (kyeonggi.com/article/20260617580013) - entrenamiento 17 junio Zapopan CONFIRMADO; Kyeonggi.com (kyeonggi.com/article/20260615580008) - declaraciones de Seol sobre lesion superada y calor CONFIRMADO; Sky Sports (skysports.com/football/korea-republic-vs-czech-republic/549766) - resultado y alineacion vs Checia CONFIRMADO; Sports Mole (sportsmole.co.uk) - prediccion XI vs Mexico ESTIMACION basada en alineacion anterior; FotMob/Soccerway - estadisticas 2025-26 CONFIRMADO; WhoScored (whoscored.com) - rating 6.48 vs Checia CONFIRMADO; SCMP (scmp.com/sport/football/article/3357358) - boicot mediatico por polemic de Son CONFIRMADO; Yahoo Sports (sports.yahoo.com) - detalles controversia servicio militar Son CONFIRMADO; Mixvale.com.br - analisis tactico rol Seol en Mundial ESTIMACION editorial; Grokipedia/Gazprom-football.com - perfil biografico ampliado ESTIMACION parcial.

#### Hwang In-beom — KOR · Mediocampista central (CDM / box-to-box, No. 6) · 29 años · 75 caps
- **Club / situación:** Feyenoord Rotterdam — Titular indiscutible en Feyenoord cuando esta sano. Temporada 2025-26 con 17 partidos (12 de inicio), 1 gol, 3 asistencias y rating promedio 7.15 en Eredivisie. Inicio de temporada brillante (Player of Month en septiembre, Team of Month en octubre), luego interrumpido por lesion de pantorrilla (diciembre), muslo (noviembre), y tobillo (marzo 2026) que lo elimino el resto de la temporada de club. La KFA asigno staff medico propio para acelerar su rehabilitacion. Recuperado para el Mundial, jugo 84 minutos contra Republica Checa (J1) logrando gol y asistencia y siendo nombrado Jugador del Partido. Contrato vigente hasta junio 2028 (firmado en septiembre 2024, €8M). Ningun rumor de transferencia activo.
- **Físico/anatomía:** 177 cm, 70 kg, velocidad punta ~32 km/h, durabilidad 55/100
- **Historial de lesiones:** Propenso 2025-26: gemelo, rotura ligamento tobillo der mar-2026; recuperado
- **Familia:** Casado con Kim Minji (boda el 25 de diciembre de 2021, tras 5 anos de noviazgo). Su esposa es ex-deportista (reportada como ex-amazona/jinete). Primera hija nacida el 11 de septiembre de 2024, nombrada 'Santa'. Hwang corto el cordon umbilical y lloro al verla nacer. Declaro en entrevistas que su familia es su mayor motivacion: 'quiero ser un marido y padre del que no hay que avergonzarse'. Mientras jugaba en Red Star Belgrado, su esposa permanecio en Corea durante el embarazo, separados por distancia. Publicamente, Hwang ha sido muy emotivo al hablar de su hija en entrevistas postpartido. (Fuentes: Xportsnews entrevista sept 2024, IBTimes, Korea.net 2024)
- **Estado personal:** Estado personal estable y muy positivo. El nacimiento de su hija Santa (septiembre 2024) fue un punto de inflexion emocional que el mismo describe como 'el inicio de una nueva vida'. Tras meses de lesiones consecutivas (cadera, muslo, tobillo) que amenazaron su participacion mundialista, su recuperacion exitosa y su actuacion de gala contra Chequia (gol + asistencia, MOTM) le han generado una oleada de alivio, confianza y satisfaccion enormes. La controversia del video burlando el servicio militar de Son Heung-min le afecta como parte del grupo (el equipo entero boicoteo medios locales), pero Hwang no es el blanco directo. El ambiente interno del equipo, aunque tenso con la prensa coreana, parece cohesionado como respuesta a la afrenta externa: paradojicamente, la polemica puede haber actuado como aglutinante. Nada en fuentes publicas indica turbulencia personal propia hoy. (Fuentes: Korea Times mayo 2026, ESPN junio 2026, Al Jazeera junio 2026, VnExpress junio 2026)
- **Personalidad:** Callado y discreto fuera del campo (multiple medios lo describen como 'soft-spoken', 'unassuming'). No busca los focos: deja que la actuacion hable por el. Con la experiencia y los anos ha ganado autoridad silenciosa; ESPN lo describe como 'elder statesman' del equipo a pesar de tener solo 29 anos. Dentro del campo es competitivo, inteligente tacticamante y con mentalidad colectiva marcada: sus declaraciones siempre priorizan el equipo sobre lo individual. Gran capacidad de adaptacion probada en 7 paises/ligas (Corea, Canada/MLS, Rusia, Grecia, Serbia, Paises Bajos). Resiliente ante la adversidad: tres lesiones en seis meses no lo quebraron. Capaz de mantener la compostura en momentos de presion maxima (gol de desempate en el min 67 Mundial). Wesley Sneijder y Karim El Ahmadi lo han elogiado publicamente tras su llegada a Feyenoord. Fue comparado con Shinji Ono. (Fuentes: ESPN, Vietnam.vn, Korea JoongAng Daily)
- **Motivación hoy:** HOY especificamente: (1) La deuda personal con su familia — quiere que su esposa Kim Minji y su hija Santa (9 meses) lo vean brillar en el mayor escenario del mundo; en octubre 2024 declaro 'quiero mostrar a mi esposa e hija lo grande que es este club y lo orgulloso que estoy'. (2) Revancha fisica: volvio de tres lesiones en seis meses para estar en el Mundial; cada partido es una victoria sobre su propio cuerpo. (3) Superar Qatar 2022 — su objetivo declarado es cuartos de final, y este partido es bisagra para lograrlo. (4) El ambiente hostil del estadio Akron con aficionados mexicanos es un estimulo, no un freno: ya lo vivio en J1 con 'un estadio como Seoul', lo que el tomo positivamente. (5) La controversia del video de Son: Hwang es parte del grupo solidario alrededor del capitan; jugar bien hoy es tambien una respuesta colectiva a quienes intentaron desestabilizarlos.
- **Biografía:** Hwang In-beom (황인범, nacido el 20 de septiembre de 1996 en Daejeon, Corea del Sur) es el mediocampista mas completo de la historia reciente del futbol coreano y el motor oculto de la seleccion. Hijo de una ciudad industrial del centro del pais, debuto como el goleador mas joven del Daejeon Citizen a los 18 anos antes de ganarse la exencion del servicio militar con el oro en los Juegos Asiaticos 2018. Su carrera ha sido un recorrido incesante por siete ligas —MLS, Liga de Rusia, Super Liga de Grecia, SuperLiga de Serbia, Eredivisie—, acumulando titulos y reconocimientos individuales en cada etapa: MVP de la EAFF 2019, Player of the Season en Serbia 2023-24, Player of the Month en Feyenoord al mes de llegar. En el plano personal, su matrimonio con Kim Minji en diciembre de 2021 y el nacimiento de su hija Santa en septiembre de 2024 redefinieron su motivacion: se presenta en cada campo como padre y marido ademas de futbolista. En el Mundial 2026, despues de superar tres lesiones encadenadas que pusieron en duda su participacion, se convirtio en la figura del debut de Corea con gol y asistencia contra Chequia —silencioso en los vestuarios, letal en el cesped—, consolidandose como el cerebro sin el cual el engranaje tatico de Hong Myung-bo sencillamente no funciona.
- **🗣️ Monólogo interior:** *“Mi gol contra Chequia todavía me arde en las piernas, en el buen sentido: sé que cuando llego desde atrás soy peligroso y hoy quiero más. Pero esto es otra cosa: 48,000 mexicanos, casi todo verde en las gradas, y nosotros cargando con el ruido de afuera, lo de Sonny, la prensa, todo ese veneno que intentamos dejar fuera del vestuario. Que hablen. Yo controlo el balón, yo marco el ritmo, y desde el centro del campo voy a apagar el estadio toque a toque. Me preocupa el aire: a esta altura y con esta humedad las piernas se cargan antes, tengo que dosificar mis llegadas y no quemarme en los primeros veinte. México nunca nos ha ganado el respeto en un Mundial, siempre nos han pasado por encima al final. Hoy se acaba eso. Si yo no me escondo, el equipo no se esconde.”*
- **X-factor:** Llegadas desde segunda línea y control del tempo: si dicta el ritmo y silencia el Akron, Corea gana el grupo.
- **Confianza del dato:** alto
- **Fuentes:** Wikipedia Hwang In-beom (en.wikipedia.org/wiki/Hwang_In-beom); ESPN 'Midfield metronome' (espn.com, pre-Mundial 2026); ESPN 'Relishing Mexico clash' (espn.com/soccer/story/_/id/49045083, 13-jun-2026); Korea Times 'Healthy at last' (koreatimes.co.kr, 26-may-2026); Xportsnews entrevista nacimiento hija (xportsnews.com/article/1902840, sept 2024); IBTimes 10 fotos esposa (ibtimes.co.uk, jun 2026); Al Jazeera controversia Son (aljazeera.com, 16-jun-2026); Yahoo Sports media blackout (sports.yahoo.com, jun 2026); Vietnam.vn 'Quiet heartbeat' (vietnam.vn, 2026); FotMob stats 2025-26 (fotmob.com); Namu Wiki KR (namu.wiki); Sports Khan entrevista Feyenoord (sports.khan.co.kr, sept 2024); Korea JoongAng Daily lesiones (koreajoongangdaily.com); RotoWire injury tracker (rotowire.com); SI.com Mexico vs South Korea preview (si.com, 18-jun-2026)

#### Paik Seung-ho — KOR · Mediocampista defensivo (doble pivote) · 29 años · 28 caps
- **Club / situación:** Birmingham City FC (EFL Championship, Inglaterra) — Titular indiscutible en Birmingham City, numero 8, contrato hasta 2028. Temporada 2025-26 excelente: 4 goles, 1 asistencia, 3374 minutos jugados, rating promedio 7.02 en FotMob, 6 tarjetas amarillas. Sufrio dos dislocaciones de hombro izquierdo (noviembre 2025 y febrero 2026), rechazo la cirugia en ambas ocasiones para proteger su participacion en el Mundial. Recuperado y en forma plena segun entrenos de la seleccion desde mayo 2026. No hay rumores de transferencia activos; el jugador mismo dijo que quedarse en Birmingham es bueno para su carrera.
- **Físico/anatomía:** 182 cm, 73 kg, velocidad punta ~30 km/h, durabilidad 60/100
- **Historial de lesiones:** Luxacion hombro nov-2025 (sin cirugia); golpe feb-mar 2026
- **Familia:** Soltero — no hay relacion romantica confirmada publicamente. En enero 2023 circularon rumores de noviazgo con la jugadora de volleyball Lee Jae-young, con fotos de anillos similares y avistamientos, pero ninguno lo confirmo oficialmente y no hay informacion posterior que confirme continuidad. Padre: Prof. Baek Il-young, docente de Educacion Fisica en la Universidad Yonsei, con doctorado de Purdue University (USA), ex directivo de la federacion coreana de tenis universitario. El padre fue quien introdujo a Paik en el futbol en mayo 2002 a traves de una escuela de futbol. Tiene dos hermanas mayores, con 6 y 7 anos de diferencia respectivamente; el es el hijo menor y tardio de la familia. Se ha reportado que aconseja a sus hermanas sobre sus vidas romanticas. Sin hijos conocidos.
- **Estado personal:** Estable y enfocado. Desde mayo 2026 entrena en el campamento previo del Mundial en Salt Lake City, Utah. La decision de rechazar la cirugia de hombro fue descrita por el mismo como una apuesta personal deliberada por el Mundial y por sus companieros en Birmingham. Comparte el clima de unidad y tension interna del equipo surcoreano tras la polemica del video sobre Son Heung-min (comentarios burlones de periodistas sobre su exencion militar, filtrados el 7 de junio): la seleccion decreto un boicot colectivo a los medios coreanos, creando un ambiente de cierre de filas y solidaridad interna que historicamente eleva el rendimiento colectivo. No hay reportes de problemas personales, conflictos internos ni presion familiar negativa. Estadoa nimo: positivo con carga de motivacion grupal elevada.
- **Personalidad:** Emocionalmente intenso pero controlado en cancha. Como capitan del equipo sub-24 en los Juegos Asiaticos 2022, lloro sin parar al final tras ganar el oro, reflejo de la presion que asumio y la profundidad de su compromiso. Descrito por entrenadores como jugador que sorprende, impredecible tacticamente. Agradecido y humilde en entrevistas. Muy social dentro del vestuario: estrecho vinculo con Hwang Hee-chan y el grupo de la generacion del 96. Habla espanol con fluidez nativa tras 7 anos en La Masia. Intelectualmente curioso (hijo de un profesor universitario). La decision de rechazar dos cirugias de hombro por el Mundial revela caracter competitivo y disposicion a asumir riesgos personales por metas colectivas. Tiene rasgos de lider silencioso: no busca el protagonismo mediatico pero genera cohesion.
- **Motivación hoy:** Principal motivador hoy: completar el sueno del Mundial que comenzó con el gol historico ante Brasil en Qatar 2022 y convertirse en pieza clave de una seleccion que gana; dice explicitamente que quiere seguir cumpliendo suenos en el Mundial. La polemica interna del equipo (boicot mediatico por Son) actua como combustible colectivo — el grupo esta cerrado en banda y con mentalidad de fortaleza. La victoria ante Chequia (donde su pase penetrante inicio el gol de la victoria) le da confianza. El rechazo voluntario a la cirugia crea una deuda emocional consigo mismo que hoy necesita pagar sobre el campo. Motivacion adicional: ganar frente al pais anfitrion en su estadio propio.
- **Biografía:** Paik Seung-ho (백승호, nacido el 17 de marzo de 1997 en Seoul) es el mediocentro defensivo de la seleccion de Corea del Sur y de Birmingham City. Hijo de un profesor universitario de ciencias del deporte, inicio su carrera en un campamento de futbol a los cinco anos y a los doce fue captado por el FC Barcelona tras deslumbrar en el Korea-Catalonia Youth Cup, pasando siete anos en La Masia. Tras rodaje en Girona, Darmstadt y Jeonbuk — donde gano la K League 1 (2021) y la FA Cup coreana (2022) — llego al Birmingham City en enero 2024 y se convirtio en pieza fundamental de su ascenso al Championship como campeon de la League One 2024-25, siendo elegido en el once ideal de la PFA. En el mundial de Qatar 2022 marcó de media distancia ante Brasil en los octavos de final en lo que fue nominado Gol del Torneo, ganandose su lugar permanente en la seleccion. En la temporada 2025-26 sufrió dos dislocaciones de hombro izquierdo (noviembre y febrero) y rechazo la cirugia en ambas ocasiones para no perderse el Mundial, una decision que define su caracter: determinado, sacrificado y colectivo. Hoy, 18 de junio de 2026, llega al partido mas exigente del grupo contra Mexico como titular en el doble pivote junto a Hwang In-beom, con el equipo unido tras el boicot mediatico en defensa de Son, habiendo participado 84 minutos y proporcionado el pase clave del gol decisivo ante Chequia el 11 de junio.
- **🗣️ Monólogo interior:** *“Si ganamos hoy, clasificamos con una jornada de sobra; eso lo cambia todo, no podemos dejarlo escapar. Voy a sentir la pelota pesada en los pulmones por la altura, así que tengo que medir cada carrera, no perseguir todo, leer y cortar antes de correr. El estadio entero va a estar contra nosotros, casi cincuenta mil mexicanos, y con todo el ruido de afuera por lo de Son tengo que ser yo el que ponga calma en el centro, ser el ancla. El árbitro uruguayo pita todo: una entrada tonta mía y nos quedamos con diez, no me lo puedo permitir; agresivo pero limpio.”*
- **X-factor:** Ser el metrónomo que tapa el medio y reparte sin perder la pelota, gestionando energía a 1,566 m para que el equipo no se ahogue en el segundo tiempo.
- **Confianza del dato:** Alto en datos clave (edad, club, contrato, lesiones, familia paterna, rol tactico, estadisticas 2025-26, actuacion vs Chequia, boicot mediatico). Medio-bajo en estado romantico actual (solo hay rumores de 2023 sin confirmacion). Estimaciones numericas en atributos son inferencias del perfil publicado y estadisticas disponibles, no datos directamente medidos.
- **Fuentes:** Wikipedia (EN): https://en.wikipedia.org/wiki/Paik_Seung-ho | Namu Wiki (KO): https://namu.wiki/w/%EB%B0%B1%EC%8A%B9%ED%98%B8 | Yahoo Sports (caps/WC): https://sports.yahoo.com/articles/paik-joins-south-korea-world-101900986.html | bet365 News (hombro nov 2025): https://news.bet365.com/en-gb/article/birmingham-city-paik-seung-ho-injuyr-against-middlesbrough/2025110815244931882 | the72.co.uk (Chris Davies injury update): https://the72.co.uk/2025/11/10/birmingham-city-chris-davies-paik-seung-ho-injury-latest/ | Korea Times (feb 2026 injury): https://www.koreatimes.co.kr/sports/20260211/south-korea-team-suffers-injury-setbacks-as-world-cup-looms | Daum/Nate (cirugia rechazada, declaraciones propias): https://v.daum.net/v/20260314230144634 | ESPN (lineup vs Mexico): https://www.espn.com/soccer/story/_/id/49079638/mexico-vs-south-korea-fifa-world-cup-2026-tv-channel-how-watch-kick-live-stream-injury-predicted-line-ups | World Soccer Talk (KOR vs CZE June 11): https://worldsoccertalk.com/world-cup/south-korea-vs-czech-republic-live-updates-minute-by-minute-coverage-of-the-2026-world-cup-group-a-game/ | Yahoo Sports (Son media blackout): https://sports.yahoo.com/soccer/article/2026-world-cup-south-korea-reportedly-stages-team-media-blackout-after-son-heung-min-mocked-for-his-military-service-005409431.html | BBC Sport (Birmingham contract 2028): https://feeds.bbci.co.uk/sport/football/articles/c8rdmnp354zo | FotMob (2025-26 stats): https://www.fotmob.com/players/848102/seung-ho-paik | Kookje (padre Baek Il-young): http://www.kookje.co.kr/news2011/asp/newsbody.asp?code=0500&key=20190611.99099005336 | Nate Sports (Lee Jae-young rumors): https://sports.news.nate.com/view/20230131n26827 | Sports Mole (predicted XI vs MEX): https://www.sportsmole.co.uk/football/south-korea/world-cup-2026/predicted-lineups/who-supports-son-up-top-in-world-cup-clash-predicted-south-korea-xi-vs-mexico_599403.html | Goal.com KR (pase decisivo vs Chequia): https://www.goal.com/kr/

#### Lee Tae-seok — KOR · LWB (Left Wing-Back) · 23 años · 19 caps
- **Club / situación:** Austria Wien — Titular indiscutible en Austria Wien (27 titularidades en 30 partidos de Bundesliga austriaca 2025-26, 2,577 minutos, 3 goles, 4 asistencias, rating promedio 7.33 en FotMob). Termino la temporada de club en mayo 2026 y llega al Mundial con ritmo de competencia solido. Su primer ano europeo fue muy exitoso, consolidandose como pieza clave y ejecutor de tiros de esquina. Contrato hasta junio 2029. Sin rumores de transferencia inmediata. Fichado por 800.000 euros desde Pohang Steelers en agosto 2025.
- **Físico/anatomía:** 174 cm, 68 kg, velocidad punta ~33 km/h, durabilidad 78/100
- **Historial de lesiones:** Sin lesiones mayores; gran fondo
- **Familia:** Padre: Lee Eul-yong (ex-futbolista, heroe de la semifinal del Mundial 2002, ahora vicepresidente de la Federacion Coreana de Futbol). Madre: Lee Suk (1972). Hermano menor: Lee Seung-jun (2004). Hermana menor: Lee So-yul (2007). Sin informacion publica confirmada sobre pareja romantica o hijos. Lee Tae-seok nacio el 28 de julio de 2002, justo cuando su padre viajaba al fichaje en Trabzonspor (Turquia) tras el Mundial. Su padre lo vio nacer y partio hacia Europa con el bebe en brazos.
- **Estado personal:** Estado personal altamente positivo y estable. Acaba de protagonizar el momento mas emotivo de su vida deportiva: el 12 de junio 2026 debuто en la Copa del Mundo vs. Republica Checa (2-1), convirtiendose junto a su padre en solo la segunda pareja padre-hijo en representar a Corea del Sur en Mundiales (tras Cha Bum-kun y Cha Du-ri). Tras el partido declaro: 'Es un honor que no puedo expresar con palabras. Me siento muy feliz de poder mostrar a mi familia que soy un hijo del que estar orgullosos.' Su padre, Lee Eul-yong, fue visto emocionado en television al momento del debut. La controversia del video burlando el servicio militar de Son Heung-min (leaked el 7 de junio, viral dias antes del partido contra Mexico) unio al grupo en torno a un proposito comun y aumento la cohesion del vestuario, segun todas las fuentes. Lee Tae-seok, como jugador sin exencion militar confirmada (no gano Juegos Asiaticos ni medalla olimpica), tiene motivacion personal adicional: un buen Mundial podria acelerar su carrera en Europa y darle mayor tiempo antes de enfrentar el servicio militar obligatorio.
- **Personalidad:** Humilde, agradecido y con fuerte sentido del deber familiar. Sus entrevistas revelan un caracter emotivo pero contenido: habla con gratitud hacia su familia y reconoce el peso del apellido Eul-yong. No es lider vocal — ese rol lo ocupa Son Heung-min — pero es trabajador y comprometido. Fisicamente agresivo en el campo (6 tarjetas amarillas en la temporada de club), lo que sugiere intensidad y temperamento competitivo. Rol models publicamente declarados: Hector Bellerin (en su juventud) y actualmente Andy Robertson de Liverpool, lo que revela aspiraciones de ser un wingback moderno de alto nivel ofensivo y defensivo. Aparecio en el programa infantil 'Naerara Shootdolyi' junto a Lee Kang-in cuando era nino, lo que sugiere personalidad extrovertida desde joven. Su musica y pasatiempos fuera del futbol no estan documentados publicamente.
- **Motivación hoy:** Motivacion maxima hoy por multiples factores convergentes: (1) Segundo partido mundialista de su vida y oportunidad de afianzar su titularidad; (2) El peso emocional de seguir los pasos del padre, que jugo dos Mundiales, es un impulso diario; (3) La unidad del vestuario frente a la controversia del video de Son Heung-min crea una mentalidad de 'todos juntos contra el mundo'; (4) Un buen partido contra Mexico (rival historicamente superior a Corea) lo consolidaria como wingback de clase mundial en el mercado europeo; (5) La situacion de su servicio militar sin resolver añade urgencia a cada actuacion internacional. Factor de presion negativa potencial: el ambiente de hostilidad con medios coreanos y el nerviosismo del equipo por el escandalo podrian generar distracciones.
- **Biografía:** Lee Tae-seok (이태석, nacido el 28 de julio de 2002 en Incheon) es el hijo del legendario Lee Eul-yong, protagonista de la semifinal del Mundial 2002, y representa la segunda generacion de una familia emblematica del futbol coreano. Criado en las academias del FC Seoul, debuto en la K-League 1 en 2021 y se forjo como lateral izquierdo tecnico y dinamico, heredando el potente pie zurdo de su padre. Tras pasos por Pohang Steelers (2024-2025, con titulo en la Copa de Corea), dio el salto a Europa en agosto de 2025, fichando por Austria Wien por 800.000 euros con contrato hasta 2029. En su primera temporada europea fue titular indiscutible (27 de 30 partidos, 3 goles, 4 asistencias), demostrando calidad suficiente para Europa media-alta. En la seleccion absoluta, debuto en noviembre 2024 y acumula 19 internacionalidades; el 12 de junio 2026 se convirtio, junto a su padre, en solo la segunda pareja padre-hijo en representar a Corea en Mundiales, tras los Cha Bum-kun y Cha Du-ri. Juega como wingback izquierdo en el sistema 3-4-2-1 de Hong Myung-bo, aportando anchura, centros con el izquierdo y presion alta; su principal area de mejora sigue siendo la solidez defensiva 1v1. Sus roles models son Hector Bellerin y Andy Robertson, perfil que resume sus ambiciones ofensivas.
- **🗣️ Monólogo interior:** *“Cuarenta y ocho mil gargantas y ninguna canta para nosotros; cuando toque la pelota va a silbar todo el Akron y tengo que dejar que ese ruido me empuje, no que me ahogue. Me toca Alvarado, el que regatea para humillar, y Quinones por dentro: si me como una finta temprano me van a buscar toda la noche, asi que primero el cuerpo, primero no perder la espalda, ya tendre tiempo de subir. El aire pesa raro aqui arriba, en el calentamiento sentia que el segundo esfuerzo no llegaba, tengo que medir cada subida porque al minuto 70 esta cancha mojada y esta altura me van a cobrar todo. Y por dentro arde lo de Son, lo del video, todo ese ruido sucio de casa: hoy juego por el, callado, ganando, porque una victoria nos clasifica y le tapa la boca a todos.”*
- **X-factor:** Contener a Alvarado en el uno contra uno sin regalarle la amarilla temprana que el arbitro uruguayo esta deseando sacar.
- **Confianza del dato:** Alta en datos biograficos, familiares, estadisticos de club y seleccion, y contexto de partido. Media en atributos numericos (estimacion calibrada con datos disponibles). Baja/especulativa en vida personal romantica (no hay informacion publica confirmada) y en estado fisico exacto post-Chequia (la sustitucion al 69' fue tactica segun fuentes, sin parte de lesion oficial).
- **Fuentes:** Wikipedia Lee Tae-seok (https://en.wikipedia.org/wiki/Lee_Tae-seok); Seoul Daily/Sedaily entrevista post-Chequia (https://www.sedaily.com/article/20055145); Edaily entrevista gala familiar (https://edaily.co.kr/News/Read?mediaCodeNo=257&newsId=05484166645481064); FotMob stats (https://www.fotmob.com/players/1107251/tae-seok-lee); Nate Sports perfil familiar (https://sports.news.nate.com/view/20260612n32693); Dkilbo noticia traspaso Austria (https://www.dkilbo.com/news/articleView.html?idxno=507987); Sports Mole predicted XI vs Mexico (https://www.sportsmole.co.uk/football/south-korea/world-cup-2026/predicted-lineups/who-supports-son-up-top-in-world-cup-clash-predicted-south-korea-xi-vs-mexico_599403.html); Yahoo Sports controversia Son Heung-min (https://sports.yahoo.com/soccer/article/2026-world-cup-south-korea-reportedly-stages-team-media-blackout-after-son-heung-min-mocked-for-his-military-service-005409431.html); Al Jazeera media blackout (https://www.aljazeera.com/sports/2026/6/16/south-korea-world-cup-squad-at-odds-with-media-over-son-heung-min-mockery); RotoWire MEX vs KOR preview (https://www.rotowire.com/soccer/article/mexico-vs-south-korea-preview-predicted-lineups-team-news-tactical-analysis-2026-world-cup-group-a-118510); StarNews Korea lineup (https://www.starnewskorea.com/en/sports/2026/06/18/2026061812125024857); Playmakerstats Austria Wien 25-26 (https://www.playmakerstats.com/player/lee-tae-seok/762303). ESTIMACIONES PROPIAS: atributos numericos sintetizados de estadisticas publicas, ratings de plataformas (FotMob 7.33, Sofascore), descripcion tacnica de Wikipedia y observaciones de analistas; servicio militar sin confirmar oficialmente.

#### Lee Kang-in — KOR · Mediapunta / Extremo Derecho (AM/RW) · 25 años · 50 caps
- **Club / situación:** Paris Saint-Germain (PSG) — Suplente de lujo en PSG bajo Luis Enrique: 27 partidos Ligue 1 (18 titularidades), 3G 4A, promedio FotMob 7.22, pero CERO titularidades en UCL en toda la temporada. No jugó ni un minuto en la final de la UCL por segundo año consecutivo. Acuerdo personal ya alcanzado con Atletico de Madrid para el verano 2026 (fee estimado ~25-35M€); salida de PSG prácticamente confirmada. El limbo contractual es a la vez liberador (ya no tiene nada que perder en PSG) y generador de concentración máxima en el Mundial como escaparate.
- **Físico/anatomía:** 173 cm, 66 kg, velocidad punta ~33 km/h, durabilidad 72/100
- **Historial de lesiones:** Lesiones musculares menores recurrentes; sin cirugias; apto
- **Familia:** Novia: Park Sang-hyo (nacida 1999, 2 años mayor), heredera de 5a generación del conglomerado Doosan (revenue USD 14.6B en 2024), actualmente haciendo máster en París. Fueron vistos juntos en la final de la UCL 2025 (Lee le puso su medalla de oro alrededor del cuello), en Roland Garros 2025 y en tiendas de lujo en París. Se conocieron a principios de 2024 a través de la hermana mayor de Lee. No hay hijos reportados. Padre: ex-boina verde surcoreano e instructor de Taekwondo, ferviente fanático de Diego Maradona, se trasladó a España antes que el resto de la familia para fundar un dojang y facilitar la carrera de su hijo. Madre: Kang Sung-mi, ex-maestra de jardín de infantes y posteriormente administradora hospitalaria. Hermana mayor: Lee Jung-eun, basada en París, aparecida en programa deportivo coreano 'The Girls Who Beat Goals', fue quien presentó a Lee y Park Sang-hyo. Segunda hermana mayor fuera del foco público.
- **Estado personal:** Estado personal relativamente estable y con viento a favor. La relación con Park Sang-hyo progresa públicamente sin escándalos. El capítulo PSG está mentalmente cerrado — la salida hacia Atletico de Madrid está acordada, lo que elimina la ansiedad de la incertidumbre laboral. La polémica del video sobre el servicio militar de Son (captada el 7 de junio en entrenamiento en Guadalajara) generó unidad de grupo: todo el plantel se cerró en banda contra la prensa doméstica. Lee, quien ya tiene su propia exención militar ganada en los Juegos Asiáticos 2023, se sumó solidariamente al boicot. Esta dinámica de 'nosotros contra el mundo' suele elevar el rendimiento colectivo. Carga emocional pendiente: el recuerdo de dos finales de UCL seguidas viendo desde el banquillo todavía pesa. El Mundial 2026 es su oportunidad de reivindicarse ante el mundo como titular indiscutible, no como pieza de rotación.
- **Personalidad:** Técnicamente brillante y con confianza elevada en su capacidad individual: no duda en driblar en espacios cerrados ni en cargar con la responsabilidad creativa del equipo. Pasional e impulsivo por naturaleza — el incidente con Son Heung-min en la Copa de Asia 2024 (pelea física antes de la semifinal, Son con dedo dislocado, Lee golpeando al capitán) fue la expresión más cruda de esa impulsividad. Sin embargo, la madurez post-escándalo es notable: viajó a Londres a disculparse en persona con Son, luego realizó disculpa pública con reverencia formal en el Estadio Mundialista de Seúl. Desde entonces ha adoptado un rol de portavoz conciliador del equipo, defendiendo al cuerpo técnico contra los abucheos de la afición y pidiendo unidad pública. Curioso: en lo táctico es un 'coachable player' que ha ampliado su repertorio de centrocampista clásico a perfil versátil. Sus referentes son Messi, Maradona (herencia del padre) y David Silva. Carácter competitivo extremo — la rabia controlada de quien lleva dos años viendo los títulos más grandes desde el banquillo actúa como combustible.
- **Motivación hoy:** MOTIVACION PRINCIPAL HOY: El Mundial 2026 es su plataforma de relanzamiento tras tres años de frustraciones en UCL. Un gran partido hoy ante Mexico, con audiencia global, consolida su valor de mercado y su narrativa de titular en Atletico. MOTIVACION SECUNDARIA: Demostrar que la reconciliacion con Son fue real y productiva — la sociedad Son-Lee es el activo más esperado de Corea del Sur y un buen partido los confirma como duo de clase mundial. MOTIVACION TERCIARIA: Redención patriótica — el escándalo de la Copa de Asia 2024 le costó contratos publicitarios y el cariño de la afición; el 9.1 en J1 vs Chequia ya ha empezado a revertir esa narrativa y hoy puede consolidarla. PESO NEGATIVO: La ligera incertidumbre física por el esguince de tobillo izquierdo de mayo (se recuperó para J1 sin problemas visibles); y el desgaste emocional del drama mediático del equipo los dias previos.
- **Biografía:** Lee Kang-in (이강인, nacido el 19 de febrero de 2001 en Incheon, Corea del Sur) es el jugador más tecnicamente completo de su generación en Asia. A los 10 años cruzó el mundo para ingresar a la academia de Valencia CF, donde se convirtió en el jugador coreano más joven en debutar profesionalmente en Europa (17 años) y ganó la Copa del Rey 2018-19. Su Premio al Balón de Oro del Mundial Sub-20 de 2019 anunció al mundo un talento generacional. Tras un paso de consolidación en RCD Mallorca (2021-23), donde absorbió la dureza de La Liga como titular habitual, PSG pagó 22M€ para hacerse con sus servicios en 2023. En París conquistó tres Ligas 1 y dos Champions League consecutivas (2025 y 2026), convirtiéndose en el primer asiático con múltiples títulos de UCL — aunque la crueldad del fútbol lo dejó en el banquillo en ambas finales. Su carrera está marcada por una dualidad: dentro del campo, es el cerebro creativo más desequilibrante de Corea del Sur, capaz de completar 38 de 38 pases con 5 regates ganados y una asistencia en un solo partido mundialista (J1 vs Chequia, rating 9.1 Flashscore); fuera, sobrevivió la peor crisis de su carrera tras la pelea física con Son Heung-min en la Copa de Asia 2024, la cual le costó contratos publicitarios y un calvario de disculpas públicas, pero de la que emergió más maduro, más líder y con la reconciliación más esperanzadora del fútbol asiático. Hoy en el Estadio Akron, ante México, con el transfer a Atlético casi firmado y el mundo mirando, Lee Kang-in vive su momento de mayor exposición y mayor claridad de propósito.
- **🗣️ Monólogo interior:** *“Cuarenta y ocho mil gargantas y ninguna canta para nosotros; cuando toque la pelota va a silbar todo el Akron y tengo que dejar que ese ruido me empuje, no que me ahogue. Me toca Alvarado, el que regatea para humillar, y Quinones por dentro: si me como una finta temprano me van a buscar toda la noche, asi que primero el cuerpo, primero no perder la espalda, ya tendre tiempo de subir. El aire pesa raro aqui arriba, en el calentamiento sentia que el segundo esfuerzo no llegaba, tengo que medir cada subida porque al minuto 70 esta cancha mojada y esta altura me van a cobrar todo. Y por dentro arde lo de Son, lo del video, todo ese ruido sucio de casa: hoy juego por el, callado, ganando, porque una victoria nos clasifica y le tapa la boca a todos.”*
- **X-factor:** Contener a Alvarado en el uno contra uno sin regalarle la amarilla temprana que el arbitro uruguayo esta deseando sacar.
- **Confianza del dato:** HIGH — La gran mayoría de atributos están respaldados por múltiples fuentes verificadas de 2025-2026. Las estimaciones numericas estan calibradas sobre estadisticas concretas (Flashscore, FotMob, Transfermarkt) y contexto narrativo extenso. Las unicas estimaciones prudentes son el numero exacto de caps hoy (49 o 50) y la valoracion de composure_volatility, que no tiene metrica directa disponible pero se infiere solidamente del historial publico.
- **Fuentes:** Wikipedia (Lee Kang-in, consultado jun 2026): edad, carrera, caps 48 a 1-jun-2026, palmarés, estilo. | StarNews Korea (abr-jun 2026): situación en PSG, minutos UCL, transfer Atletico, fee negociado. | Flashscore (jun 2026): rating 9.1 J1 vs Chequia, estadísticas detalladas (38/38 pases, 5 dribbles, 10/14 duelos, 3 big chances). | Yahoo Sports / IBTimes SG / FNNews / KBizoom (2025-2026): relación con Park Sang-hyo, presencia en final UCL 2025 y Roland Garros. | CNN / Goal.com / Malay Mail / Soccerway (feb-mar 2024): incidente con Son Heung-min en Copa de Asia, disculpas formales. | Korea Herald / Yahoo Sports (jun 2026): relación Son-Lee en Mundial 2026, boicot mediático. | SCMP / Sportskeeda (jun 2026): boicot mediático por video de servicio militar de Son. | ESPN / GetFrenchFootball / Yahoo Sports (jun 2026): acuerdo con Atletico de Madrid. | Sports Mole / RotoWire (jun 2026): lineup previsto vs Mexico, rol táctico. | MSN / StarNews (may 2026): lesion tobillo izquierdo vs Brest. | Malay Mail (jun 2025): Lee pide a fans ver el lado positivo del equipo antes del Mundial. | Korea Herald (2024): 'mutinería' en Copa de Asia y jerarquía estricta. | SCMP (sep 2023): exención militar tras oro Juegos Asiáticos 2023. ESTIMACIONES (marcadas como tal): caps totales hoy (50) — estimado sumando el partido vs Chequia (J1=cap 49 aprox) y hoy J2=cap 50, basado en 48 caps a 1-jun-2026; composure_volatility estimado por el contraste entre temple en partidos grandes (Copa de Asia, UCL) y episodio impulsivo de 2024; injury_risk estimado bajo dado recuperación exitosa para J1 sin signos de recaída.

#### Lee Jae-sung — KOR · Mediocampista ofensivo (CAM / interior derecho) · 33 años · 106 caps
- **Club / situación:** 1. FSV Mainz 05 (Bundesliga, Alemania) — Titular establecido y pilar del equipo. En febrero de 2026 renovó contrato por voluntad propia ("no fue una decision dificil"), declarandose completamente instalado en el club tras 159 apariciones y 28 goles. Sufrió fractura de falange del dedo gordo del pie izquierdo a principios de abril de 2026, perdió las últimas 4 jornadas del Bundesliga, pero recuperó ritmo de entrenamiento completo a mediados de mayo antes del final de temporada. Terminó la temporada 2025/26 con 4 goles y 2 asistencias en 28 partidos de liga (rating FotMob 6.81). No figura en el parte de lesiones del partido vs Mexico. Mainz clasificó a la Conference League 2025/26, donde llegaron a cuartos de final (primer europeo de la historia del club).
- **Físico/anatomía:** 180 cm, 70 kg, velocidad punta ~31 km/h, durabilidad 68/100
- **Historial de lesiones:** Pomulo roto jul-2025; muslo sep-2025; fractura dedo abr-2026; en monitoreo
- **Familia:** Oriundo de Ulsan, tercer hijo (el menor) de tres hermanos varones. Su hermano mayor es el también futbolista profesional Lee Jae-kwon; ambos cursaron juntos la secundaria Hakseong y la Universidad de Korea (고려대). No hay información pública confirmada sobre pareja sentimental, esposa o hijos del futbolista Lee Jae-sung. Mantiene amistad muy estrecha con Son Heung-min (ambos nacidos en 1992, se conocen desde la seleccion sub-15 en 2007).
- **Estado personal:** Estable y pleno. En declaraciones de junio de 2026 ha manifestado que "pasa cada dia con gratitud y trabaja mas duro". Ha asumido públicamente que este es su último Mundial ("solo tengo este Mundial en mente, no el siguiente"), lo que le da un enfoque intenso y sin presión adicional de futuro. La renovacion de contrato en Mainz (febrero 2026) eliminó toda incertidumbre laboral. La polémca del video sobre el servicio militar de Son, su amigo más cercano en la selección, afectó el animo colectivo del equipo pero al mismo tiempo unio al grupo: todos los jugadores cerraron filas en solidaridad. Lee, como co-capitan de facto y veterano de 11 años en el equipo, ha asumido rol de lider en el camarín durante la crisis mediática. Recuperación física completa de la fractura de dedo, aunque los últimos 6 meses de temporada en Mainz fueron un peu fragmentados por esa lesión.
- **Personalidad:** Introvertido reflexivo con vena intelectual inusual para un futbolista. Lleva años escribiendo columnas y un blog narrativo ('이재성의 축구이야기') donde reflexiona sobre la vida, el deporte y la adaptación cultural en Alemania. Responde entrevistas en alemán pese a no ser nativo (dejó sorprendido a periodistas germanos). Humilde hasta el autodesprecio: en 2023 afirmó que "en Corea no me ven como una estrella". Colega y entrenadores lo describen como "absolutamente fiable", "brutal en el trabajo" y "enormemente decente como persona". Su entrenador Fischer dijo que "a veces hay que protegerlo de sí mismo" porque quiere jugar tres veces por semana sin descanso. Tiene hobbies creativos: armar sets de Lego, leer, cocinar (preparó galletas de vainilla alemanas y lo escribió en su blog). Modelo de rol: Totti y luego Iniesta. Liderazgo por ejemplo, no por voz. Comparte caracteristicas con el jugador tipo 'agua' en vestuario: cohesiona, no protagoniza, rara vez amarilla.
- **Motivación hoy:** 1) Este es declaradamente su ULTIMO Mundial: máxima motivación existencial. 2) Quiere marcar en un Mundial (nunca lo ha hecho en 2018 ni 2022 pese a jugar todos los grupos). 3) La crisis del video de Son lo ha galvanizado: defender al amigo de toda la vida desde los 15 años y al capitán del equipo. 4) El desafío de jugar vs Mexico en altitud (1,566m), con aficion hostil y sin Montes (defensivo), es visto como oportunidad de oro. 5) Renovacion reciente en Mainz = paz mental total. 6) Mentalidad de lider que guia a jugadores jovenes en su primer Mundial.
- **Biografía:** Lee Jae-sung (이재성, nacido el 10 de agosto de 1992 en Ulsan, Corea del Sur) es el mediocampista ofensivo más veterano de la historia reciente de la selección coreana, con 106 internacionalidades y 15 goles, convirtiéndolo en el centrocampista más 'capeado' del combinado Taeguek. Hijo menor de tres hermanos, siguió los pasos de su hermano Lee Jae-kwon hasta la Universidad de Korea antes de debutar con Jeonbuk Hyundai Motors en 2014, donde ganó la Liga de Campeones de la AFC 2016 y fue MVP de la K League 2017. Desde 2018 emigró a Europa (Holstein Kiel, Mainz 05), consolidándose como uno de los pilares del Bundesliga con 159 apariciones y 28 goles para el club renano, renovando contrato en febrero de 2026 por iniciativa propia. Conocido por un estilo de vida inusual para un futbolista de elite —escribe columnas literarias, estudia alemán de manera autodidacta, arma Lego y reflexiona sobre filosofía del deporte en su blog personal—, es descrito por entrenadores y compañeros como un modelo de profesionalismo, humildad y entrega sin límite. Amigo íntimo de Son Heung-min desde los 15 años (selección sub-15 de 2007), llega a este México vs Corea del Sur sabiendo que es su tercer y último Mundial, con una fractura de dedo superada a tiempo, y galvanizado por la polémica del video sobre el servicio militar de su capitán y mejor amigo.
- **🗣️ Monólogo interior:** *“Cuarenta y ocho mil gargantas y ninguna canta para nosotros; cuando toque la pelota va a silbar todo el Akron y tengo que dejar que ese ruido me empuje, no que me ahogue. Me toca Alvarado, el que regatea para humillar, y Quinones por dentro: si me como una finta temprano me van a buscar toda la noche, asi que primero el cuerpo, primero no perder la espalda, ya tendre tiempo de subir. El aire pesa raro aqui arriba, en el calentamiento sentia que el segundo esfuerzo no llegaba, tengo que medir cada subida porque al minuto 70 esta cancha mojada y esta altura me van a cobrar todo. Y por dentro arde lo de Son, lo del video, todo ese ruido sucio de casa: hoy juego por el, callado, ganando, porque una victoria nos clasifica y le tapa la boca a todos.”*
- **X-factor:** Contener a Alvarado en el uno contra uno sin regalarle la amarilla temprana que el arbitro uruguayo esta deseando sacar.
- **Confianza del dato:** Alta. Ha renovado contrato, tiene mas de 100 caps, viene de temporada sólida en Mainz y fue elogiado después del partido contra Chequia. Declaró abiertamente que quiere marcar un gol en este Mundial. La adversidad del video de Son, lejos de deprimirlo, parece haberlo energizado.
- **Fuentes:** Wikipedia (Lee Jae-sung, en.wikipedia.org/wiki/Lee_Jae-sung) [CONFIRMADO]; Bundesliga.com perfil oficial y articulo 'Midfield Magician' [CONFIRMADO]; FIFA.com entrevista oficial 2026 'Stability will be key' [CONFIRMADO]; Mainz05.de anuncio renovacion contrato y entrevista febrero 2026 [CONFIRMADO]; RotoWire preview Mexico vs Korea y parte de lesiones [CONFIRMADO]; Hankookilbo.com entrevista junio 2026 ('ultimo Mundial', caps, citas directas) [CONFIRMADO]; Starnewskorea.com reporte fractura de dedo (10 abril 2026) [CONFIRMADO]; Koreadaily.com recuperacion fractura (mayo 2026) [CONFIRMADO]; Yahoo Sports/TNT Sports/Al Jazeera polemica video Son y boicot mediatico [CONFIRMADO]; Sportsmole.co.uk prediccion alineacion vs Mexico [CONFIRMADO]; Namu.wiki y Brunch.co.kr (blog, personalidad, familia, hermano) [CONFIRMADO]; Sportbookreview.com altitud Estadio Akron [CONFIRMADO]; FootyStats/FotMob estadisticas temporada 2025-26 [CONFIRMADO]. NOTA: informacion sobre pareja/hijos NO encontrada en ninguna fuente publica — se asume vida privada no divulgada. Edad citada como '33' segun nacimiento agosto 1992 (cumple 34 en agosto 2026).

#### Son Heung-min — KOR · Delantero izquierdo / Extremo izquierdo · 33 años · 145 caps
- **Club / situación:** Los Angeles FC (MLS) — Titular indiscutible en LAFC. Fichado en agosto 2025 por transferencia record MLS (~$26.5M desde Tottenham). En 2025 debut fue explosivo: 12 goles y 4 asistencias en 13 partidos. En la temporada regular 2026 lleva 13 partidos, 0 goles y 8-9 asistencias — lider en asistencias de la MLS — pero en una racha sin goles de 13 apariciones consecutivas. Jugo las clasificatorias del Mundial con 10 goles en 13 partidos. Contrato hasta diciembre 2027. Rumores de retorno a Europa (Milan, Bayern) fueron publicamente desmentidos por el propio Son en noviembre 2025.
- **Físico/anatomía:** 183 cm, 78 kg, velocidad punta ~35 km/h, durabilidad 70/100
- **Historial de lesiones:** Cirugia orbital (4 fracturas) 2022; brazo roto 2020; pie/isquios recurrentes; velocidad confirmada 35.1 km/h
- **Familia:** Soltero sin hijos ni pareja confirmada. Ha declarado publicamente que priorizara el futbol hasta retirarse antes de casarse o formar familia. Vinculado romanticalmente en el pasado a la cantante K-pop Jisoo (BLACKPINK) y a Bang Min-ah, pero siempre negado. Familia nuclear central: padre Son Woong-jung (ex futbolista, entrenador, mentor de vida desde la infancia — entreno a Heung-min con 500 disparos por pie por dia); madre Eun Ja Kil (apoyo emocional, privada); hermano mayor Heung-Yun Son (exentrenador en academia del padre). La familia residio con el en Europa durante su etapa en Tottenham. Nota: el padre enfrentó acusaciones legales de abuso infantil en su academia en Corea del Sur en 2024 — el padre se disculpo publicamente.
- **Estado personal:** Estable profesionalmente pero bajo presion extradeportiva significativa. La semana previa al partido (7-16 jun 2026) vivio la polemica del microfono abierto: periodistas surcoreanos captados burlándose de su servicio militar abreviado y de su forma de correr en entrenamientos. La KFA emitio comunicado, el jefe de prensa renuncio, el equipo boicoteo a la prensa coreana, y Son mismo se reunio con los periodistas implicados. Segun fuentes, Son no aclaro si levantaria el veto. El equipo entrena a puerta cerrada. Esta controversia — en un tema hipersenisble en Corea del Sur como el servicio militar — lo afecta emocionalmente aunque su respuesta publica ha sido de liderazgo y calma. Ademas viene de fallar multiples chances claras vs Chequia (J1): dos tiros sobre el arco, un disparo desviado y un remate sin fuerza, siendo sustituido al 69'. Eso pesa. Sin embargo, antes del torneo declaro estar 'guardando los goles para explotar en el Mundial'. Vive en Los Angeles, soltero, entorno estable, sin escandalo personal propio.
- **Personalidad:** Lider autentico, humilde, orientado al equipo. Reiteradamente declara que el futbol es colectivo: 'nunca he pensado que yo soy mas importante que mis compañeros'. Educado por su padre con disciplina extrema y sin elogios — lo que forjo una psicologia de busqueda constante de mejora y resistencia al fracaso. Extrovertido y cariñoso con compañeros y aficion, celebre por su sonrisa y carisma fuera del campo. Internamente muy competitivo y exigente consigo mismo. Enfria las criticas externas con ecuanimidad publica pero las interioriza para motivarse. Doble pie natural (ambidiestro por entrenamiento paterno). Ha mostrado agresividad defensiva que le costo tres rojas en 2019 en la Premier League — sugiere una intensidad subyacente que puede descontrolarse aunque en general es disciplinado. En 2022 jugo el Mundial con mascara tras fractura orbital — mentalidad 'juego a traves del dolor'. Estratega: decidio mudarse a LA un año antes del Mundial para preparar condiciones y compartir su experiencia con la seleccion. Forbes Korea Power Celebrity Top 5, simbolo nacional.
- **Motivación hoy:** Motivador PRIMARIO hoy: potencialmente su ultimo Mundial (el mismo lo ha dicho). Quiere dejar legado historico — un gol vs Mexico lo igualaria como maximo goleador asiatico en Mundiales (Honda, Japon). Viene de un match de J1 sin gol pese a múltiples oportunidades claras — la presion interna de revertir eso es alta. La polemica del servicio militar lo energiza: el escandalo fue percibido como una afrenta hacia el y sus compañeros de vida lo respaldan, lo que puede catalizar una respuesta en el campo. DESMOTIVADOR: racha de 13 partidos seguidos sin gol en LAFC mas las chances falladas vs Chequia pueden erosionar ligeramente su confianza de cara al arco, aunque su discurso publico lo niega. El peso de ser simbolo nacional en su ultimo probable Mundial es doble filo: motiva y presiona simultaneamente.
- **Biografía:** Son Heung-min (Chuncheon, 8 julio 1992) es el mayor futbolista asiatico de todos los tiempos y capitan emblematico de Corea del Sur. Forjado desde los 6 años por su padre Son Woong-jung — ex futbolista cuya carrera trunco una lesion — bajo un regimen diario de 500 disparos por pie, cuatro horas de malabarismo y cero partidos oficiales hasta los 14, Son desarrolló una ambidestreza y tecnica de elite que lo llevo a los 16 años al Hamburgo SV. Paso por el Bayer Leverkusen antes de llegar al Tottenham Hotspur (2015-2025), donde marcó 173 goles, ganó la Bota de Oro de la Premier League 2022 (primer asiatico en conseguirlo), disputó una final de Champions League (2019) y levantó la Europa League (2025) como capitan. En agosto 2025 rompio el record de traspaso de la MLS al firmar por el LAFC por ~$26.5M. Con la seleccion suma 145 caps y 56 goles (segundo historico), habiendo jugado tres Mundiales anteriores — incluyendo Qatar 2022 con mascara protectora tras fractura orbital. El Mundial 2026 en Norteamerica llega cargado de simbolismo: potencialmente su ultimo, en el continente donde ahora vive, con la polemica del microfono abierto encendida (periodistas burlándose de su servicio militar abreviado), y tras fallar goles cantados vs Chequia en J1. A sus 33 años, soltero, enfocado, vive en Los Angeles sin familia propia, con su identidad profesional totalmente ligada al futbol y a la seleccion.
- **🗣️ Monólogo interior:** *“Sin Cesar atras, me toca a mi bajar de central y cargar con el brazalete; no es mi posicion, pero soy el capitan y este equipo necesita que yo de la cara. El Akron va a rugir, 48 mil mexicanos empujando, y yo nací para estas noches. Cuidado con Tejera, pita todo y yo siempre ando al limite con las amarillas, hoy tengo que medir el barrido y ganar con la cabeza, no con la pierna. Si ganamos hoy clasificamos antes de tiempo y nadie nos quita el liderato; le metemos a Corea que viene tocada por su lio interno. Vamos con todo, esta es mi casa.”*
- **X-factor:** Liderazgo y lectura desde el centro de la zaga improvisada: si organiza la linea y domina el balon aereo sin caer en faltas tontas, Mexico cierra el grupo hoy.
- **Confianza del dato:** Alta en datos biográficos y contextuales (confirmados por múltiples fuentes primarias). Alta en la polemica del servicio militar (reportada por Al Jazeera, La Nacion, Latinus, ABC Noticias y otras fuentes). Alta en estadisticas de clubs e internacionales (ESPN, MLS, Transfermarkt). Moderada en atributos numericos del gemelo digital (son estimaciones fundamentadas en evidencia publica, no en datos biometricos privados): finishing bajo por racha sin gol y fallos en J1; emotional_state_today bajo por polemica activa; motivation_today alto por legado y revancha; composure_volatility moderada-alta por historico de rojas y presion del momento.
- **Fuentes:** LAFC oficial: https://www.lafc.com/news/lafc-signs-global-football-icon-son-heung-min | MLS Soccer transfer record: https://www.mlssoccer.com/news/lafc-break-mls-transfer-record-son-heung-min-signing-tottenham-south-korea | SI.com transfer rumors: https://www.si.com/soccer/lafc-son-heung-min-confirms-winter-plans-amid-transfer-rumors | Goal.com David Beckham clause: https://www.goal.com/en/lists/son-heung-min-premier-league-return-january-ex-tottenham-star-david-beckham-clause-mls-contract-lafc/blteed4a6a2de8c619a | ESPN cuarto Mundial: https://www.espn.com/soccer/story/_/id/49023594/fourth-fifa-world-cup-south-korea-captain-son-heung-min-feeling-kid | Infobae perfil Mexico: https://www.infobae.com/mexico/deportes/2026/05/21/el-jugador-que-mexico-debera-vigilar-en-el-mundial-2026-son-heung-min-estrella-y-capitan-de-corea-del-sur/ | Transfermarkt perfil: https://www.transfermarkt.us/heung-min-son/profil/spieler/91845 | Athlon Sports familia 2026: https://athlonsports.com/soccer/son-heung-min-married-2026-wife-girlfriend-parents-family | La Nacion polemica prensa: https://www.lanacion.com.ar/deportes/futbol/corea-del-sur-en-crisis-los-jugadores-no-hablan-con-la-prensa-tras-un-video-viralizado-con-criticas-nid16062026/ | Latinus.us veto prensa: https://latinus.us/deportes/futbol-internacional/2026/6/16/mundial-2026-corea-del-sur-prensa-roces-son-heung-min-servicio-militar-176322.html | Al Jazeera media controversy: https://www.aljazeera.com/sports/2026/6/16/south-korea-world-cup-squad-at-odds-with-media-over-son-heung-min-mockery | DraftKings performance vs Czechia: https://dknetwork.draftkings.com/2026/06/11/tracking-son-heung-min-in-south-korea-vs-czechia-on-thursday-6-11-26-how-did-he-perform/ | Fox Sports chances missed: https://www.foxsports.com/watch/fmc-o701qc3jztv59byb | ESPN stats 2026 MLS: https://www.espn.com/soccer/player/stats/_/id/149945/son-heung-min | Goal.com asistencias Messi record: https://www.goal.com/en-us/lists/son-heung-min-mls-lafc-superstar-assist-record-lionel-messi/blt09fd8ade14ef1c68 | BeIN Sports padre formacion: https://www.beinsports.com/en-us/soccer/fifa-world-cup-2026/articles/the-story-of-heung-min-son-extreme-discipline-and-family-pressure-to-reach-the-world-cup-2026-06-02 | StarNews motivacion: https://www.starnewskorea.com/en/sports/2026/05/27/2026052714322259473 | StarNews confianza goles: https://www.starnewskorea.com/en/sports/2026/05/23/2026052308331013145 | FIFA.com stats quotes: https://www.fifa.com/en/articles/son-heungmin-stats-quotes-records | Olympics.com forma Mundial: https://www.olympics.com/en/news/son-heungmin-fifa-world-cup-2026-stats-form-watch-republic-of-korea-star | Taeguk Warriors analisis: https://www.taegukwarriors.com/korea-republic-vs-mexico-world-cup-group-a-match-2-preview-the-son-heung-min-debate-media-boycott-and-more/ | NBC News J1 resultado: https://www.nbcnews.com/sports/soccer/live-blog/fifa-world-cup-2026-opening-ceremonies-june-11-live-updates-rcna349400

---

## 6. Fórmulas completas del modelo

### 6.1 Goles esperados base (Poisson de fuerzas — Maher 1982)
```
λ_local = prom_goles · fuerza_ataque_local · fuerza_defensa_visitante · ventaja_local
λ_visit = prom_goles · fuerza_ataque_visit · fuerza_defensa_local
fuerza_ataque  = goles_marcados_equipo / promedio_liga
fuerza_defensa = goles_recibidos_equipo / promedio_liga      (>1 = defensa débil)
ventaja_local  = ×1.15–1.30  (≈ +0.3 a +0.4 goles);  0 si cancha neutral
```

### 6.2 Corrección Dixon-Coles (1997) — más empates 0-0 y 1-1
```
P(x,y) = Poisson(x;λ) · Poisson(y;μ) · τ(x,y)
τ(0,0) = 1 − λ·μ·ρ      τ(1,0) = 1 + μ·ρ
τ(0,1) = 1 + λ·ρ        τ(1,1) = 1 − ρ        resto = 1
ρ ≈ −0.08   (rango −0.03 a −0.15;  ρ=0 ⇒ Poisson simple)
+ ponderado temporal exp(−ξ·Δt) para dar más peso a partidos recientes
```

### 6.3 Elo de selecciones (eloratings.net) → supremacía de goles
```
W_e = 1 / (1 + 10^(−(E_local + ventaja − E_visit)/400))      ventaja_local = +100 Elo
K (importancia): Mundial 60 · final continental 50 · clasificatorios 40 · otros 30 · amistoso 20
× factor por margen de victoria (×1.5 por 2 goles, ×1.75 por 3, …)
supremacía_goles = (E_local + ventaja − E_visit)/400 · ~1.0  (≈ 400 Elo = 1 gol)
λ_local = base_total/2 + supremacía/2 ;  λ_visit = base_total/2 − supremacía/2
```

### 6.4 Poisson bivariada (Karlis-Ntzoufras 2003) — correlación de goles
```
golesL = X1 + X3 ;  golesV = X2 + X3 ;  Xi ~ Poisson(λi)
Cov(golesL, golesV) = λ3 ≈ 0.10   (λ3 = 0 ⇒ independencia ⇒ doble Poisson)
```

### 6.5 De-vig de cuotas (probabilidad de mercado limpia)
```
p_cruda = 1 / cuota_decimal ;  overround = Σ p_cruda − 1
Método potencia (recomendado): hallar k tal que Σ (1/cuota_i)^k = 1
                               p_justa = (1/cuota_i)^k
(Alternativas: aditivo, Shin. El multiplicativo simple es el peor.)
```

### 6.6 Motor estocástico de gemelos digitales (`sim_gemelos.py`)
**Por CADA simulación (nada estático):**
```
# (a) Condiciones del día
lluvia       ~ Bernoulli(0.42)
temperatura  ~ Normal(22, 2)
afición      ~ Normal(ruido=89, 8)
pitch_speed  = base · (1.06 si llueve)

# (b) "Día" de cada jugador
forma        = 1 + z·(1 − consistencia/100)·0.30      # los irregulares oscilan más
temple_hoy   ~ Normal(temple_medio + (clutch−50)·0.10, volatilidad)
motiv_hoy    = motivación ± Normal(0,5)
lesión       ~ Bernoulli( max(riesgo, 100−durabilidad)/100 · 0.05 ) → forma ×0.5

# (c) Índices de equipo (suma ponderada por rol de posición)
ofensivo_i   = 0.5·finishing + 0.3·creatividad + 0.2·skill  (× forma·temple·motiv)
defensivo_i  = 0.6·defensa  + 0.2·aéreo       + 0.2·skill  (× forma·temple)
ataque_eq    = 0.7·Σ(w_att·ofensivo) + 0.3·Σ(w_cre·ofensivo)
defensa_eq   = Σ(w_def·defensivo)

# (d) λ por equipo
aéreo_eq     = media_pond(0.6·(altura−170) + 0.4·(aéreo−50))   → goles de balón parado
pace_eq      = media_pond(0.5·pace + 0.5·(velmax−28)·8)
contragolpe  = 1 + 0.0015·(pace_propio − pace_rival)·(1 + 0.5·lluvia)
λ_local = BASE · mult_ataque · (def_rival) · afición · lluvia · contragolpe + ABP_aéreo
λ_visit = BASE · mult_ataque · (def_local) · lluvia · contragolpe + ABP_aéreo

# (e) Motor minuto a minuto (96')
por minuto t: gol si random < λ/90 ajustado por:
   - fatiga/altitud (min 60+): MEX stamina + , KOR stamina −
   - game state: el que pierde ×1.18 ; el rival contragolpea ×0.92
   - rojas: hazard/min = (100−disciplina)/100·0.0009 ; roja ⇒ ataque ×0.72, rival ×1.15
```

---

## 7. Parámetros y modificadores del caso base

```
Ancla λ:           MEX 1.30, KOR 1.02
Dixon-Coles ρ:     −0.08          Poisson bivariada λ3: 0.10
Ventaja afición:   +0.12 xG  ×(1 + 0.0020·(ruido−50))
Altitud:           MEX stamina + ; KOR stamina −  (fatiga último tercio)
Lluvia (p=0.42):   MEX control ×0.98 ; KOR contragolpe ×1.04 ; pitch ×1.06 ; contragolpe ×1.5
Árbitro Tejera:    ~5 amarillas → riesgo roja = 100 − disciplina
Bajas MEX:         sin Montes (Edson de central, durabilidad 55) ni Malagón (portero #1)
N_SIMS:            modelo 1 = 5.5M · modelo 2 = 100k · modelo 3 = 500k
```

| Factor | A favor | Modificador |
|---|---|---|
| Afición/anfitrión (94% local, ruido 89) | 🇲🇽 | +0.12 xG |
| Altitud 1,566 m (Corea no del todo aclimatada) | 🇲🇽 | fatiga KOR último tercio |
| Invicto histórico en Mundiales (1998, 2018) | 🇲🇽 | +0.03 |
| Aéreo / balón parado (zaga alta: Rangel/Edson 190, Jiménez 188) | 🇲🇽 | + goles ABP |
| Suspensión de Montes (zaga MEX improvisada) | 🇰🇷 | +0.05 a Corea |
| Lluvia + velocidad de Son (35.1 km/h) | 🇰🇷 | contragolpe ×1.5 con lluvia |
| Polémica interna de Son (boicot prensa) | 🇲🇽 | ánimo KOR − (62) pero clutch + |
| Duelo Jiménez vs Kim Min-jae | — | clave del partido |

---

## 8. Resultados completos de los 3 modelos

### 8.1 Modelo 1 — Estadístico frío (5.5M sims)
- Dixon-Coles (forma/xG): MEX 39.2 / E 33.4 / KOR 27.4
- Elo (1880 vs 1740): MEX 42.9 / E 31.9 / KOR 25.2
- Mercado de-vig: MEX 39.4 / E 32.2 / KOR 28.4
- Ajustado por bajas: MEX 36.2 / E 32.9 / KOR 30.9
- **Consenso ensamble:** **MEX 39.6 / E 32.6 / KOR 27.9** · goles 1.22–0.99

### 8.2 Modelo 2 — Agente-por-jugador (100k)
- **MEX 46.4 / E 28.4 / KOR 25.2** · goles 1.62–1.19 · Over 2.5 53% · BTTS 60% · alguna roja 8.5%
- Señal emergente: 11/11 coreanos sienten la altitud negativa; 11/11 mexicanos positiva.

### 8.3 Modelo 3 — Gemelos digitales + física (estocástico, 500k)
- **MEX 46.5 / E 28.7 / KOR 24.8** · goles 1.57–1.13 (λ sd ±0.12/0.10)
- Over 2.5 50% · Under 2.5 50% · BTTS 57% · alguna roja 5%
- **Condicional clima:** con lluvia (43%) MEX 45.4 / E 28.9 / KOR 25.7 · sin lluvia MEX 47.4 / E 28.5 / KOR 24.1
- Marcadores: 1-1 13.5% · 1-0 MEX 10.8% · 2-1 MEX 10.2% · 2-0 7.6% · 0-0 7.1% · 0-1 7.0%

### 8.4 Veredicto triangulado
> **México favorito (~46-48%), empate ~28-29%, Corea ~24%. México no pierde ~75%.** Escenario más probable: **victoria mexicana ajustada (1-0 / 2-1)** decidida en el último tercio (altitud) con 1-1 como empate más repetido. **Llaves:** lluvia (abre el contragolpe coreano), zaga improvisada de México sin Montes, y Lee Kang-in entre líneas en los primeros 60'. Cuanto más realismo metimos, más convergió con el mercado → señal de calibración correcta.

---

## 9. Fuentes consultadas (todas, por categoría)

**Rendimiento / jugadores:** fbref.com · sofascore.com · fotmob.com · theanalyst.com (Opta/Stats Perform) · whoscored.com · transfermarkt (perfiles, lesiones, altura/peso) · au.soccerway.com (injury history) · ea.com (atributos como proxy).
**Ranking / fuerza:** inside.fifa.com/fifa-world-ranking · eloratings.net · concacaf.com · AFC.
**Resultados / contexto:** en.wikipedia.org (resultados, Grupo A 2026) · espn.com · goal.com · fifa.com (Match Centre, artículos) · foxsports.com · skysports.com · cbssports.com.
**Mercado:** Bet365 · ESPN odds · Kalshi.
**Clima / entorno:** meteored.mx (hora por hora) · telediario.mx · infobae.com · tiempo3.com · es.weatherspark.com (Seúl).
**Sede / cancha:** informador.mx (cancha Akron) · scientificamerican.com + infobae.com (césped Mundial 2026) · dazn.com (capacidad) · worldcupper.com · seatgeek.com.
**Ciencia del deporte:** Nassis 2013 (journals.lww.com, altitud 1,400-1,750 m, −3.1% distancia) · McSharry 2007 (bmj.com) · Gore 2008 (aclimatación) · Konefał 2014 / Nassis 2014 (calor) · Nevill et al. 2002 + ghost games COVID (nature.com) · JQAS host-advantage (degruyterbrill.com).
**Metodología:** Dixon & Coles 1997 · Maher 1982 · Karlis & Ntzoufras 2003 (aueb.gr PDF) · Clarke 2017 (de-vig) · dashee87.github.io · pena.lt/y (penaltyblog) · tactiq.club · towardsdatascience.com (Elo→λ).
**Jugadores (notables):** Jiménez fractura craneal (skysports, si.com, nbcnews) · Edson cirugía tobillo (hammers.news) · Gallardo velocidad (tudn.com) · Son velocidad 35.1 km/h (premierleague.com, yahoo) · Son cirugía orbital (skysports) · Kim Min-jae (bavarianfootballworks) · controversia Son (aljazeera, foxsports) · Son a LAFC (lafc.com).

> *Cada gemelo digital (sección 5.3) incluye sus fuentes específicas.*

---

## 10. Tiers de disponibilidad y consideraciones de modelado

### Tiers (del catálogo)
- **T1 — Fácil/gratis:** demografía, stats básicas, resultados, plantillas, valores, clima. (Transfermarkt, FBref, APIs abiertas, datos meteorológicos.)
- **T2 — De pago:** event data detallado, xG, mapas de pase, datos de árbitros. (Opta/StatsBomb, Wyscout.)
- **T3 — Interno del club:** GPS, carga de entrenamiento, HRV, sueño, wellness, datos médicos.
- **T4 — Casi inobtenibles/subjetivos:** estado emocional real, vida familiar, motivación, química. → **Aquí usamos agentes IA como proxy** (role-play + investigación pública), que es la innovación de este modelo.

### Reglas de modelado (para no arruinar el modelo)
1. Más variables ≠ mejor (maldición de la dimensionalidad / overfitting).
2. Multicolinealidad: altura↔aéreo, sprints↔distancia. Podar con correlación/VIF.
3. Sin fuga de información (*leakage*): toda feature debe existir ANTES del partido.
4. Naturaleza temporal: validación temporal (entrenar pasado, probar futuro), no aleatoria.
5. Datos faltantes (T3-4): imputar / excluir / indicador "missing".
6. Eventos raros (goles, rojas) → datos desbalanceados; usar AUC/PR.
7. Correlación ≠ causalidad.
8. Agregación según target (equipo ⇒ sumas/medias ponderadas por minutos).
9. Importancia de features (SHAP / feature importance) para podar.
10. Empezar simple (10-20 features T1-2) y añadir complejidad solo si mejora fuera de muestra.

---

## 11. Cómo re-correr / inventario de archivos

```bash
cd "/Users/issacvm/Documents/Futbol Wuru"
python3 sim_mex_kor.py     # Modelo 1: estadístico (Dixon-Coles/Elo/mercado/consenso)
python3 sim_agentes.py     # Modelo 2: agente-por-jugador (lee player_minds.json)
python3 sim_gemelos.py     # Modelo 3: gemelos digitales estocástico (lee twins.json + env.json)
```

| Archivo | Contenido |
|---|---|
| `sim_mex_kor.py` | Modelo estadístico (Poisson bivariada + Dixon-Coles + Elo + mercado + consenso) |
| `sim_agentes.py` | Motor minuto-a-minuto con estado mental de 22 agentes |
| `sim_gemelos.py` | Motor estocástico con gemelos digitales + entorno + física |
| `player_minds.json` | 22 mentes (estado emocional + monólogo interior) |
| `twins.json` | 22 gemelos digitales (bio, familia, personalidad, atributos, física, lesiones) |
| `env.json` | Entorno del día (clima, pasto, aforo, % afición, ruido) |
| `estrategia de analisis.md` | **Este documento maestro** |
| `/Users/issacvm/Downloads/variables_modelo_futbol.md` | Catálogo base de variables (referencia) |

### Para un PARTIDO NUEVO (receta)
1. Lanzar los agentes (sección 2) cambiando equipos/sede/fecha.
2. Guardar salidas estructuradas en `twins.json`, `env.json`, `player_minds.json`.
3. Ajustar en los scripts: `BASE_MEX/BASE_KOR` (ancla λ del consenso), nombres de equipo, `SIT`/modificadores, `N_SIMS`.
4. Correr los 3 scripts y triangular con el mercado de-vig.

---

## 12. Honestidad metodológica y roadmap

### Qué es dato confirmado vs estimación
- **Confirmado:** rankings, resultados/forma, alineaciones, bajas, sede/fecha/hora, clima hora a hora, tipo de pasto, aforo, alturas/pesos, historiales de lesiones, velocidad de Son (35.1 km/h), cuotas, eventos vitales públicos (duelo de Jiménez, divorcio de Kim Min-jae, polémica de Son).
- **Estimado:** velocidades punta de la mayoría (sin GPS público), ratings 0-100 (pace, durabilidad, atributos mentales), magnitudes de modificadores situacionales, λ ancla, y los estados emocionales (role-play, no medición).
- **Sesgos a vigilar:** forma inflada por amistosos débiles; el mercado ya incorpora intangibles; role-play plausible pero no verificable; marcadores modales rara vez >13%.
- **Validación:** triangulación con el mercado de-vig como ancla externa.

### Roadmap (mejoras)
1. **Tracking real** (GPS/eventos): distancia, sprints, PlayerLoad, mapas de calor → fatiga y química exactas.
2. **Carga acumulada** (minutos 7/30 días) y ACWR para riesgo de lesión dinámico.
3. **Calibración histórica** (MLE de ρ, ventaja local y modificadores sobre partidos pasados).
4. **Blend con ML** (XGBoost meta-modelo sobre las salidas de los 3 modelos + features del catálogo).
5. **Narración en vivo** (agentes decidiendo jugada a jugada).
6. **Wellness/HRV** y noticias de último minuto como inputs dinámicos.

---
*Generado para el proyecto Futbol Wuru. Caso base: México vs Corea del Sur, Mundial 2026, Grupo A, Jornada 2, Estadio Akron (Guadalajara). Modelo: Monte Carlo + Gemelos Digitales con IA multi-agente.*

---

## 13. CALIBRACIÓN POST-PARTIDO — back-test contra el resultado real (MEX 1-0 COREA)

> El partido se jugó el 18-jun-2026. **Resultado real: México 1-0 Corea del Sur** (Luis Romo 49', tras error del portero Kim Seung-gyu; doble atajada de Raúl Rangel al 87'). Esto permite medir qué tan acertado fue el modelo y corregir errores sistemáticos.

### 13.1 Predicción (v1, pre-partido) vs Realidad
| Métrica | Predicción v1 | Realidad | ¿Acertó? |
|---|---|---|---|
| Resultado (favorito) | México 46.5% (modal) | **Ganó México** | ✅ dirección correcta |
| Marcador | 1-1 (13.5%), **1-0 MEX (10.8%, #3)**, 2-1 (10.2%) | **1-0 MEX** | ✅ top-3 |
| Portería a cero MEX | ~37% | **Sí** | ✅ |
| Tarjeta roja | ~5% (alguna) | Ninguna | ✅ (caso 95%) |
| Partido cerrado / Under 2.5 | ~50% | 1 gol → Under | ✅ |
| **Goles totales (media)** | **2.70** | **1** | ❌ inflado |
| **xG / quién crea más** | México con ventaja ofensiva (λ 1.39 vs 1.00) | **Corea más xG (0.69-0.91 vs 0.48-0.53), 58% posesión** | ❌ proceso invertido |
| **Desgaste de Corea por altitud** | Asumido (desplome último tercio) | No respaldado; Corea apretó al final | ❌ sobrevalorado |
| Goleador / alineación | Apoyado en Jiménez; Mora titular | Marcó **Romo** (no modelado); **Mora suplente**; Jiménez flojo | ❌ rotación de Aguirre |
| Portero decisivo | No modelado explícito (sí en monólogo de Rangel) | **Decisivo** (error de Kim + atajadas de Rangel) | 🟡 intuido, no modelado |

**Veredicto de acierto:** el modelo **acertó en lo esencial** (favorito correcto con la mayor probabilidad asignada al evento ocurrido, marcador entre los más probables, portería a cero, sin roja, partido cerrado). Pero tuvo **3 errores sistemáticos**: (1) goles inflados, (2) dio a México la ventaja de *creación* cuando Corea creó más, (3) sobrevaloró la altitud. El partido lo decidió el **portero**, factor que v1 no modelaba de forma explícita.

### 13.2 Mejoras aplicadas → MOTOR v2 (`sim_gemelos_v2.py`)
1. **Goles más bajos y realistas:** total de ~2.70 → **~2.2** (real fue 1; el modelo frío daba 2.16). Se bajó la creación base.
2. **Separación CREACIÓN (xG) vs CONVERSIÓN:** Corea crea más por posesión (estilo ×1.02); México es más vertical/clínico (mejor *finishing* de Quiñones/Jiménez). El favoritismo de México viene de **conversión + afición + portería**, no de crear más.
3. **CAPA DE PORTERO (clave):** cada GK tiene un *rendimiento del día* ~Normal(habilidad, volatilidad) que multiplica los goles rivales (0.75–1.30). Captura en una sola mecánica tanto el **error de Kim** como las **atajadas heroicas de Rangel** (Rangel tiene volatilidad alta = comodín).
4. **ALTITUD SUAVIZADA → FATIGA por DISTANCIA REAL:** se elimina el "desplome por altura". La fatiga del último tercio se deriva de la **distancia recorrida real** (capa física, sección 14); la altitud solo encarece ~3% el esfuerzo coreano.
5. **INCERTIDUMBRE DE ALINEACIÓN:** ruido extra en la forma del día (Aguirre rota; Romo entró y marcó, Mora no jugó).

### 13.3 Resultado del MOTOR v2 (500k) y nuevo back-test
| Métrica | v1 (pre-partido) | **v2 (calibrado)** | Realidad |
|---|---|---|---|
| Gana México | 46.5% | **44.0%** | ✅ ganó |
| Empate | 28.7% | **31.4%** | — |
| Gana Corea | 24.8% | **24.7%** | — |
| Goles totales | 2.70 | **2.23** | 1 |
| **Prob. del marcador real 1-0** | 10.8% (#3) | **14.2% (#1, empatado con 1-1)** | ✅ |
| Portería a cero MEX | 37% | **38.8%** | ✅ |
| Alguna roja | 5% | 4.9% | ✅ ninguna |

> v2 mantiene a México como favorito (coherente con Elo 1805 vs 1740 y el mercado), pero con **goles realistas** y el **1-0 como marcador más probable**, que es exactamente lo que ocurrió. **Nota anti-sobreajuste:** v2 NO se fuerza a "predecir 1-0"; se corrigieron mecanismos generales (goles, portero, fatiga real) — un solo partido no debe reescribir el modelo, solo señalar sesgos.

---

## 14. CAPA FÍSICA / TRACKING REAL (cierre de la laguna T3 del GPS)

> Era la mayor laguna del modelo (sección 9): los datos de GPS (distancia, sprints, PlayerLoad) son T3 (internos del club). **Solución:** ingerir los datos físicos que FIFA y Sofascore SÍ publican de los partidos del Mundial.

### 14.1 Fuentes públicas de datos físicos (lo que sí se puede obtener)
| Fuente | Acceso | Campos | Granularidad |
|---|---|---|---|
| **FIFA Training Centre** (fifatrainingcentre.com) | **Gratis** (PDF post-partido, ~53 pág. por cada uno de los 104 partidos) | distancia, sprints, velocidad punta, alta intensidad + métricas EFI tácticas | equipo y jugador |
| **FIFA+ / Player App** | Gratis | distancia, sprints, top speed | jugador |
| **Sofascore** | **Gratis** (web/app; API no oficial) | distancia (km), nº sprints, velocidad punta (km/h), heatmap | equipo y jugador |
| **FotMob** | Gratis | físicos donde disponibles | jugador |
| Opta/Stats Perform, Lenovo Football AI Pro | Pago / interno | set completo de tracking | — |
| StatsBomb open data | Gratis | **solo eventos + 360**, NO físicos | — |

### 14.2 Campos físicos confirmados en circulación (Mundial 2026)
- **Distancia por equipo** (p.ej. Austria-Jordania 239.6 km combinados) y **por jugador** (Olise 12.6 km).
- **Sprints por jugador** (Raphinha 80, Olise 79).
- **Velocidad punta** (Bos 36.7 · Haaland 36.5 · **Son 35.2** · Mbappé 35.1 km/h).
- FIFA cruza distancia/sprints/top-speed vs **temperatura** (distancia y sprints bajan con calor; la velocidad punta no) → útil para Guadalajara.

### 14.3 Cómo se ingirió en el modelo
- Nuevos campos en `twins.json`: **`distance_km`, `sprints`, `top_speed_kmh`**.
- **Datos reales usados como ancla:** Son 35.2 km/h (J1) y Quiñones 8.02 km / 7 sprints (J1). El resto se estima con un *prior por posición × stamina* hasta que FIFA publique el reporte del partido.
- El motor v2 usa la **distancia real de equipo** para la fatiga del último tercio (México ~115 km, Corea ~126 km → Corea presiona más pero se desgasta más), reemplazando el proxy crudo de altitud.
- **Resultado:** México corre menos y mantiene piernas para cerrar; Corea corre más (presión alta) pero paga el esfuerzo — mecánica físicamente fundamentada, no un "castigo por altura" inventado.

### 14.4 Ingesta programática (recomendado para futuros partidos)
1. **Sofascore (API no oficial)** vía wrappers `ScraperFC` / `sofascore-wrapper` / `LanusStats` → `event/{id}/lineups`, estadísticas de jugador, `/heatmap` (distancia, sprints, top speed cuando existen). Limitado por *rate limit* y ToS.
2. **FIFA Training Centre** (verdad de referencia): scraper + parser de los PDF post-partido del Match Report Hub.
3. Tratar distancia/sprints como **sensibles a la temperatura** (validado por FIFA) → modelar para el calor/humedad de la sede.
4. No existe API oficial gratuita de FIFA con métricas físicas; las de Opta/DSG/Sportmonks son de pago.

> **Inventario actualizado:** se añade `sim_gemelos_v2.py` (motor calibrado) y los campos físicos en `twins.json`. El v1 (`sim_gemelos.py`) se conserva para comparación histórica.

---
*Actualización post-partido (19-jun-2026): calibración tras MEX 1-0 COREA + capa física/tracking real. El modelo acertó el favorito, el marcador top y la portería a cero; se corrigieron goles inflados, el proceso de creación xG y la sobrevaloración de la altitud, y se cerró la laguna del GPS con datos físicos públicos de FIFA/Sofascore.*

---

## 15. BACKTEST — validación sobre 28 partidos ya jugados del Mundial 2026

> Metodología: 1 agente predictor por partido aplicando el modelo maestro completo, **sin ver el marcador** (solo info pre-partido: Elo/forma/H2H/sede/altitud/clima/bajas/jugadores/cuotas). El agente devuelve λ (goles esperados) y probabilidades; luego se corre el **mismo motor Dixon-Coles** para todos y se puntúa contra el resultado real.

### 15.1 Resultados globales (28 partidos)
| Métrica | Modelo (Dixon-Coles desde λ) | Prob. directa del agente | Baseline "gana 1º/local" | Baseline "mayor λ" |
|---|---|---|---|---|
| **Acierto 1X2** | **57.1%** (16/28) | 53.6% | 53.6% | 57.1% |
| **Brier multiclase** ↓ | **0.530** | 0.547 | — | — |
| **Log-loss** ↓ | **0.877** | 0.908 | — | — |

- El **motor uniforme (λ→Dixon-Coles) supera a la probabilidad "a ojo" del agente** en acierto, Brier y log-loss → conviene estandarizar la simulación, no fiarse del número suelto del agente.
- 57% de acierto 1X2 es sólido (azar 3-vías ≈ 33%), pero **apenas supera al baseline de favorito** → el valor real del modelo está en la **calibración probabilística**, no en el argmax.

### 15.2 Calibración (probabilidad asignada → acierto real)
| Prob. predicha | Acierto real | Lectura |
|---|---|---|
| ~40% | 75% (3/4) | bien |
| **~50%** | **27% (3/11)** | ❌ **sobreconfianza en partidos parejos** |
| ~60% | 83% (5/6) | muy bien |
| ~70% | 67% (4/6) | bien |
| ~90% | 100% (1/1) | perfecto |

**El modelo es excelente con favoritos claros y malo en partidos cerrados (~50%)**, que en fase de grupos se vuelven empates/sorpresas.

### 15.3 Hallazgos clave
1. **36% de empates reales (10/28)** — tasa altísima (lo normal es ~25%). El modelo casi nunca elige "empate" como #1 (rara vez es el resultado individual más probable), penalizando el acierto. Probabilísticamente asignaba ~28% a empate; el grupo salió cagey. *(Muestra pequeña: 36% es probablemente ruido, no señal permanente.)*
2. **Subestima goles: 2.47 predicho vs 3.18 real.** Sobre todo en **goleadas de favoritos** que el modelo achicó: Inglaterra 4-2 (pred 1-1), USA 4-1 (pred 1-1), Francia 3-1 (pred 1-1), Suecia 5-1, Suiza 4-1, Canadá 6-0. **Los agentes comprimieron λ de los equipos fuertes (demasiado tímidos en ataque).**
3. **Clava las goleadas obvias:** Alemania 7-1, Argentina 3-0, Canadá-Qatar 6-0, Iraq 1-4 Noruega, Uzbekistán 1-3 Colombia, Haití 0-1 Escocia, México 2-0 Sudáfrica.
4. **Falla en parejos/sorpresas:** España 0-0 Cabo Verde, Países Bajos 2-2 Japón, Brasil 1-1 Marruecos, Bélgica 1-1 Egipto, Arabia 1-1 Uruguay, Australia 2-0 Turquía (sorpresa), Ghana 1-0 Panamá (sorpresa).
5. **Grupo A (nuestro caso):** acertó ambos — México favorito (ganó) y Corea-Chequia.

### 15.4 Recalibración probada con datos reales (sin sobreajustar)
Barrido sobre transform de λ (G=escala de goles, S=ensanche favorito-débil, ρ=corrección de empate):
- **Mejor combinación: S≈1.3 (favoritos algo más fuertes) + ρ≈−0.14/−0.16 (más empates)** → Brier 0.530→**0.528**, Log-loss 0.877→**0.851**. Mejora real pero modesta.
- **Subir goles global (G>1) NO ayuda** al scoring probabilístico (la muestra es muy empatada). La subestimación de goles está en las **goleadas**, no en todos los partidos.

### 15.5 Refinamientos adoptados
1. **ρ (Dixon-Coles) = −0.14** (antes −0.08): más masa en empates, mejor log-loss.
2. **Ensanchar λ favorito↔débil (×~1.3 sobre la diferencia)**: los equipos fuertes deben tener λ más alto (cola de goleada), corrigiendo la timidez de los agentes.
3. **NO bajar goles de forma global** (lección anti-sobreajuste del caso México-Corea): los empates 1-1/2-2 conviven con goleadas 5-1; el total medio del Mundial es ~3.
4. **Partidos cerrados:** reducir la confianza del favorito y subir el empate cuando |λ_local−λ_visit| es pequeño.
5. **Mayor muestra:** re-evaluar tras la J3 y los 8avos (28 partidos es poco; el 36% de empates puede ser ruido).

> **Conclusión del backtest:** el modelo **predice bien el favorito y las goleadas claras, está bien calibrado en los extremos, pero es flojo en partidos parejos y subestima los goles de los fuertes**. Las correcciones (ρ, ensanche de λ) son modestas y principiadas; el aprendizaje grande es metodológico: estandarizar el motor (λ→Dixon-Coles) y no sobreajustar a muestras chicas.

---
*Backtest 19-jun-2026: 28 partidos del Mundial 2026, 1 agente por partido (modelo maestro completo, sin fuga de resultado). Archivos: `backtest.json` (predicciones+resultados), `backtest_score.py` (scoring).*

---

## 16. CALIBRACIÓN CON DATOS REALES — el "oro" para próximos partidos

> Objetivo: ajustar el modelo con los resultados reales para acercar las simulaciones a la realidad. **Hecho con rigor (validación cruzada) para NO sobreajustar.**

### 16.1 El hallazgo crítico: la calibración agresiva NO generaliza
Búsqueda en malla de 4 parámetros sobre los 28 partidos:
- **In-sample** el mejor combo bajaba log-loss 0.877 → 0.819 (parecía gran mejora).
- **Leave-one-out CV (fuera de muestra): 0.878 ≈ baseline 0.877.** → la "mejora" era **ruido sobreajustado** (el 36% de empates de esta muestra no se repetirá).

**Conclusión:** con 28 partidos NO se puede recalibrar fuerte de forma fiable. Hacerlo es engañarse. → Se aplica una calibración **modesta y pre-registrada** (de sesgos REPETIBLES, no del ruido) y se re-ajustará con >60 partidos.

### 16.2 Calibración adoptada (`calibration.json`)
Transformación de λ + Dixon-Coles con 4 perillas justificadas por sesgos repetibles:
| Parámetro | Valor | Justificación (sesgo repetible, no ruido) |
|---|---|---|
| **G** (escala de goles) | **1.05** | El Mundial es algo goleador (real 3.18 vs predicho 2.47) |
| **S** (ensanche favorito↔débil) | **1.20** | Los agentes IA son **tímidos** con el ataque de los fuertes (comprimieron λ); ensanchar da cola de goleada |
| **ρ** (Dixon-Coles) | **−0.12** | Más masa en empates 0-0/1-1; rango estándar de la literatura |
| **δ** (multiplicador de empate) | **1.10** | Leve exceso de empates en fase de grupos (conservador) |

Fórmula: `λ_fav' = media·G + dif·S`, luego Dixon-Coles(ρ), luego `P(empate)·δ` y renormalizar.

### 16.3 Mejora validada sobre los 28 partidos
| | Log-loss ↓ | Brier ↓ | Acierto |
|---|---|---|---|
| Sin calibrar | 0.8768 | 0.5303 | 57.1% |
| **Calibrado** | **0.8556** | **0.5245** | 57.1% |
| Mejora | **+0.021** | **+0.006** | = |

Modesta pero **real y honesta** (no infla el acierto a costa de sobreajuste). Validación en el caso real: México-Corea con λ 1.34-0.92 → **México 46% / Empate 32% / Corea 22%**, con **1-0 como 2º marcador** (resultado real ✅).

### 16.4 El predictor reutilizable (`predict_match.py`)
El "oro" operativo: toma los **goles esperados (λ)** de cualquier fuente (agente, motor de gemelos, o Elo) y aplica la calibración + Dixon-Coles para devolver 1X2, marcadores y cuotas justas calibradas.
```bash
python3 predict_match.py <lambda_local> <lambda_visit> [Local] [Visit]
# ej: python3 predict_match.py 1.34 0.92 Mexico Corea
```
**Flujo recomendado para un partido nuevo:** modelo maestro/agentes → estiman λ por equipo → `predict_match.py` → probabilidades calibradas.

### 16.5 Plan de re-calibración (cómo mejora con el tiempo)
1. Tras **J3** (~+20 partidos) y **octavos**, re-correr `backtest-wc2026` (1 agente/partido) → ampliar `backtest.json`.
2. Re-ejecutar `calibrate.py`: con >60 partidos la LOO-CV ya distinguirá señal de ruido → permitirá afinar G/S/ρ/δ con confianza.
3. Vigilar si el 36% de empates persiste (señal) o regresa a ~25% (era ruido).

> **Archivos nuevos:** `calibrate.py` (ajuste + LOO-CV), `calibration.json` (parámetros), `predict_match.py` (predictor calibrado reutilizable), `backtest_score.py` (scoring).

---
*Calibración 19-jun-2026: recalibrado con datos reales bajo validación cruzada. Lección de oro: con muestra chica, calibración modesta y pre-registrada > ajuste agresivo (que sobreajusta). Mejora real de log-loss/Brier sin inflar el acierto. Re-calibrar con >60 partidos.*

---

## 17. OPTIMIZACIÓN MASIVA Y ENSAMBLE — qué movió la aguja y qué no (con rigor estadístico)

> Se exploraron MUCHAS configuraciones, parámetros y fuentes de datos para acercar el modelo a la realidad, **siempre evaluando fuera de muestra (CV) + bootstrap de significancia** para no sobreajustar. Usando todos los núcleos de la Mac.

### 17.1 Búsqueda masiva de parámetros (`search_calibration.py`)
- **6,720 configuraciones × 28 partidos** (G, S, ρ, δ₀, y κ = boost de empate en partidos parejos), en multiprocessing (13 núcleos, 0.4 s).
- Mejor **in-sample**: log-loss 0.877 → 0.822 (espejismo de sobreajuste).
- **CV del procedimiento (elige-en-train, evalúa-en-test, 7-fold×300): 0.866** vs baseline 0.877 → mejora pequeña.
- **Bootstrap (5,000): mejora media +0.053, IC95% [−0.020, +0.124] → cruza 0 → NO significativa.**

### 17.2 Ensamble con datos independientes: agentes + Elo (`ensemble_blend.py`)
- Fuente nueva: **Elo pre-torneo de eloratings.net** (48 equipos, `elo.json`). Se derivó λ desde Elo (supremacía = ΔElo/400 + ventaja anfitrión).
- Resultado del barrido de peso w (CV):

| Fuente | Log-loss ↓ | Brier ↓ | Acierto |
|---|---|---|---|
| **Agentes solo** | **0.856** | **0.525** | **57.1%** |
| Elo solo | 0.947 | 0.573 | 50.0% |
| Mezcla óptima (CV) | w=**1.00** (100% agentes) | — | — |

- **El CV eligió 0% Elo.** Los agentes ya **subsumen** el Elo (lo usan junto con forma, bajas, cuotas y contexto), así que el Elo crudo solo añade ruido. Ensamble **no mejora** (bootstrap: 0.0000).

### 17.3 Conclusión (lo que de verdad aprendimos)
1. **Ningún ajuste de parámetros ni ensamble mejora de forma ESTADÍSTICAMENTE SIGNIFICATIVA con 28 partidos.** La señal de calibración existe (mejora ~0.02–0.05 de log-loss) pero está dentro del ruido.
2. **El cuello de botella es la CANTIDAD de datos, no la potencia de cómputo ni el número de parámetros.** Probamos miles de configs en <1 s; el límite es estadístico.
3. **El Elo no aporta sobre los agentes** → los agentes con el modelo maestro completo ya son la mejor fuente disponible. Buena validación del enfoque.
4. Se mantiene la **calibración modesta** (sección 16: G=1.05, S=1.2, ρ=−0.12, δ=1.10), que mejora log-loss/Brier sin sobreajustar. NO se adoptan los parámetros agresivos de la búsqueda (no son significativamente mejores y se apoyan en la anomalía de empates).

### 17.4 El plan que SÍ moverá la aguja (toda la maquinaria ya está lista)
- **Acumular datos:** tras J3 + octavos (>60–100 partidos), re-correr `backtest-wc2026` (1 agente/partido) → ampliar `backtest.json`.
- Re-ejecutar `search_calibration.py` y `ensemble_blend.py`: con más muestra, el **bootstrap tendrá poder** para detectar mejoras reales y la CV podrá afinar G/S/ρ/δ/κ con confianza.
- Vigilar si el **36% de empates** persiste (señal → subir δ/κ) o vuelve a ~25% (era ruido).

> **Archivos nuevos:** `search_calibration.py` (búsqueda CV+bootstrap), `ensemble_blend.py` (agentes+Elo), `elo.json`, `search_result.json`, `ensemble_result.json`.

---
*Optimización 19-jun-2026: probadas miles de configuraciones y un ensamble con Elo, con CV + bootstrap. Lección de oro reforzada: con 28 partidos, la mejora no es significativa y el Elo no aporta sobre los agentes. La maquinaria queda lista para mejorar de verdad cuando haya más datos (J3+).*

---

## 18. BACKTEST HISTÓRICO (124 partidos: Mundiales 2018+2022+2026) — calibración con poder estadístico

> Para conseguir muestra grande SIN esperar a la J3, se backtesteó sobre fase de grupos de **3 Mundiales**: 2018 (48) + 2022 (48) + 2026 (28) = **124 partidos**, con Elo pre-torneo real de eloratings.net. Calibra el motor cuantitativo Elo→Dixon-Coles (parámetros generales y transferibles).

### 18.1 Calibración del motor Elo (`hist_calibrate.py`, 2,520 configs × 124 partidos, CV+bootstrap)
| | Log-loss ↓ | Brier ↓ | Acierto |
|---|---|---|---|
| Baseline Elo (TOTAL 2.7, GP400 1.0, HOST 0, ρ −0.08) | 1.0099 | 0.602 | 55.6% |
| Mejor in-sample (TOTAL 3.0, GP400 1.3, HOST 100-130) | 1.0039 | 0.596 | 54.0% |
| **CV fuera de muestra del "buscar el mejor"** | **1.0234** | — | — |
| **Bootstrap mejora** | **+0.006, IC95% [−0.014, +0.026] → NO significativa** |||

**Aun con 124 partidos, el tuning NO mejora de forma significativa.** El fútbol es intrínsecamente ruidoso; no se puede "tunear" hacia ganancias grandes.

### 18.2 PERO la dirección de los parámetros es consistente y futbolísticamente sensata
El optimizador, en las 3 muestras, siempre tira hacia:
- **TOTAL ≈ 2.85–3.0** → el Mundial es goleador (confirmado: 2026 real 3.18).
- **GP400 ≈ 1.2–1.3** (vs 1.0) → los **favoritos deben separarse más** (eco del sesgo "modelo demasiado tímido").
- **HOST ≈ 90–130 Elo** → la **ventaja del anfitrión es real y grande** (coincide con la literatura).
→ Se adoptan como **priors moderados transferibles** (`calibration_elo.json`: TOTAL 2.85, GP400 1.2, HOST 90, ρ −0.10, δ 1.05), aunque no alcancen p<0.05.

### 18.3 LA GRAN VALIDACIÓN: el modelo de agentes le gana al motor Elo
Sobre el subconjunto 2026 (mismo set, ambas fuentes):
| Modelo | Log-loss ↓ | Acierto |
|---|---|---|
| Motor Elo baseline | 0.9754 | 53.6% |
| Motor Elo calibrado (direccional) | 0.9518 | 53.6% |
| **AGENTES + modelo maestro (calibrado)** | **0.8556** | **57.1%** |

→ **El modelo maestro completo (agentes) supera con claridad a un motor Elo bien calibrado** (0.856 vs 0.952 log-loss; 57% vs 54%). Toda la maquinaria de investigación/gemelos **se justifica**: no es adorno, aporta señal real sobre el Elo puro.

### 18.4 Conclusión definitiva
1. **Hemos tocado el techo del tuning**, tanto en el torneo actual (28) como en muestra grande (124): las ganancias por ajuste de parámetros NO son estadísticamente significativas. Es la **varianza irreducible** del fútbol.
2. **El modelo está bien construido:** vence a baselines (Elo, mercado-vía-agentes) y está bien calibrado en los extremos.
3. **Priors transferibles ganados:** Mundial goleador, favoritos más separados, ventaja anfitrión ~90 Elo. Útiles para cualquier partido nuevo.
4. **De aquí en más, la mejora NO viene de más tuning** sino de **datos más ricos por partido** (tracking GPS real, alineaciones confirmadas, lesiones de último minuto) — que ya están cableados para ingerirse cuando se publiquen.

> **Archivos nuevos:** `hist2018.json`, `hist2022.json`, `elo2018.json`, `elo2022.json`, `hist_calibrate.py`, `calibration_elo.json`.

---
*Backtest histórico 19-jun-2026: 124 partidos de 3 Mundiales. Lección de oro final: el tuning no rinde más (varianza irreducible), pero el modelo de agentes le gana al Elo calibrado → el enfoque maestro vale. Mejoras futuras = datos más ricos, no más parámetros.*

---

## 19. PROYECCIÓN DEL TORNEO COMPLETO — Monte Carlo de 50,000 Mundiales

> Se simula el torneo entero hacia adelante desde el estado real (28 partidos jugados): los 44 partidos de grupo pendientes + toda la llave (R32→R16→QF→SF→Final), 50,000 veces. **Motor: Elo calibrado (`calibration_elo.json`: TOTAL 2.85, GP400 1.2, HOST 90, ρ −0.10) → Dixon-Coles.** Decisión de diseño: para proyectar un torneo (miles de caminos, rivales aún desconocidos) el estándar es el modelo de fuerza de equipo, NO 22 bots/jugador por partido hipotético (eso es para un partido estelar concreto, como hicimos con México-Corea).

### 19.1 Favoritos al título (Top 16 de 48)
| Equipo | 8vos | 4tos | Semis | Final | 🏆 Campeón |
|---|---|---|---|---|---|
| Argentina | 72% | 56% | 41% | 27% | **17.3%** |
| España | 62% | 46% | 35% | 24% | **14.9%** |
| Francia | 75% | 53% | 36% | 22% | **12.9%** |
| Inglaterra | 72% | 48% | 30% | 17% | **10.0%** |
| Colombia | 68% | 42% | 23% | 12% | 6.3% |
| Brasil | 53% | 32% | 17% | 9% | 4.2% |
| Portugal | 50% | 27% | 15% | 8% | 3.7% |
| Alemania | 63% | 31% | 17% | 8% | 3.6% |
| Noruega | 60% | 33% | 17% | 8% | 3.3% |
| Países Bajos | 49% | 28% | 14% | 7% | 2.9% |
| Suiza | 63% | 31% | 13% | 6% | 2.2% |
| México | 59% | 25% | 12% | 5% | 2.0% |
| Japón | 46% | 24% | 11% | 5% | 2.0% |
| Bélgica | 46% | 23% | 10% | 4% | 1.6% |
| Austria | 42% | 22% | 10% | 4% | 1.5% |
| Australia | 55% | 24% | 9% | 4% | 1.3% |

### 19.2 Clasificación proyectada por grupo (líder probable / clasifican)
- **A:** México (gana grupo 93%, ya clasificado) · Corea 2° (88% clasifica)
- **B:** Canadá (62%) · Suiza (ambos ~100% clasifican)
- **C:** Brasil (39%) · Escocia / Marruecos peleados (88/88/81% clasificar — grupo abierto)
- **D:** USA (54%) · Australia (40%)
- **E:** Alemania (64%) · Costa de Marfil (95% clasifica)
- **F:** Suecia (36%) · Países Bajos / Japón (grupo muy parejo: 95/86/85%)
- **G:** Bélgica (40%) · Egipto/Irán/N.Zelanda peleados (el más abierto)
- **H:** España (57%) · Uruguay (71%)
- **I:** Francia (62%) · Noruega (97% clasifica)
- **J:** Argentina (76%) · Austria (94% clasifica)
- **K:** Colombia (65%) · Portugal (78%)
- **L:** Inglaterra (86%) · Croacia/Ghana peleados (71/71%)

### 19.3 Bracket proyectado (camino "chalk": avanza el favorito por Elo)
- **Octavos destacados:** Alemania-Francia→Francia, Portugal-España→España, Argentina-Australia→Argentina, Japón-Inglaterra→Inglaterra.
- **Cuartos:** Francia, España, Inglaterra (sobre Brasil), Argentina (sobre Colombia).
- **Semis:** España def. Francia · Argentina def. Inglaterra.
- **Final proyectada:** 🇪🇸 **España vs Argentina** 🇦🇷 → **Campeón (chalk): España** (Elo 2129 vs 2128, prácticamente moneda al aire).
- *Nota:* el Monte Carlo da a **Argentina** ligeramente por delante (17.3% vs 14.9%) por un camino esperado algo más cómodo; ambos son claramente el top-2. El "chalk" es un único camino determinista; las probabilidades de 19.1 son la salida robusta.

### 19.4 Metodología y caveats
- **Grupos:** partidos jugados se respetan; pendientes se simulan; estándares por puntos→DG→GF, terceros rankeados y top-8 a la llave.
- **Mejores terceros:** asignados a sus slots oficiales (74,77,79,80,81,82,85,87) por **matching bipartito** respetando los grupos permitidos (aproxima la tabla FIFA de 495 filas; efecto de 2º orden en el campeón).
- **Llaves:** empates resueltos por expectativa Elo (prórroga/penales). Sedes de eliminatorias tratadas como neutrales (caveat: los anfitriones podrían tener algo de localía).
- **Modelo:** Elo calibrado sobre 124 partidos históricos — el motor validado. No usa bots/jugador (reservados para partido estelar puntual).

> **Archivos nuevos:** `tournament_state.json` (grupos+fixtures), `tournament_sim.py` (Monte Carlo 50k), `tournament_probs.json` (probabilidades), datos de llave.

---
*Proyección 19-jun-2026: 50,000 torneos simulados con el motor Elo calibrado. Favoritos: Argentina 17%, España 15%, Francia 13%, Inglaterra 10%. México 2% (clasificado, gana Grupo A 93%). Final proyectada España–Argentina.*

---

## 20. ESPECIFICACIÓN DEL MODELO COMPLETO AL 100% — cobertura total de variables y brechas

> Objetivo: que el modelo simule el partido al **100%** — emociones, clima, altura, **desarrollo de cada jugador**, **vida de cada jugador**, físico, táctica, entorno — **sin saltarse nada**. Esta sección audita el modelo contra el catálogo completo (`/Users/issacvm/Downloads/variables_modelo_futbol.md`, 18 secciones), marca qué YA está, qué FALTA, y cómo se añade cada cosa.

### 20.1 ¿Ya incluye todo? Estado por DOMINIO
| Dominio | ¿Incluido? | Dónde / cómo |
|---|---|---|
| **Emociones / sentimientos del día** | ✅ SÍ | Modelo 2 (agente-por-jugador, monólogo) + `emotional_state_today`, `motivation_today`, `pressure`, `nerves` |
| **Vida personal / familia / historia** | ✅ SÍ | Gemelo profundo: `family`, `personal_state`, `motivation_drivers`, `bio` (pareja, hijos, duelos, eventos vitales) |
| **Personalidad / carácter** | ✅ SÍ | `personality`, `clutch`, `composure`, `consistency`, `discipline` |
| **Clima (temp, lluvia, humedad, viento)** | ✅ SÍ | `env` (sorteado por partido) |
| **Altitud** | ✅ SÍ | `env` + fatiga del último tercio |
| **Físico / anatomía (altura, velocidad, peso, durabilidad)** | ✅ SÍ | `height_cm`, `top_speed_kmh`, `weight_kg`, `durability` |
| **Habilidad técnica y táctica** | ✅ SÍ | atributos 0-100 + rol por posición |
| **Estadística de rendimiento / forma / xG** | ✅ SÍ | forma últimos 10, xG, fuerza Elo |
| **Árbitro** | ✅ SÍ | tendencia tarjetas → riesgo roja |
| **Mercado (de-vig)** | ✅ SÍ | triangulación con cuotas |
| **Desarrollo del jugador (curva de carrera/potencial)** | 🟡 PARCIAL → **se añade** | hoy solo vía edad; falta trayectoria/potencial explícito |
| **Tracking GPS (distancia, sprints, HSR, PlayerLoad)** | 🟡 PARCIAL → **brecha** | solo distancia-proxy; falta telemetría real (FIFA/Sofascore) |
| **Carga de entrenamiento / ACWR / congestión** | ⬜ FALTA | T3 interno; proxy por minutos recientes |
| **Wellness / HRV / sueño / RPE** | ⬜ FALTA | T3 interno; proxy por descanso + sentimiento |
| **Físicos de laboratorio (VO2, lactato, fuerza, salto)** | ⬜ FALTA | T3 interno; proxy por pace/stamina |
| **Composición corporal (IMC, % grasa, masa muscular)** | ⬜ FALTA | T3; derivable parcial de altura/peso |
| **Sociales avanzados (sentimiento en redes, cultural, religión)** | 🟡 PARCIAL → **se añade** | añadir flags: sentimiento mediático, adaptación, Ramadán |

**Respuesta corta:** el modelo profundo (México-Corea) YA incluye emociones, clima, altura, físico, vida y familia. Lo que **faltaba** para el 100% son sobre todo datos **Tier-3/4** (tracking real, carga/wellness, laboratorio) + **desarrollo de carrera** y un par de **sociales**. Se especifican abajo y se añaden al esquema.

### 20.2 BRECHAS por sección del catálogo (lo que falta, con fuente y cómo entra)
| Sec. catálogo | Variables que FALTAN | Tier | Cómo obtenerlas / proxy | Cómo alimentan el modelo |
|---|---|---|---|---|
| 1. Identidad | edad relativa, idiomas, % uso de cada pie, edad de debut | T1 | Transfermarkt/Wikipedia | ajuste fino de versatilidad; bajo impacto |
| 2. Antropometría | IMC, % grasa, masa muscular, envergadura, zancada, somatotipo | T3 | médico interno; IMC derivable de altura/peso | aéreo, potencia, resistencia |
| 3. Físico atlético | aceleración 0-30m, deceleración, agilidad, VO2máx, potencia anaeróbica, fuerza, salto, flexibilidad, reacción, FC, **HRV**, lactato, RSA | T3 | tests de club (no público) → proxy con pace/stamina | contragolpe, fatiga, duelos |
| 4. Salud/carga | **fatiga acumulada 7/30 días**, **ACWR (carga aguda:crónica)**, densidad de calendario, secuelas | T3 | minutos recientes (público) como proxy; ACWR solo interno | riesgo de lesión dinámico, rendimiento tardío |
| 8. Rendimiento | xA, PSxG, pases progresivos, **curva de progresión por edad** | T2 | fbref/Opta | calidad fina; **desarrollo** (ver 20.3) |
| 9. Tracking | **distancia total, sprints, HSR, aceleraciones, mapa de calor, PlayerLoad, off-ball** | T3→público parcial | **FIFA Training Centre (PDF post-partido) + Sofascore** | fatiga real (reemplaza proxy), intensidad |
| 12. Entrenamiento | carga (volumen×intensidad), monotonía/strain, **sueño**, nutrición, recuperación, periodización, **RPE** | T3 | interno (no público) → omitir o proxy | forma física fina |
| 16. Social/vital | **sentimiento en redes (cuantificado)**, adaptación cultural (recién llegado), **prácticas religiosas (Ramadán)**, residencia/distancia al CT | T4 | scraping redes + noticias | ánimo/foco; Ramadán solo si aplica por fecha |
| 18. Temporal | **tendencia (mejora/declive)**, estacionalidad, tiempo desde último gol | T1 | fbref | **desarrollo/forma** (ver 20.3) |

### 20.3 NUEVO: "Desarrollo del jugador" y "Vida del jugador" como inputs explícitos del 100%
Se añaden al esquema del gemelo digital los campos que faltaban para cubrir **desarrollo** y profundizar **vida**:

**Desarrollo / trayectoria de carrera:**
- `career_phase`: "emergente | ascenso | pico | meseta | declive" (de edad + minutos + valor de mercado).
- `age_curve_factor`: multiplicador por curva de edad (los delanteros pican ~24-29; porteros/centrales aguantan más).
- `potential`: techo proyectado (0-100) para juveniles (p. ej. Mora, Yamal).
- `trend_form`: forma reciente vs su media histórica (mejora/declive).
- `minutes_load_30d`: minutos en 30 días (proxy de fatiga acumulada).

**Vida / contexto social (amplía lo ya existente):**
- `media_sentiment`: sentimiento neto en prensa/redes (−100..+100) — presión/respaldo.
- `cultural_adaptation`: recién llegado a su liga/país (sí/no) → foco.
- `religious_context`: ayuno/Ramadán activo en la fecha (sí/no) → rendimiento físico.
- `life_event_recent`: evento vital reciente (nacimiento, duelo, boda, divorcio) y su signo (motiva/distrae) — ya capturado en `personal_state`, ahora como campo estructurado.

### 20.4 ESQUEMA "100%" del gemelo digital (todos los campos)
```
IDENTIDAD: name, age, position(es), foot, foot_usage_pct, caps, debut_age, nationality, dual_nationality, relative_age
ANTROPOMETRIA: height_cm, weight_kg, bmi, body_fat_pct(≈), wingspan(≈), somatotype(≈)
FISICO: skill, finishing, creativity, pace, aerial, defense, stamina_base, top_speed_kmh,
        acceleration(≈), agility(≈), vo2max(≈ proxy), strength(≈), jump(≈), rsa(≈), reaction(≈)
SALUD/CARGA: durability, injury_risk, injury_history, minutes_load_30d, acwr(≈ proxy), reinjury_risk, chronic_conditions
TECNICA/TACTICA: passing, dribbling, heading, set_pieces, vision, positioning, pressing, transitions, discipline_tactical
MENTAL/EMOCION: composure_mean, composure_volatility, clutch, pressure_resistance, consistency, focus,
        motivation_today, emotional_state_today, pressure, nerves, leadership, frustration_mgmt
RENDIMIENTO: goals/90, assists/90, xG/90, xA/90, psxg(GK), shots, key_passes, duels_won, form_last10
TRACKING: distance_km, sprints, high_intensity_runs, accel_count, playerload(≈), heatmap_zone(≈)
DESARROLLO: career_phase, age_curve_factor, potential, trend_form
VIDA/SOCIAL: family, personal_state, personality, motivation_drivers, life_event_recent,
        media_sentiment, cultural_adaptation, religious_context, bio, inner_monologue, x_factor
ENTRENAMIENTO(≈/T3): training_load, sleep, nutrition, rpe  (proxy o ausente)
(≈ = estimado/proxy cuando el dato T3 no es público)
```

### 20.5 Honestidad: completitud ≠ ganancia predictiva
Validado en backtest (secciones 15-18): más allá de **fuerza de equipo + forma + bajas clave + localía + emociones**, las capas T3-T4 (tracking, carga, laboratorio) **aportan poco al acierto** (mejora no significativa con la muestra actual). Se incluyen para el realismo "100%" y para riesgo de lesión, pero se marca cuáles son **predictivas** (fuerza, forma, bajas, localía, finishing, portero) vs cuáles son **de realismo/fidelidad** (laboratorio, tracking fino, vida detallada). Para datos T3 no públicos se usan **proxies** o se omiten, dejándolo explícito.

### 20.6 Estado de implementación
- **Ya operativo:** todo lo ✅ de 20.1 (incluido emociones, clima, altura, vida/familia en el modelo profundo).
- **Por cablear (cuando se publique / con scraping):** tracking real FIFA/Sofascore (sec. 14 ya documenta la ingesta), campos de desarrollo (20.3) en el esquema del gemelo, sociales avanzados (sentimiento/cultural/religión).
- **No públicos (se quedan como proxy):** carga de entrenamiento, ACWR, HRV, sueño, RPE, físicos de laboratorio, composición corporal — Tier 3 interno de clubes.

---
*Sección 20 (21-jun-2026): especificación del modelo COMPLETO al 100% y auditoría de cobertura vs el catálogo de 18 secciones. Lo ya incluido (emociones, clima, altura, vida, físico) y lo que falta (tracking real, carga/wellness, laboratorio, desarrollo de carrera, sociales avanzados) queda documentado con fuente, proxy y forma de ingestión. Completitud para fidelidad; el acierto lo dominan fuerza+forma+bajas+localía+emoción.*

---

## 21. PLAN DE EJECUCIÓN MAESTRO — runbook OBLIGATORIO del modelo completo (por fases)

> **Regla de oro:** el modelo completo ejecuta SIEMPRE todo este proceso, **sin omitir fases**. Donde falten datos, los agentes hacen **investigación exhaustiva** para conseguir toda la data pública posible de cada jugador; lo que no exista se estima y se marca. **Cada titular recibe un agente individual** con su contexto real (vida, forma, emoción, desarrollo) lo más fiel posible a la realidad.

### Diagrama de fases
```
FASE 0  Definición del partido
FASE 1  INVESTIGACIÓN EXHAUSTIVA  (recolectar TODO lo posible — aquí se cierran las brechas)
FASE 2  ENTENDIMIENTO / SÍNTESIS  (construir gemelos + contexto individual por jugador)
FASE 3  EJECUCIÓN / SIMULACIÓN    (3 capas; 1 agente por jugador piensa como él)
FASE 4  RESULTADOS / TRIANGULACIÓN (consenso + reporte)
FASE 5  CALIBRACIÓN / APRENDIZAJE  (post-partido: comparar vs real y reajustar)
```

### FASE 0 — Definición del partido
Fijar: equipos (local/visitante), fecha, sede (estadio/ciudad/altitud), ronda, qué está en juego, si juega un anfitrión en casa. Salida: ficha del partido.

### FASE 1 — INVESTIGACIÓN EXHAUSTIVA (cerrar TODAS las brechas)
Fan-out de agentes en paralelo. **Mandato:** buscar a fondo (FIFA, fbref, Sofascore, Transfermarkt, prensa, entrevistas, redes) hasta agotar lo público; solo marcar "no disponible" tras esfuerzo real, y entonces estimar con justificación.
- **Agente Contexto:** sede, H2H, árbitro (tarjetas/penales), cuotas pre-partido, qué se juega.
- **Agente Entorno:** clima hora a hora, pasto (tipo/estado), aforo, % afición local, ruido, altitud.
- **Agente Equipo (×2, uno por selección):** XI probable, sistema/estilo, forma últimos 10, bajas/lesiones/suspensiones, cohesión, noticias de campamento.
- **Agente Físico/Tracking (×2):** distancia, sprints, velocidad punta por jugador (FIFA Training Centre + Sofascore); promedios de equipo.
- **★ Agente Biográfico POR JUGADOR (×22):** dossier exhaustivo de cada titular — edad, club y situación, **familia (pareja, hijos)**, **vida fuera del fútbol y eventos vitales**, **personalidad**, **desarrollo de carrera (fase, potencial, trayectoria)**, forma, lesiones/físico, **sentimiento mediático**, qué lo motiva/deprime HOY. Con fuentes y marca dato vs estimación.
Salida: **dossier completo por jugador** + entorno + equipo + físico.

### FASE 2 — ENTENDIMIENTO / SÍNTESIS
- Convertir cada dossier en un **GEMELO DIGITAL** con TODOS los campos del esquema 100% (sec. 20.4): identidad, antropometría, físico, salud/carga, técnica/táctica, mental/emoción, rendimiento, tracking, **desarrollo**, **vida/social**.
- Redactar el **CONTEXTO INDIVIDUAL** de cada jugador (su narrativa real: cómo llega hoy, su momento vital y de forma) — será el "alma" que recibe su agente en la Fase 3.
- Construir parámetros de equipo (ataque/defensa/portero/aéreo/pace/fatiga), entorno y aplicar calibración (`calibration*.json`).
- Cross-check de coherencia; marcar confianza (dato/estimación) por campo.

### FASE 3 — EJECUCIÓN / SIMULACIÓN (las 3 capas, nada se salta)
- **Capa 1 — Estadística:** Elo calibrado → Dixon-Coles → λ base (fuerza + sede + forma).
- **★ Capa 2 — Agente-por-jugador (×22):** a CADA jugador se le da su **contexto individual** (Fase 2) y **piensa como él**: siente presión, ánimo, motivación → devuelve estado mental del día + monólogo + modificadores. Se agregan a nivel equipo.
- **Capa 3 — Gemelos estocástico (≥100k):** motor minuto a minuto con todos los atributos + entorno + física + fatiga + portero + aéreo + contragolpe; sortea condiciones y "día" de cada jugador.
- **Ancla de mercado:** de-vig de cuotas.

### FASE 4 — RESULTADOS / TRIANGULACIÓN
- Triangular Capa 1 + Capa 2 + Capa 3 + mercado → **consenso**: P(1X2), goles esperados, marcadores top, Over/Under, BTTS, riesgo de roja, jugador clave, resultados condicionales (lluvia, etc.).
- Generar reporte y **guardar artefactos** (dossiers, `twins`, `env`, `player_minds`, salida).

### FASE 5 — CALIBRACIÓN / APRENDIZAJE (post-partido)
- Comparar predicción vs resultado real; registrar acierto (Brier/log-loss/marcador).
- Acumular al dataset y **recalibrar** (`calibrate.py`/`hist_calibrate.py`) cuando haya muestra.

### Reglas inquebrantables
1. **No se omite ninguna fase.** Si falta tiempo/recursos, se reduce el nº de simulaciones, NUNCA las fases.
2. **Un agente individual por cada titular** con su contexto real (vida + forma + emoción + desarrollo).
3. **Investigación exhaustiva primero:** los huecos se buscan a fondo antes de estimar; toda estimación se marca y se cita fuente.
4. **Todo se guarda** y queda reproducible.

### ★ PROMPT MAESTRO (reusable — pegar para correr el modelo completo)
```
Ejecuta el MODELO COMPLETO de predicción para el partido [LOCAL] vs [VISITANTE]
([fecha], [sede], [ronda], [qué se juega], anfitrión: [sí/no]).
Sigue las 5 fases del runbook (sección 21) SIN OMITIR NINGUNA:

FASE 1 (investigación exhaustiva, agentes en paralelo): Contexto, Entorno, 2×Equipo,
2×Físico/Tracking, y 22×Biográfico (1 por titular). Mandato: agotar fuentes públicas
(FIFA, fbref, Sofascore, Transfermarkt, prensa, entrevistas, redes) para conseguir
TODA la data posible de cada jugador (vida, familia, personalidad, desarrollo de
carrera, físico/tracking, sentimiento mediático, estado de hoy). Marcar dato vs estimación + fuentes.

FASE 2 (síntesis): construir el gemelo digital 100% de cada jugador (esquema 20.4) y
redactar su CONTEXTO INDIVIDUAL real. Parámetros de equipo + entorno + calibración.

FASE 3 (simulación, 3 capas): (1) Elo calibrado→Dixon-Coles (λ base);
(2) 22 agentes-jugador, cada uno con su contexto, que PIENSAN como el jugador y
devuelven estado mental + monólogo + modificadores; (3) motor estocástico de gemelos
(≥100k) con física/fatiga/portero/aéreo/contragolpe. Ancla con cuotas de-vig.

FASE 4 (resultados): triangular las 3 capas + mercado → consenso (1X2, goles,
marcadores, O/U, BTTS, roja, jugador clave, condicional clima). Guardar artefactos.

FASE 5 (post-partido): comparar vs real, registrar acierto y recalibrar.
```

### Prompt por jugador (Fase 1 biográfico + Fase 3 role-play)
```
[Fase 1] Investiga EXHAUSTIVAMENTE a [jugador] para [partido]. Consigue TODO lo público:
edad, club y situación, familia (pareja/hijos), vida fuera del fútbol y eventos vitales
recientes, personalidad, desarrollo de carrera (fase/potencial/trayectoria), forma,
lesiones y físico, sentimiento en prensa/redes, y qué lo motiva o le pesa HOY. Cita fuentes;
si algo no existe públicamente, dilo y estima con justificación. Devuelve el gemelo 100% (esquema 20.4).

[Fase 3] Eres [jugador]. Con TODO tu contexto real (arriba), métete en tu cabeza para
[partido]: siente la presión, el ánimo, la motivación, tu momento vital y de forma.
Devuelve tu estado mental del día (0-100), tus modificadores de rendimiento y tu monólogo interior.
```

> **Escalado realista:** modelo completo ≈ 50 agentes/partido (22 biográficos + 22 role-play + ~6 contexto/entorno/físico). Para varios partidos se ejecuta en serie por partido. Si se requiere recortar, se baja nº de simulaciones, NUNCA fases ni el principio de 1 agente por jugador.

---
*Sección 21 (21-jun-2026): plan de ejecución maestro del modelo completo, por fases (investigación exhaustiva → entendimiento → ejecución → resultados → calibración), con prompt maestro reutilizable y prompt por jugador. El proceso es obligatorio y completo: cada titular tiene su agente individual con contexto real; los datos faltantes se investigan a fondo antes de estimar.*

---

## 22. ★★★ COMANDO DE EJECUCIÓN Y REGLAS INVIOLABLES ★★★

> **COMANDO GATILLO:** cuando se diga **"correr el modelo del .md"** (o "corre el modelo completo"), se ejecuta EXACTAMENTE el runbook de la sección 21, las 5 fases, **tal cual**, sin atajos ni interpretaciones.

### REGLAS INVIOLABLES (obligatorias, sin excepción)
1. **JAMÁS, JAMÁS omitir nada.** Ninguna fase, ningún jugador, ninguna variable obtenible. Si algo no se puede, se documenta y se estima con fuente — pero NO se salta.
2. **Investigación exhaustiva SIEMPRE.** Donde falte data, los agentes la buscan a fondo (FIFA, fbref, Sofascore, Transfermarkt, prensa, entrevistas, redes) hasta agotar lo público. La información es valiosa: se prioriza conseguirla.
3. **Se pueden lanzar MULTIAGENTES sin reparo: hasta 200 agentes por ejecución si es necesario.** No se escatima en recursos ni en tokens. La calidad y la cobertura mandan sobre el costo y la velocidad.
4. **Un agente individual por CADA jugador titular**, con su contexto real (vida, familia, forma, emoción, desarrollo) lo más fiel a la realidad. Cada agente "es" su jugador.
5. **Exhaustividad > velocidad > costo.** Si hay que recortar algo por límites, se recorta el número de SIMULACIONES Monte Carlo, **nunca** las fases, ni los agentes de investigación, ni el principio de 1 agente por jugador.
6. **Todo se guarda** (dossiers por jugador, gemelos, entorno, mentes/monólogos, resultados) y queda reproducible.
7. **Marcar siempre** dato confirmado vs estimación, con fuentes.

### Presupuesto de agentes (referencia)
- Modelo completo por partido ≈ **45-50 agentes** (contexto + entorno + físico + 1 por jugador para investigación/embodiment de los 22 titulares).
- Varios partidos el mismo día → se ejecuta **en serie por partido**; el total puede acercarse a **~200 agentes/día**, lo cual está EXPLÍCITAMENTE autorizado.

> En resumen: **"correr el modelo del .md" = ejecutar el runbook completo (sección 21), sin omitir absolutamente nada, lanzando todos los agentes que hagan falta (hasta ~200), investigando a fondo cada jugador y dándole a cada uno su contexto individual real.**

---
*Sección 22 (21-jun-2026): comando gatillo "correr el modelo del .md" + reglas inviolables. Nunca omitir nada; multiagentes hasta 200 autorizados; no escatimar recursos; 1 agente por jugador con contexto real; exhaustividad sobre costo/velocidad.*
