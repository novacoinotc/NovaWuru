import "../lib/loadenv";
import { sql } from "../lib/db";
import { clv as clvCalc } from "../lib/betting";
import { readFileSync, existsSync } from "fs";
import { resolve } from "path";

// results.json keyed por "homeNorm|awayNorm": { hg, ag }  (lo escribe settle_auto.py)
const norm = (s: string) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");

function grade(market: string, sel: string, home: string, away: string, hg: number, ag: number): boolean {
  if (market === "1X2") {
    if (norm(sel) === norm(home)) return hg > ag;
    if (norm(sel) === norm(away)) return ag > hg;
    return hg === ag; // Empate
  }
  if (market === "O/U 2.5") return sel.startsWith("Over") ? hg + ag >= 3 : hg + ag <= 2;
  if (market === "BTTS") return sel.includes("Si") ? hg >= 1 && ag >= 1 : !(hg >= 1 && ag >= 1);
  return false;
}

async function main() {
  const path = resolve(process.cwd(), "../results.json");
  if (!existsSync(path)) { console.log("No hay results.json — nada que liquidar."); await sql.end(); return; }
  const results = JSON.parse(readFileSync(path, "utf8")) as Record<string, { hg: number; ag: number }>;

  const matches = (await sql`select id, home, away from matches where status != 'finished'`) as any[];
  let settled = 0, pnlTotal = 0;
  for (const m of matches) {
    const key = `${norm(m.home)}|${norm(m.away)}`;
    const r = results[key];
    if (!r) continue;
    await sql`update matches set status='finished', home_goals=${r.hg}, away_goals=${r.ag} where id=${m.id}`;
    const bets = (await sql`select * from bets where match_id=${m.id} and status in ('open','leg')`) as any[];
    // resolver parleys/soñadoras aparte (sus legs estan en otra tabla)
    for (const bt of bets) {
      if (bt.market === "Parlay" || bt.market === "Soñadora") continue; // se liquidan abajo
      const won = grade(bt.market, bt.selection, m.home, m.away, r.hg, r.ag);
      if (bt.status === "leg") { // leg de soñadora: solo marca resultado, sin mover saldo
        await sql`update bets set status=${won ? "won" : "lost"}, settled_at=now() where id=${bt.id}`;
        continue;
      }
      const pnl = won ? Number(bt.potential_return) : -Number(bt.stake);
      const back = won ? Number(bt.stake) + Number(bt.potential_return) : 0;
      const cv = clvCalc(Number(bt.odds_taken), Number(bt.closing_odds ?? bt.odds_taken));
      await sql`update bets set status=${won ? "won" : "lost"}, result_pnl=${pnl}, clv=${cv}, settled_at=now() where id=${bt.id}`;
      await sql`update bankroll set current = current + ${back}, updated_at=now() where id=1`;
      const cur = (await sql`select current from bankroll where id=1`)[0].current;
      await sql`insert into bankroll_history (balance, note) values (${cur}, ${m.home + " vs " + m.away + ": " + bt.selection})`;
      settled++; pnlTotal += pnl;
    }
  }

  // Parleys y Soñadoras: ganan solo si TODAS sus legs ganaron; pierden si alguna pierde; pendientes si falta liquidar legs
  const parlays = (await sql`select * from bets where market in ('Parlay','Soñadora') and status='open'`) as any[];
  for (const p of parlays) {
    const legs = (await sql`select b.status from parlay_legs pl join bets b on b.id=pl.leg_bet_id where pl.parlay_id=${p.id}`) as any[];
    if (!legs.length || legs.some((l) => l.status === "open" || l.status === "leg")) continue; // aun pendiente
    const won = legs.every((l) => l.status === "won");
    const pnl = won ? Number(p.potential_return) : -Number(p.stake);
    const back = won ? Number(p.stake) + Number(p.potential_return) : 0;
    await sql`update bets set status=${won ? "won" : "lost"}, result_pnl=${pnl}, settled_at=now() where id=${p.id}`;
    await sql`update bankroll set current = current + ${back}, updated_at=now() where id=1`;
    const cur = (await sql`select current from bankroll where id=1`)[0].current;
    await sql`insert into bankroll_history (balance, note) values (${cur}, ${(p.market === "Soñadora" ? "🎰 Soñadora x" : "Parlay x") + legs.length})`;
    settled++; pnlTotal += pnl;
  }
  console.log(`✅ Liquidadas ${settled} apuestas. P&L: ${pnlTotal.toFixed(0)} MXN`);
  await sql.end();
}
main().catch((e) => { console.error(e); process.exit(1); });
