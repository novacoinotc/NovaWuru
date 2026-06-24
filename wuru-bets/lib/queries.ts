import { sql } from "./db";

export type Bet = {
  id: number; sport: string; league: string; home: string; away: string;
  kickoff: string; market: string; selection: string;
  model_prob: number; odds_taken: number; implied_prob: number; edge: number;
  stake: number; potential_return: number; status: string;
  result_pnl: number | null; closing_odds: number | null; clv: number | null;
  odds_source: string | null;
};

export async function getBankroll(id = 1) {
  const rows = await sql`select * from bankroll where id = ${id}`;
  return rows[0] as { id: number; name: string; starting: number; current: number; currency: string } | undefined;
}

export async function getOpenBets(): Promise<Bet[]> {
  return (await sql`
    select b.*, m.sport, m.league, coalesce(m.home,'Parlay') as home, coalesce(m.away,'') as away, m.kickoff
    from bets b left join matches m on m.id = b.match_id
    where b.status = 'open' and b.model = 'valor' and b.market not in ('Soñadora','Parlay')
    order by b.edge desc
  `) as unknown as Bet[];
}

export async function getSettledBets(): Promise<Bet[]> {
  return (await sql`
    select b.*, m.sport, m.league, coalesce(m.home,'Parlay') as home, coalesce(m.away,'') as away, m.kickoff
    from bets b left join matches m on m.id = b.match_id
    where b.status in ('won','lost','void') and b.model = 'valor' and b.market not in ('Soñadora','Parlay') and coalesce(b.odds_source,'') != 'dream'
    order by b.settled_at desc nulls last
    limit 200
  `) as unknown as Bet[];
}

// Modelo Simulación (A/B): apuestas al favorito de cada simulación
export async function getSimBets(): Promise<Bet[]> {
  return (await sql`
    select b.*, m.sport, m.league, coalesce(m.home,'') as home, coalesce(m.away,'') as away, m.kickoff
    from bets b left join matches m on m.id = b.match_id
    where b.model = 'simulacion'
    order by (b.status='open') desc, b.placed_at desc
    limit 200
  `) as unknown as Bet[];
}

export type Dream = {
  id: number; status: string; odds_taken: number; model_prob: number;
  stake: number; potential_return: number; result_pnl: number | null; odds_source: string;
  legs: { home: string; away: string; selection: string; odds: number; prob: number; status: string }[];
};

async function fetchParlays(market: string): Promise<Dream[]> {
  const dreams = (await sql`
    select id, status, odds_taken, model_prob, stake, potential_return, result_pnl, odds_source
    from bets where market=${market} order by (status='open') desc, id desc limit 50
  `) as any[];
  const out: Dream[] = [];
  for (const d of dreams) {
    const legs = (await sql`
      select coalesce(m.home,'?') as home, coalesce(m.away,'') as away,
             b.selection, b.odds_taken as odds, b.model_prob as prob, b.status
      from parlay_legs pl join bets b on b.id = pl.leg_bet_id
      left join matches m on m.id = b.match_id
      where pl.parlay_id = ${d.id} order by b.id`) as any[];
    out.push({ ...d, legs } as Dream);
  }
  return out;
}

export async function getDreamBets(): Promise<Dream[]> { return fetchParlays("Soñadora"); }
export async function getSmartParlays(): Promise<Dream[]> { return fetchParlays("Parlay"); }

export async function getHistory(model = "valor") {
  return (await sql`select ts, balance from bankroll_history where coalesce(model,'valor')=${model} order by ts asc`) as unknown as {
    ts: string; balance: number;
  }[];
}

export type Prediction = {
  match_id: number; league: string; home: string; away: string; kickoff: string;
  p_home: number; p_draw: number; p_away: number; fav: string; fav_prob: number;
};

export async function getPredictions(): Promise<Prediction[]> {
  return (await sql`
    select p.* from predictions p
    join matches m on m.id = p.match_id
    where m.status != 'finished'
    order by p.kickoff asc nulls last
    limit 60
  `) as unknown as Prediction[];
}

export function kpis(starting: number, current: number, bets: Bet[]) {
  const settled = bets.filter((b) => b.status !== "open");
  const staked = settled.reduce((a, b) => a + Number(b.stake), 0);
  const pnl = settled.reduce((a, b) => a + Number(b.result_pnl ?? 0), 0);
  const wins = settled.filter((b) => b.status === "won").length;
  const withClv = settled.filter((b) => b.clv != null);
  const avgClv = withClv.length ? withClv.reduce((a, b) => a + Number(b.clv), 0) / withClv.length : 0;
  return {
    pnl,
    roi: starting ? (current - starting) / starting : 0,
    yield: staked ? pnl / staked : 0,
    hitRate: settled.length ? wins / settled.length : 0,
    nSettled: settled.length,
    avgClv,
  };
}
