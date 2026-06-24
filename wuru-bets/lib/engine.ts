import { sql } from "./db";
import { ev, impliedProb, stakeFor, devig } from "./betting";
import { fetchOdds, findEntry, realOdds, type OddsEntry } from "./odds";

// Defensas anti-error-de-modelo: el mercado (consenso de casas) es afilado.
const W_MODEL = 0.30;   // peso de nuestro modelo; 0.70 al mercado (de-vig)
const EDGE_CAP = 0.15;  // edge > 15% casi siempre es error del modelo, no valor real
const MAX_ODDS = 7.0;   // evita longshots donde domina el error del modelo

export type Pred = {
  id: string; sport: string; league: string; home: string; away: string;
  kickoff?: string; markets: { market: string; selection: string; prob: number }[];
};

const SHADE = 0.12, MARGIN = 1.045;

// PRNG determinista por corrida
function makeRng(seed: number) {
  let s = seed >>> 0;
  return () => { s = (s + 0x6d2b79f5) | 0; let t = s; t = Math.imul(t ^ (t >>> 15), 1 | t); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

/** Sintetiza cuota de mercado a partir de la prob del modelo (hasta conectar feed real de momios). */
export function syntheticOdds(prob: number, rnd: () => number): number {
  const shade = 1 + (rnd() - 0.5) * 2 * SHADE;
  const odds = (1 / (prob * shade)) / MARGIN;
  return Math.min(Math.round(odds * 100) / 100, 21);
}

/** Coloca apuestas de valor (paper) a partir de predicciones. Devuelve resumen. */
export async function placeBets(
  preds: Pred[],
  opts: { reset?: boolean; evThreshold?: number; fraction?: number; maxPct?: number; seed?: number } = {}
) {
  const EV_TH = opts.evThreshold ?? Number(process.env.EV_THRESHOLD || 0.05);
  const FRAC = opts.fraction ?? Number(process.env.KELLY_FRACTION || 0.25);
  const MAXPCT = opts.maxPct ?? Number(process.env.MAX_STAKE_PCT || 0.03);
  const rnd = makeRng(opts.seed ?? 424242);

  // Momios reales (si hay ODDS_API_KEY); si no, fallback sintético.
  let oddsList: OddsEntry[] = [];
  try { oddsList = await fetchOdds(); } catch { oddsList = []; }

  if (opts.reset) await sql`truncate bets, matches, bankroll_history restart identity cascade`;
  const b = (await sql`select starting from bankroll where id=1`)[0] as any;
  const starting = Number(b?.starting ?? 100000);
  if (opts.reset) await sql`update bankroll set current=${starting} where id=1`;

  let placed = 0, exposure = 0;
  const now = Date.now();
  for (let i = 0; i < preds.length; i++) {
    const p = preds[i];
    const kickoff = p.kickoff ? new Date(p.kickoff) : new Date(now + (1 + i * 0.4) * 86400000);
    await sql`insert into matches (ext_id, sport, league, home, away, kickoff, status)
      values (${p.id}, ${p.sport}, ${p.league}, ${p.home}, ${p.away}, ${kickoff}, 'scheduled')
      on conflict (ext_id) do update set kickoff=excluded.kickoff`;
    const matchId = (await sql`select id from matches where ext_id=${p.id}`)[0].id;
    const entry = findEntry(oddsList, p.home, p.away);
    // evitar duplicar apuestas abiertas del mismo partido
    await sql`delete from bets where match_id=${matchId} and status='open'`;

    const haveReal = oddsList.length > 0;
    // agrupar por mercado para poder de-viguear (quitar margen) cada mercado completo
    const groups: Record<string, typeof p.markets> = {};
    for (const mk of p.markets) (groups[mk.market] ??= []).push(mk);

    for (const market in groups) {
      const sels = groups[market];
      const selOdds = sels.map((s) => realOdds(entry, market, s.selection, p.home, p.away));
      if (haveReal && selOdds.some((o) => o == null)) continue; // sin mercado real completo (p.ej. BTTS) -> saltar
      const marketProbs = haveReal && selOdds.length >= 2 ? devig(selOdds as number[]) : sels.map(() => null);

      for (let j = 0; j < sels.length; j++) {
        const model = Number(sels[j].prob);
        if (model < 0.05) continue;
        const odds = haveReal ? (selOdds[j] as number) : syntheticOdds(model, rnd);
        const source = haveReal ? "real" : "synthetic";
        const mProb = marketProbs[j];
        // prob efectiva = mezcla modelo + mercado (el mercado pesa más, es afilado)
        const effProb = haveReal && mProb != null ? W_MODEL * model + (1 - W_MODEL) * mProb : model;
        const edge = ev(effProb, odds);
        if (edge < EV_TH || edge > EDGE_CAP || odds < 1.2 || odds > MAX_ODDS) continue;
        const stake = stakeFor(starting, effProb, odds, { fraction: FRAC, maxPct: MAXPCT });
        if (stake < 50) continue;
        const ret = Math.round(stake * (odds - 1));
        await sql`insert into bets (match_id, market, selection, model_prob, odds_taken, implied_prob, edge, stake, potential_return, opening_odds, odds_source, status)
          values (${matchId}, ${market}, ${sels[j].selection}, ${effProb}, ${odds}, ${impliedProb(odds)}, ${edge}, ${stake}, ${ret}, ${odds}, ${source}, 'open')`;
        placed++; exposure += stake;
      }
    }
  }
  // saldo disponible = inicial - exposición abierta + retornos liquidados
  const realized = (await sql`select coalesce(sum(case when status='won' then potential_return when status='lost' then -stake else 0 end),0) as r from bets`)[0].r;
  const openExp = (await sql`select coalesce(sum(stake),0) as e from bets where status='open'`)[0].e;
  await sql`update bankroll set current=${starting - Number(openExp) + Number(realized)}, updated_at=now() where id=1`;
  return { placed, exposure, matches: preds.length };
}
