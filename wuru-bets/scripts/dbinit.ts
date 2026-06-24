import "../lib/loadenv";
import { sql } from "../lib/db";

async function main() {
  await sql`create table if not exists bankroll (
    id int primary key default 1,
    name text default 'Wuru Paper',
    currency text default 'MXN',
    starting numeric not null,
    current numeric not null,
    updated_at timestamptz default now()
  )`;
  await sql`create table if not exists bankroll_history (
    id serial primary key, ts timestamptz default now(), balance numeric not null, note text
  )`;
  await sql`create table if not exists matches (
    id serial primary key, ext_id text unique, sport text, league text,
    home text not null, away text not null, kickoff timestamptz,
    status text default 'scheduled', home_goals int, away_goals int
  )`;
  await sql`create table if not exists bets (
    id serial primary key,
    match_id int references matches(id),
    market text, selection text,
    model_prob numeric, odds_taken numeric, implied_prob numeric, edge numeric,
    stake numeric, potential_return numeric,
    status text default 'open',
    result_pnl numeric, opening_odds numeric, closing_odds numeric, clv numeric,
    odds_source text default 'synthetic',
    placed_at timestamptz default now(), settled_at timestamptz
  )`;
  await sql`alter table bets add column if not exists odds_source text default 'synthetic'`;
  await sql`create table if not exists parlay_legs (
    id serial primary key,
    parlay_id int references bets(id),
    leg_bet_id int references bets(id)
  )`;

  const start = Number(process.env.BANKROLL_MXN || 100000);
  await sql`insert into bankroll (id, starting, current) values (1, ${start}, ${start})
            on conflict (id) do nothing`;
  console.log("✅ Esquema listo. Bankroll inicial:", start, "MXN");
  await sql.end();
}
main().catch((e) => { console.error(e); process.exit(1); });
