import "../lib/loadenv";
import { sql } from "../lib/db";
import { placeBets, type Pred } from "../lib/engine";
import { readFileSync } from "fs";
import { resolve } from "path";

// ACUMULA: coloca apuestas de valor NUEVAS sin borrar las existentes (mantiene momios tempranos).
async function main() {
  const preds = JSON.parse(readFileSync(resolve(process.cwd(), "../predictions.json"), "utf8")) as Pred[];
  const r = await placeBets(preds, { reset: false });
  console.log(`✅ Accrue: ${r.placed} apuestas nuevas, exposición +${r.exposure.toLocaleString("es-MX")} MXN`);
  await sql.end();
}
main().catch((e) => { console.error(e); process.exit(1); });
