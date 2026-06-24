import { sql } from "./db";

export type Bet = {
  id: number; sport: string; league: string; home: string; away: string;
  kickoff: string; market: string; selection: string;
  model_prob: number; odds_taken: number; implied_prob: number; edge: number;
  stake: number; potential_return: number; status: string;
  result_pnl: number | null; closing_odds: number | null; clv: number | null;
  odds_source: string | null;
};

export async function getBankroll() {
  const rows = await sql`select * from bankroll where id = 1`;
  return rows[0] as { starting: number; current: number; currency: string } | undefined;
}

export async function getOpenBets(): Promise<Bet[]> {
  return (await sql`
    select b.*, m.sport, m.league, coalesce(m.home,'Parlay') as home, coalesce(m.away,'') as away, m.kickoff
    from bets b left join matches m on m.id = b.match_id
    where b.status = 'open'
    order by b.edge desc
  `) as unknown as Bet[];
}

export async function getSettledBets(): Promise<Bet[]> {
  return (await sql`
    select b.*, m.sport, m.league, coalesce(m.home,'Parlay') as home, coalesce(m.away,'') as away, m.kickoff
    from bets b left join matches m on m.id = b.match_id
    where b.status in ('won','lost','void')
    order by b.settled_at desc nulls last
    limit 200
  `) as unknown as Bet[];
}

export async function getHistory() {
  return (await sql`select ts, balance from bankroll_history order by ts asc`) as unknown as {
    ts: string; balance: number;
  }[];
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
