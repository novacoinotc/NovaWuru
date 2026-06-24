// ===== Momios reales vía The Odds API (https://the-odds-api.com) =====
// Plan gratis: 500 req/mes. Sin key -> el engine usa cuotas sintéticas (fallback).

const ALIASES: Record<string, string> = {
  "usa": "united states",
  "korea republic": "south korea",
  "czechia": "czech republic",
  "ivory coast": "cote d ivoire",
  "cote d'ivoire": "cote d ivoire",
  "turkiye": "turkey",
  "cabo verde": "cape verde",
  "dr congo": "dr congo",
  "bosnia and herzegovina": "bosnia and herzegovina",
};
function canon(s: string): string {
  const n = s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z ]/g, "").trim();
  return ALIASES[n] ?? n;
}

export type OddsEntry = {
  home: string; away: string;
  kickoff?: string;               // fecha/hora real del partido (ISO, UTC)
  h2h: Record<string, number>;   // por nombre de equipo y "Draw"
  totals: Record<string, number>; // "Over" / "Under" (línea 2.5)
};

/** Trae los momios actuales (mediana de casas) para TODAS las ligas configuradas. */
export async function fetchOdds(): Promise<OddsEntry[]> {
  const key = process.env.ODDS_API_KEY;
  if (!key) return [];
  // ODDS_SPORT_KEYS (lista separada por comas) o ODDS_SPORT_KEY (una sola)
  const sports = (process.env.ODDS_SPORT_KEYS || process.env.ODDS_SPORT_KEY || "soccer_fifa_world_cup")
    .split(",").map((s) => s.trim()).filter(Boolean);
  const regions = process.env.ODDS_REGIONS || "us,uk,eu";
  const all: any[] = [];
  for (const sport of sports) {
    try {
      const url = `https://api.the-odds-api.com/v4/sports/${sport}/odds?regions=${regions}&markets=h2h,totals&oddsFormat=decimal&apiKey=${key}`;
      const res = await fetch(url, { cache: "no-store" });
      if (res.ok) all.push(...((await res.json()) as any[]));
    } catch { /* liga sin datos / off-season: ignorar */ }
  }
  const data = all;
  const median = (a: number[]) => { if (!a.length) return 0; const s = [...a].sort((x, y) => x - y); const m = Math.floor(s.length / 2); return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  return data.map((ev) => {
    const h2hA: Record<string, number[]> = {}, totA: Record<string, number[]> = {};
    for (const bk of ev.bookmakers ?? []) {
      for (const mk of bk.markets ?? []) {
        for (const o of mk.outcomes ?? []) {
          if (o.price < 1.01 || o.price > 100) continue; // descarta líneas corruptas
          if (mk.key === "h2h") {
            const k = o.name === "Draw" ? "Draw" : o.name;
            (h2hA[k] ??= []).push(o.price);
          } else if (mk.key === "totals" && Math.abs((o.point ?? 0) - 2.5) < 0.01) {
            (totA[o.name] ??= []).push(o.price);
          }
        }
      }
    }
    const h2h: Record<string, number> = {}, totals: Record<string, number> = {};
    for (const k in h2hA) h2h[k] = median(h2hA[k]);   // consenso (mediana), robusto a outliers
    for (const k in totA) totals[k] = median(totA[k]);
    return { home: ev.home_team, away: ev.away_team, kickoff: ev.commence_time, h2h, totals };
  });
}

/** Empareja un partido (nuestros nombres) con un evento de la API. */
export function findEntry(list: OddsEntry[], home: string, away: string): OddsEntry | undefined {
  const h = canon(home), a = canon(away);
  return list.find((e) => {
    const eh = canon(e.home), ea = canon(e.away);
    return (eh === h && ea === a) || (eh === a && ea === h);
  });
}

/** Devuelve la cuota real para un (mercado, selección) o null si no existe. */
export function realOdds(
  entry: OddsEntry | undefined, market: string, selection: string, predHome: string, predAway: string
): number | null {
  if (!entry) return null;
  if (market === "1X2") {
    const sel = canon(selection);
    if (sel === canon(predHome) || sel === canon(predAway)) {
      // emparejar por NOMBRE de equipo (no por posición local/visitante)
      for (const k of Object.keys(entry.h2h)) if (k !== "Draw" && canon(k) === sel) return entry.h2h[k];
      return null;
    }
    return entry.h2h["Draw"] ?? null; // Empate
  }
  if (market === "O/U 2.5") {
    return selection.startsWith("Over") ? entry.totals["Over"] ?? null : entry.totals["Under"] ?? null;
  }
  return null; // BTTS no viene en h2h/totals -> fallback sintético
}

export const oddsReady = () => !!process.env.ODDS_API_KEY;
