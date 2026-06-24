import postgres from "postgres";
import { neon } from "@neondatabase/serverless";

const url = process.env.DATABASE_URL || "postgres://wuru:wuru@localhost:5432/wuru";

// Neon (prod/Vercel): driver HTTP oficial. Local (Docker): driver postgres TCP.
function make() {
  if (/neon\.tech/.test(url)) {
    const nsql = neon(url) as unknown as { end: () => Promise<void> } & ReturnType<typeof neon>;
    nsql.end = async () => {}; // no-op (HTTP, sin conexión persistente)
    return nsql as unknown as ReturnType<typeof postgres>;
  }
  return postgres(url, { ssl: false, max: 5 });
}

const g = globalThis as unknown as { _sql?: ReturnType<typeof postgres> };
export const sql = g._sql ?? (g._sql = make());
