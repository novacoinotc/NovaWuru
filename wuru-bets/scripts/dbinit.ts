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
  // Simulaciones (quién gana según el modelo) — separadas de las apuestas
  await sql`create table if not exists predictions (
    id serial primary key,
    match_id int unique references matches(id) on delete cascade,
    league text, home text, away text, kickoff timestamptz,
    p_home numeric, p_draw numeric, p_away numeric,
    fav text, fav_prob numeric, updated_at timestamptz default now()
  )`;

  // A/B test: 2 modelos en paralelo, cada uno con su bankroll
  await sql`alter table bets add column if not exists model text default 'valor'`;
  await sql`alter table bankroll_history add column if not exists model text default 'valor'`;

  const start = Number(process.env.BANKROLL_MXN || 100000);
  await sql`insert into bankroll (id, name, starting, current) values (1, 'Modelo Valor', ${start}, ${start})
            on conflict (id) do nothing`;
  await sql`insert into bankroll (id, name, starting, current) values (2, 'Modelo Simulación', ${start}, ${start})
            on conflict (id) do nothing`;
  console.log("✅ Esquema listo. 2 modelos ×", start, "MXN (Valor + Simulación)");
  await sql.end();
}
main().catch((e) => { console.error(e); process.exit(1); });
