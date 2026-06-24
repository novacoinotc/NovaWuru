import "../lib/loadenv";
import { sql } from "../lib/db";
import { placeBets, placeSimBets, type Pred } from "../lib/engine";
import { readFileSync } from "fs";
import { resolve } from "path";

// ACUMULA: coloca apuestas NUEVAS sin borrar las existentes (mantiene momios tempranos). Ambos modelos.
async function main() {
  const preds = JSON.parse(readFileSync(resolve(process.cwd(), "../predictions.json"), "utf8")) as Pred[];
  const r = await placeBets(preds, { reset: false });
  const s = await placeSimBets(preds, { reset: false });
  console.log(`✅ Accrue: Modelo Valor +${r.placed} | Modelo Simulación +${s.placed}`);
  await sql.end();
}
main().catch((e) => { console.error(e); process.exit(1); });
