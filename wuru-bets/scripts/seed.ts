import "../lib/loadenv";
import { sql } from "../lib/db";
import { placeBets, type Pred } from "../lib/engine";
import { readFileSync } from "fs";
import { resolve } from "path";

async function main() {
  const path = resolve(process.cwd(), "../predictions.json");
  const preds = JSON.parse(readFileSync(path, "utf8")) as Pred[];
  const r = await placeBets(preds, { reset: true });
  console.log(`✅ Seed: ${r.matches} partidos, ${r.placed} apuestas de valor, exposición ${r.exposure.toLocaleString("es-MX")} MXN`);
  await sql.end();
}
main().catch((e) => { console.error(e); process.exit(1); });
