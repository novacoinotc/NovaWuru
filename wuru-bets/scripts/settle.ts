import { sql } from "../lib/db";
import { clv as clvCalc } from "../lib/betting";
import { readFileSync, existsSync } from "fs";
import { resolve } from "path";
try { (process as any).loadEnvFile?.(".env"); } catch {}

// results.json: { "ENG_GHA": {"hg":0,"ag":1,"closing":{"1X2":{"Ghana":3.9}}}, ... }
function grade(market: string, sel: string, home: string, away: string, hg: number, ag: number): boolean {
  if (market === "1X2") {
    if (sel === home) return hg > ag;
    if (sel === away) return ag > hg;
    return hg === ag; // Empate
  }
  if (market === "O/U 2.5") return sel.startsWith("Over") ? hg + ag >= 3 : hg + ag <= 2;
  if (market === "BTTS") return sel.includes("Si") ? hg >= 1 && ag >= 1 : !(hg >= 1 && ag >= 1);
  return false;
}

async function main() {
  const path = resolve(process.cwd(), "../results.json");
  if (!existsSync(path)) { console.log("No hay results.json — nada que liquidar."); await sql.end(); return; }
  const results = JSON.parse(readFileSync(path, "utf8")) as Record<string, { hg: number; ag: number; closing?: any }>;

  let settled = 0, pnlTotal = 0;
  for (const [extId, r] of Object.entries(results)) {
    const mr = (await sql`select id, home, away from matches where ext_id=${extId}`)[0] as any;
    if (!mr) continue;
    await sql`update matches set status='finished', home_goals=${r.hg}, away_goals=${r.ag} where id=${mr.id}`;
    const bets = (await sql`select * from bets where match_id=${mr.id} and status='open'`) as any[];
    for (const bt of bets) {
      const won = grade(bt.market, bt.selection, mr.home, mr.away, r.hg, r.ag);
      const pnl = won ? Number(bt.potential_return) : -Number(bt.stake);
      const back = won ? Number(bt.stake) + Number(bt.potential_return) : 0; // dinero devuelto al saldo
      const closing = r.closing?.[bt.market]?.[bt.selection] ?? Number(bt.odds_taken);
      const cv = clvCalc(Number(bt.odds_taken), Number(closing));
      await sql`update bets set status=${won ? "won" : "lost"}, result_pnl=${pnl}, closing_odds=${closing}, clv=${cv}, settled_at=now() where id=${bt.id}`;
      await sql`update bankroll set current = current + ${back}, updated_at=now() where id=1`;
      const cur = (await sql`select current from bankroll where id=1`)[0].current;
      await sql`insert into bankroll_history (balance, note) values (${cur}, ${mr.home + " vs " + mr.away + ": " + bt.selection})`;
      settled++; pnlTotal += pnl;
    }
  }
  console.log(`✅ Liquidadas ${settled} apuestas. P&L: ${pnlTotal} MXN`);
  await sql.end();
}
main().catch((e) => { console.error(e); process.exit(1); });
