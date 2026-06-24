import { NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { aiReady } from "@/lib/ai";
import { oddsReady } from "@/lib/odds";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const b = (await sql`select current, currency from bankroll where id=1`)[0];
    const n = (await sql`select count(*)::int as c from bets where status='open'`)[0];
    return NextResponse.json({ ok: true, bankroll: b, openBets: n?.c ?? 0, ai: aiReady(), odds: { real: oddsReady() } });
  } catch (e) {
    return NextResponse.json({ ok: false, error: (e as Error).message }, { status: 500 });
  }
}
