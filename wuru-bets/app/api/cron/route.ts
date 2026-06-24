import { NextResponse } from "next/server";
import { placeBets, type Pred } from "@/lib/engine";
import { aiReady } from "@/lib/ai";

export const dynamic = "force-dynamic";

// GET: estado (lo llama el cron de Vercel). Requiere CRON_SECRET si está configurado.
export async function GET(req: Request) {
  const secret = process.env.CRON_SECRET;
  const auth = req.headers.get("authorization");
  if (secret && auth !== `Bearer ${secret}`) return NextResponse.json({ error: "no autorizado" }, { status: 401 });
  return NextResponse.json({ ok: true, ai: aiReady(), note: "Listo. Envía predicciones por POST para colocar apuestas de valor." });
}

// POST: ingiere predicciones (del modelo Wuru) y coloca apuestas de valor (paper).
export async function POST(req: Request) {
  const secret = process.env.CRON_SECRET;
  const auth = req.headers.get("authorization");
  if (secret && auth !== `Bearer ${secret}`) return NextResponse.json({ error: "no autorizado" }, { status: 401 });
  const body = (await req.json()) as { predictions: Pred[]; reset?: boolean };
  if (!body?.predictions?.length) return NextResponse.json({ error: "faltan predicciones" }, { status: 400 });
  const r = await placeBets(body.predictions, { reset: !!body.reset });
  return NextResponse.json({ ok: true, ...r });
}
