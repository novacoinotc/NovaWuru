import "../lib/loadenv";
import { sql } from "../lib/db";
import { placeBets, placeSimBets, type Pred } from "../lib/engine";
import { readFileSync } from "fs";
import { resolve } from "path";

async function main() {
  const path = resolve(process.cwd(), "../predictions.json");
  const preds = JSON.parse(readFileSync(path, "utf8")) as Pred[];
  const r = await placeBets(preds, { reset: true });
  const s = await placeSimBets(preds, { reset: true });
  console.log(`✅ Seed: ${r.matches} partidos | Modelo Valor: ${r.placed} apuestas | Modelo Simulación: ${s.placed} apuestas`);
  await sql.end();
}
main().catch((e) => { console.error(e); process.exit(1); });
