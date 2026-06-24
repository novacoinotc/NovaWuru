import postgres from "postgres";

const url = process.env.DATABASE_URL || "postgres://wuru:wuru@localhost:5432/wuru";
const isManaged = /neon\.tech|supabase|aws|sslmode=require/.test(url);

// Singleton para evitar multiples pools en dev/serverless
const g = globalThis as unknown as { _sql?: ReturnType<typeof postgres> };
export const sql =
  g._sql ??
  postgres(url, {
    ssl: isManaged ? "require" : false,
    max: isManaged ? 1 : 5,
  });
if (process.env.NODE_ENV !== "production") g._sql = sql;
