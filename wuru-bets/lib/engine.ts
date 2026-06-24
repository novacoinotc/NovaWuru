import { sql } from "./db";
import { ev, impliedProb, stakeFor, devig } from "./betting";
import { fetchOdds, findEntry, realOdds, type OddsEntry } from "./odds";

// Defensas anti-error-de-modelo: el mercado (consenso de casas) es afilado.
const W_MODEL = 0.30;   // peso de nuestro modelo; 0.70 al mercado (de-vig)
const EDGE_CAP = 0.15;  // edge > 15% casi siempre es error del modelo, no valor real
const MAX_ODDS = 7.0;   // evita longshots donde domina el error del modelo

// ===== Apuestas Soñadoras (billete de loteria con cabeza) =====
const DREAM_MIN_P = Number(process.env.DREAM_MIN_PROB || 0.45);  // legs de prob media-alta...
const DREAM_MAX_P = Number(process.env.DREAM_MAX_PROB || 0.72);  // ...pero no casi-seguras (pagan poco)
const DREAM_STAKE = Number(process.env.DREAM_STAKE || 100);      // monto fijo minimo
const DREAM_MULT_MIN = Number(process.env.DREAM_MULT_MIN || 7);  // multiplicador combinado minimo
const DREAM_MAX_LEGS = Number(process.env.DREAM_MAX_LEGS || 6);
const DREAM_MAX_OPEN = Number(process.env.DREAM_MAX_OPEN || 2);  // cuantas soñadoras abiertas a la vez

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

  // dedup: mismo partido puede venir con varios IDs (archivos viejos _GLM, etc.) -> 1 solo por fixture
  const fxKey = (h: string, a: string) => (h + "|" + a).toLowerCase().normalize("NFD").replace(/[^a-z0-9|]/g, "");
  const seenFx = new Set<string>();
  const uniqPreds = preds.filter((p) => { const k = fxKey(p.home, p.away); if (seenFx.has(k)) return false; seenFx.add(k); return true; });

  let placed = 0, exposure = 0;
  const placedBets: { id: number; prob: number; odds: number; matchId: number; source: string }[] = [];
  // candidatos para Apuestas Soñadoras: mejor leg 1X2 (prob media-alta) por partido
  const dreamCands: { matchId: number; fx: string; selection: string; prob: number; odds: number }[] = [];
  const now = Date.now();
  for (let i = 0; i < uniqPreds.length; i++) {
    const p = uniqPreds[i];
    const kickoff = p.kickoff ? new Date(p.kickoff) : new Date(now + (1 + i * 0.4) * 86400000);
    await sql`insert into matches (ext_id, sport, league, home, away, kickoff, status)
      values (${p.id}, ${p.sport}, ${p.league}, ${p.home}, ${p.away}, ${kickoff}, 'scheduled')
      on conflict (ext_id) do update set kickoff=excluded.kickoff`;
    const matchId = (await sql`select id from matches where ext_id=${p.id}`)[0].id;
    const entry = findEntry(oddsList, p.home, p.away);

    const haveReal = oddsList.length > 0;
    // agrupar por mercado para poder de-viguear (quitar margen) cada mercado completo
    const groups: Record<string, typeof p.markets> = {};
    for (const mk of p.markets) (groups[mk.market] ??= []).push(mk);

    for (const market in groups) {
      const sels = groups[market];
      const selOdds = sels.map((s) => realOdds(entry, market, s.selection, p.home, p.away));
      if (haveReal && selOdds.some((o) => o == null)) continue; // sin mercado real completo (p.ej. BTTS) -> saltar
      const marketProbs = haveReal && selOdds.length >= 2 ? devig(selOdds as number[]) : sels.map(() => null);

      // === Soñadoras: registra el mejor leg 1X2 (prob media-alta) con momio real de este partido ===
      if (market === "1X2" && haveReal) {
        let best: { selection: string; prob: number; odds: number } | null = null;
        for (let j = 0; j < sels.length; j++) {
          const mProb = marketProbs[j];
          const eff = mProb != null ? W_MODEL * Number(sels[j].prob) + (1 - W_MODEL) * mProb : Number(sels[j].prob);
          const o = selOdds[j] as number;
          if (eff >= DREAM_MIN_P && eff <= DREAM_MAX_P && o >= 1.4 && o <= 3.2) {
            if (!best || eff > best.prob) best = { selection: sels[j].selection, prob: eff, odds: o };
          }
        }
        if (best) dreamCands.push({ matchId, fx: fxKey(p.home, p.away), ...best });
      }

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
        // si ya tenemos esta apuesta abierta (de una corrida anterior), la MANTENEMOS al momio temprano
        const dup = await sql`select 1 from bets where match_id=${matchId} and market=${market} and selection=${sels[j].selection} and status='open' limit 1`;
        if (dup.length) continue;
        const stake = stakeFor(starting, effProb, odds, { fraction: FRAC, maxPct: MAXPCT });
        if (stake < 50) continue;
        const ret = Math.round(stake * (odds - 1));
        const ins = await sql`insert into bets (match_id, market, selection, model_prob, odds_taken, implied_prob, edge, stake, potential_return, opening_odds, odds_source, status)
          values (${matchId}, ${market}, ${sels[j].selection}, ${effProb}, ${odds}, ${impliedProb(odds)}, ${edge}, ${stake}, ${ret}, ${odds}, ${source}, 'open') returning id`;
        placedBets.push({ id: Number(ins[0].id), prob: effProb, odds, matchId, source });
        placed++; exposure += stake;
      }
    }
  }

  // ===== PARLEYS: combina las legs mas seguras (prob alta) de partidos DISTINTOS =====
  const safe = placedBets.filter((b) => b.source === "real" && b.prob >= 0.55).sort((a, b) => b.prob - a.prob);
  const seenM = new Set<number>(); const legs: typeof safe = [];
  for (const b of safe) { if (!seenM.has(b.matchId)) { seenM.add(b.matchId); legs.push(b); } if (legs.length >= 3) break; }
  if (legs.length >= 2) {
    const codds = legs.reduce((a, b) => a * b.odds, 1);
    const cprob = legs.reduce((a, b) => a * b.prob, 1);
    const pev = cprob * codds - 1;
    if (pev > 0) {
      const pstake = Math.min(Math.round(starting * 0.01), stakeFor(starting, cprob, codds, { fraction: FRAC, maxPct: 0.01 }));
      if (pstake >= 50) {
        const pret = Math.round(pstake * (codds - 1));
        const pins = await sql`insert into bets (match_id, market, selection, model_prob, odds_taken, implied_prob, edge, stake, potential_return, opening_odds, odds_source, status)
          values (${null}, 'Parlay', ${legs.length + " legs seguras"}, ${cprob}, ${Math.round(codds * 100) / 100}, ${1 / codds}, ${pev}, ${pstake}, ${pret}, ${Math.round(codds * 100) / 100}, 'real', 'open') returning id`;
        for (const l of legs) await sql`insert into parlay_legs (parlay_id, leg_bet_id) values (${Number(pins[0].id)}, ${l.id})`;
        placed++; exposure += pstake;
      }
    }
  }
  // ===== APUESTAS SOÑADORAS: longshot de varios partidos, stake fijo chico, multiplicador alto =====
  let dreams = 0;
  const openDreams = Number((await sql`select count(*) c from bets where market='Soñadora' and status='open'`)[0].c);
  if (openDreams < DREAM_MAX_OPEN) {
    // legs de prob media-alta, una por partido, las mas probables primero
    const cands = dreamCands.sort((a, b) => b.prob - a.prob);
    const dlegs: typeof cands = [];
    const seen = new Set<string>();
    let codds = 1;
    for (const c of cands) {
      if (seen.has(c.fx)) continue; // una leg por partido (dedup por fixture)
      dlegs.push(c); seen.add(c.fx); codds *= c.odds;
      if (dlegs.length >= DREAM_MAX_LEGS) break;
      if (dlegs.length >= 4 && codds >= DREAM_MULT_MIN) break; // ya multiplica suficiente
    }
    const cprob = dlegs.reduce((a, b) => a * b.prob, 1);
    // firma para no duplicar la misma soñadora en re-corridas
    const sig = dlegs.map((l) => `${l.matchId}:${l.selection}`).sort().join("|");
    const exists = sig ? await sql`select 1 from bets where market='Soñadora' and selection=${sig} and status='open' limit 1` : [{}];
    if (dlegs.length >= 4 && codds >= DREAM_MULT_MIN && cprob >= 0.03 && (!sig || !exists.length)) {
      const cret = Math.round(DREAM_STAKE * (codds - 1));
      const dins = await sql`insert into bets (match_id, market, selection, model_prob, odds_taken, implied_prob, edge, stake, potential_return, opening_odds, odds_source, status)
        values (${null}, 'Soñadora', ${sig}, ${cprob}, ${Math.round(codds * 100) / 100}, ${1 / codds}, ${cprob * codds - 1}, ${DREAM_STAKE}, ${cret}, ${Math.round(codds * 100) / 100}, 'real', 'open') returning id`;
      // legs como filas 'leg' (stake 0, no son posiciones) para poder liquidarlas
      for (const l of dlegs) {
        const li = await sql`insert into bets (match_id, market, selection, model_prob, odds_taken, implied_prob, edge, stake, potential_return, opening_odds, odds_source, status)
          values (${l.matchId}, '1X2', ${l.selection}, ${l.prob}, ${l.odds}, ${1 / l.odds}, 0, 0, 0, ${l.odds}, 'dream', 'leg') returning id`;
        await sql`insert into parlay_legs (parlay_id, leg_bet_id) values (${Number(dins[0].id)}, ${Number(li[0].id)})`;
      }
      placed++; exposure += DREAM_STAKE; dreams++;
    }
  }

  // saldo disponible = inicial - exposición abierta + retornos liquidados
  const realized = (await sql`select coalesce(sum(case when status='won' then potential_return when status='lost' then -stake else 0 end),0) as r from bets`)[0].r;
  const openExp = (await sql`select coalesce(sum(stake),0) as e from bets where status='open'`)[0].e;
  await sql`update bankroll set current=${starting - Number(openExp) + Number(realized)}, updated_at=now() where id=1`;
  return { placed, exposure, matches: preds.length, dreams };
}
