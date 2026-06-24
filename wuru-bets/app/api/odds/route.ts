import { NextResponse } from "next/server";
import { fetchOdds, oddsReady } from "@/lib/odds";

export const dynamic = "force-dynamic";

// Diagnóstico de la conexión de momios reales.
export async function GET() {
  if (!oddsReady()) {
    return NextResponse.json({
      ready: false,
      note: "Sin ODDS_API_KEY → se usan cuotas sintéticas. Registra una key gratis en the-odds-api.com y ponla en .env.",
    });
  }
  try {
    const list = await fetchOdds();
    return NextResponse.json({
      ready: true,
      events: list.length,
      sample: list.slice(0, 3).map((e) => ({ home: e.home, away: e.away, h2h: e.h2h, totals: e.totals })),
    });
  } catch (e) {
    return NextResponse.json({ ready: true, error: (e as Error).message }, { status: 500 });
  }
}
