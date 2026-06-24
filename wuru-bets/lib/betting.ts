// ===== Núcleo matemático de apuestas (determinista, sin IA) =====

/** Probabilidad implícita de una cuota decimal. */
export const impliedProb = (odds: number) => (odds > 1 ? 1 / odds : 0);

/** Quita el margen (vig) de un mercado con el método de la potencia. */
export function devig(odds: number[]): number[] {
  const raw = odds.map((o) => 1 / o);
  // hallar exponente k tal que sum(raw^k) = 1
  let lo = 0.5, hi = 1.5;
  for (let i = 0; i < 80; i++) {
    const mid = (lo + hi) / 2;
    const s = raw.reduce((a, p) => a + Math.pow(p, mid), 0);
    if (s > 1) lo = mid;
    else hi = mid;
  }
  const k = (lo + hi) / 2;
  return raw.map((p) => Math.pow(p, k));
}

/** Valor esperado por unidad apostada. EV>0 = apuesta con valor. */
export const ev = (prob: number, odds: number) => prob * odds - 1;

/** Fracción de Kelly (0..1) del bankroll a apostar. */
export function kelly(prob: number, odds: number, fraction = 0.25): number {
  const b = odds - 1;
  if (b <= 0) return 0;
  const f = (prob * b - (1 - prob)) / b; // Kelly completo
  return Math.max(0, f) * fraction;
}

/** Stake recomendado en dinero, con tope de seguridad. */
export function stakeFor(
  bankroll: number,
  prob: number,
  odds: number,
  opts: { fraction?: number; maxPct?: number } = {}
): number {
  const frac = kelly(prob, odds, opts.fraction ?? 0.25);
  const capped = Math.min(frac, opts.maxPct ?? 0.03);
  return Math.round(bankroll * capped);
}

/** Closing Line Value: cuánto le ganamos a la cuota de cierre. */
export function clv(oddsTaken: number, closingOdds: number): number {
  if (!closingOdds || closingOdds <= 1) return 0;
  return impliedProb(closingOdds) / impliedProb(oddsTaken) - 1;
}

export const fmtMXN = (n: number) =>
  new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 }).format(n);
