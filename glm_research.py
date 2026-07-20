#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Research runner con GLM 5.2 (z.ai, endpoint Anthropic-compatible + web search), PARALELO.
Arma match_<ID>.json compatible con sim_match.py. Reusable: research_match(meta).
CLI: python3 glm_research.py ID "Home" "Away" GRUPO "Sede" [HostNation]
"""
import json, sys, re, os, time, urllib.request, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = os.environ.get("GLM_API_KEY") or ""
if not KEY:
    try:
        for line in open(os.path.join(os.path.dirname(__file__) or ".", "wuru-bets/.env"), encoding="utf-8"):
            if line.startswith("GLM_API_KEY="): KEY = line.strip().split("=", 1)[1]
    except Exception: pass
BASE = "https://api.z.ai/api/anthropic/v1/messages"
MODEL = "glm-4.6"
_lock = threading.Lock()
USAGE = {"in": 0, "out": 0, "calls": 0}

def glm(prompt, web=True, max_tokens=1800, retries=5):
    body = {"model": MODEL, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
    if web: body["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(BASE, data=json.dumps(body).encode(),
                headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=150))
            u = d.get("usage", {})
            with _lock:
                USAGE["in"] += u.get("input_tokens", 0); USAGE["out"] += u.get("output_tokens", 0); USAGE["calls"] += 1
            return "".join(c.get("text", "") for c in d.get("content", []) if c.get("type") == "text")
        except urllib.error.HTTPError as e:
            if attempt == retries: raise
            time.sleep(20 * (attempt + 1) if e.code == 429 else 5)  # 429 = rate limit -> backoff largo
        except Exception:
            if attempt == retries: raise
            time.sleep(5)

def parse_json(text):
    t = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    clean = lambda s: re.sub(r",\s*([}\]])", r"\1", s)
    try: return json.loads(clean(t))
    except Exception: pass
    for pat in (r"\[.*\]", r"\{.*\}"):  # array primero (XI), luego objeto (gemelo)
        m = re.search(pat, t, re.DOTALL)
        if m:
            try: return json.loads(clean(m.group(0)))
            except Exception: continue
    raise ValueError("JSON no parseable")

FILLER = dict(age=26, skill=68, finishing=55, creativity=58, pace=62, aerial=62, defense=60, stamina_base=70,
    composure_mean=68, composure_volatility=14, clutch=65, pressure_resistance=66, discipline=70, consistency=68,
    motivation_today=80, emotional_state_today=75, injury_risk=15, height_cm=180, top_speed_kmh=32, durability=72,
    career_phase="pico", family="", personal_state="(dato no disponible)", inner_monologue="", sources="filler")
def filler(name, pos): return {"name": name, "position": pos, **FILLER}

TWIN = ('{"name","position","age":int,"skill":0-100,"finishing":0-100,"creativity":0-100,"pace":0-100,'
  '"aerial":0-100,"defense":0-100,"stamina_base":0-100,"composure_mean":0-100,"composure_volatility":0-35,'
  '"clutch":0-100,"pressure_resistance":0-100,"discipline":0-100,"consistency":0-100,"motivation_today":0-100,'
  '"emotional_state_today":0-100,"injury_risk":0-100,"height_cm":int,"top_speed_kmh":num,"durability":0-100,'
  '"career_phase":"emergente|ascenso|pico|meseta|declive","family":"...","personal_state":"...","inner_monologue":"...","sources":"..."}')

def get_xi(team, opp, ctx):
    p = f"Investiga (web search) el XI PROBABLE de {team} vs {opp}. {ctx}\nResponde SOLO JSON array de 11: [{{\"name\":\"...\",\"position\":\"...\"}}]. Sin texto extra."
    return parse_json(glm(p))[:11]

def get_twin(name, pos, team, opp, ctx):
    p = (f"Eres un analista de scouting de élite. Investiga EXHAUSTIVAMENTE con WEB SEARCH a {name} ({pos}) de {team}, "
         f"de cara al partido vs {opp}. {ctx}\n\n"
         f"Haz MÚLTIPLES búsquedas y profundiza en TODO:\n"
         f"1) FORMA RECIENTE: rendimiento en sus últimos 5-10 partidos (goles, asistencias, minutos, rating), club y selección.\n"
         f"2) FÍSICO/LESIONES: estado físico actual, lesiones recientes o molestias, minutos acumulados, fatiga, riesgo.\n"
         f"3) DATOS REALES: edad exacta, estatura, velocidad punta, pierna hábil, rol táctico específico.\n"
         f"4) VIDA Y PSICOLOGÍA: familia (pareja, hijos), origen, historia personal, presión mediática, motivación hoy, estado emocional.\n"
         f"5) MENTALIDAD: temple bajo presión, historial en partidos grandes/clutch, disciplina (tarjetas), consistencia.\n\n"
         f"Traduce TODO a los atributos numéricos (fundamentados en lo que encontraste, no inventes). "
         f"Escribe un MONÓLOGO INTERIOR largo y vívido (250+ palabras, en primera persona) que capture su cabeza HOY. "
         f"En 'sources' lista las URLs/medios reales que consultaste.\n\n"
         f"Responde SOLO JSON: {TWIN}. Sin texto extra.")
    for attempt in range(2):  # reintento si el JSON viene mal
        try:
            t = parse_json(glm(p, max_tokens=4200)); t["name"] = t.get("name", name); t["position"] = t.get("position", pos)
            return t
        except Exception:
            if attempt == 1: raise
            time.sleep(2)

def get_env(home, away, venue, comp="Mundial 2026"):
    p = (f"Investiga (web search) condiciones de {home} vs {away} en {venue} ({comp}).\n"
         'Responde SOLO JSON: {"rain_probability_kickoff":0-1,"temp_c_kickoff":num,"humidity_pct":num,"wind_kmh":num,'
         '"pitch_type":"...","pitch_speed_factor":num,"stadium_capacity":int,"home_support_pct":0-1,"crowd_noise":0-100,"notes":"..."}. Sin texto.')
    e = parse_json(glm(p))
    if e.get("crowd_noise", 0) > 100: e["crowd_noise"] = 95
    if e.get("home_support_pct", 0) > 1: e["home_support_pct"] = e["home_support_pct"] / 100.0
    return e

def research_match(meta, workers=6, verbose=True):
    home, away, venue = meta["home"], meta["away"], meta.get("venue", "sede neutral")
    host = meta.get("host", "")
    comp = meta.get("comp", "Mundial 2026")
    ctx = f"{meta.get('group','')}, {venue}, {comp}." + (f" {host} juega en casa (ventaja local)." if host else " Sede neutral.")
    t0 = time.time()
    def pad_xi(xi):
        xi = xi[:11]
        while len(xi) < 11: xi.append({"name": f"Jugador {len(xi)+1}", "position": "MF"})
        return xi
    with ThreadPoolExecutor(workers) as ex:
        fenv = ex.submit(get_env, home, away, venue, comp)
        fH = ex.submit(get_xi, home, away, ctx); fA = ex.submit(get_xi, away, home, ctx)
        env = fenv.result(); xiH = pad_xi(fH.result()); xiA = pad_xi(fA.result())
        futs = {ex.submit(get_twin, pl["name"], pl["position"], home, away, ctx): ("home", pl) for pl in xiH}
        futs.update({ex.submit(get_twin, pl["name"], pl["position"], away, home, ctx): ("away", pl) for pl in xiA})
        got = {"home": {}, "away": {}}
        for f in as_completed(futs):
            side, pl = futs[f]
            try: got[side][pl["name"]] = f.result()
            except Exception: pass
    # garantizar 11 por equipo: reintento secuencial de los que faltaron, relleno si falla
    def finalize(side, xi, opp):
        res = []
        for pl in xi:
            t = got[side].get(pl["name"])
            if t is None:
                try: t = get_twin(pl["name"], pl["position"], home if side == "home" else away, opp, ctx)
                except Exception: t = filler(pl["name"], pl["position"])
            res.append(t)
        return res[:11]
    H = finalize("home", xiH, away); A = finalize("away", xiA, home)
    out = {"meta": meta, "env": env, "home": {"team": home, "players": H}, "away": {"team": away, "players": A}}
    json.dump(out, open(f"match_{meta['id']}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if verbose: print(f"  ✅ {meta['id']}: {len(H)}v{len(A)} jugadores en {time.time()-t0:.0f}s")
    return out

def main():
    _id, home, away, group, venue = sys.argv[1:6]
    host = sys.argv[6] if len(sys.argv) > 6 else ""
    research_match({"id": _id, "home": home, "away": away, "group": group, "venue": venue, "host": host})
    print(f"   GLM: {USAGE['calls']} llamadas | {USAGE['in']:,} in | {USAGE['out']:,} out")

if __name__ == "__main__":
    main()
