import { getBankroll, getOpenBets, getSettledBets, getHistory, getDreamBets, getSmartParlays, getPredictions, kpis } from "@/lib/queries";
import { fmtMXN } from "@/lib/betting";
import BankrollChart from "@/components/BankrollChart";

export const dynamic = "force-dynamic";

function pct(n: number) { return `${(n * 100).toFixed(1)}%`; }
function fmtKO(d: string | null) {
  if (!d) return "—";
  const dt = new Date(d);
  return dt.toLocaleString("es-MX", { timeZone: "America/Mexico_City", weekday: "short", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}
function Stat({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: "pos" | "neg" }) {
  return (
    <div className="card p-4">
      <div style={{ color: "var(--muted)", fontSize: 12 }}>{label}</div>
      <div className={`text-2xl font-bold ${tone ?? ""}`} style={{ marginTop: 4 }}>{value}</div>
      {sub && <div style={{ color: "var(--muted)", fontSize: 11, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

export default async function Dashboard() {
  let bankroll, open: Awaited<ReturnType<typeof getOpenBets>> = [], settled: Awaited<ReturnType<typeof getSettledBets>> = [], history: Awaited<ReturnType<typeof getHistory>> = [], dreams: Awaited<ReturnType<typeof getDreamBets>> = [], smart: Awaited<ReturnType<typeof getSmartParlays>> = [], preds: Awaited<ReturnType<typeof getPredictions>> = [];
  let dbError = "";
  try {
    bankroll = await getBankroll();
    [open, settled, history, dreams, smart, preds] = await Promise.all([getOpenBets(), getSettledBets(), getHistory(), getDreamBets(), getSmartParlays(), getPredictions()]);
  } catch (e) {
    dbError = (e as Error).message;
  }

  if (dbError || !bankroll) {
    return (
      <main className="p-8 max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold mb-2">⚽ Wuru Bets</h1>
        <div className="card p-6">
          <p className="mb-2">Base de datos no inicializada o sin conexión.</p>
          <pre style={{ color: "var(--muted)", fontSize: 12, whiteSpace: "pre-wrap" }}>{dbError}</pre>
          <p style={{ marginTop: 12, color: "var(--muted)" }}>Corre: <code>docker compose up -d</code> · <code>npm run db:init</code> · <code>npm run seed</code></p>
        </div>
      </main>
    );
  }

  const k = kpis(Number(bankroll.starting), Number(bankroll.current), [...open, ...settled]);
  const exposure = open.reduce((a, b) => a + Number(b.stake), 0);
  const chart = [{ label: "Inicio", balance: Number(bankroll.starting) }, ...history.map((h, i) => ({ label: `#${i + 1}`, balance: Number(h.balance) }))];

  return (
    <main className="p-6 md:p-8 max-w-7xl mx-auto">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">⚽ Wuru Bets <span className="chip">paper trading</span></h1>
          <p style={{ color: "var(--muted)", fontSize: 13 }}>Value betting · ¼ Kelly · CLV · modelo Wuru</p>
        </div>
        <div className="text-right">
          <div style={{ color: "var(--muted)", fontSize: 12 }}>Saldo actual</div>
          <div className="text-3xl font-extrabold">{fmtMXN(Number(bankroll.current))}</div>
        </div>
      </header>

      <section className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6">
        <Stat label="P&L total" value={fmtMXN(k.pnl)} tone={k.pnl >= 0 ? "pos" : "neg"} />
        <Stat label="ROI" value={pct(k.roi)} tone={k.roi >= 0 ? "pos" : "neg"} sub={`inicial ${fmtMXN(Number(bankroll.starting))}`} />
        <Stat label="Yield" value={pct(k.yield)} tone={k.yield >= 0 ? "pos" : "neg"} sub="ganancia/apostado" />
        <Stat label="CLV prom." value={pct(k.avgClv)} tone={k.avgClv >= 0 ? "pos" : "neg"} sub="vs cuota cierre" />
        <Stat label="Acierto" value={pct(k.hitRate)} sub={`${k.nSettled} liquidadas`} />
        <Stat label="Exposición abierta" value={fmtMXN(exposure)} sub={`${open.length} posiciones`} />
      </section>

      <section className="card p-4 mb-6">
        <h2 className="font-semibold mb-2">Curva de saldo</h2>
        <BankrollChart data={chart} starting={Number(bankroll.starting)} />
      </section>

      <section className="card p-4 mb-6 overflow-x-auto">
        <h2 className="font-semibold mb-1">🔮 Simulaciones — quién gana según el modelo ({preds.length})</h2>
        <p style={{ color: "var(--muted)", fontSize: 12, marginBottom: 12 }}>Esto es lo que dice la simulación Monte Carlo (100k), <b>sin estrategia de apuestas</b>. Solo el pronóstico: probabilidad de cada resultado y favorito.</p>
        <table>
          <thead><tr><th>Fecha y hora (MX)</th><th>Partido</th><th>🏆 Favorito</th><th>Local</th><th>Empate</th><th>Visitante</th></tr></thead>
          <tbody>
            {preds.map((p) => {
              const mx = Math.max(Number(p.p_home), Number(p.p_draw), Number(p.p_away));
              const cell = (v: number) => <td style={{ fontWeight: Number(v) === mx ? 700 : 400, color: Number(v) === mx ? "var(--green)" : undefined }}>{pct(Number(v))}</td>;
              return (
                <tr key={p.match_id}>
                  <td style={{ whiteSpace: "nowrap", color: "var(--muted)", fontSize: 12 }}>{fmtKO(p.kickoff)}</td>
                  <td><b>{p.home}</b> vs {p.away}</td>
                  <td><b className="pos">{p.fav}</b> {pct(Number(p.fav_prob))}</td>
                  {cell(Number(p.p_home))}{cell(Number(p.p_draw))}{cell(Number(p.p_away))}
                </tr>
              );
            })}
            {preds.length === 0 && <tr><td colSpan={6} style={{ color: "var(--muted)" }}>Sin simulaciones aún. Corre el análisis.</td></tr>}
          </tbody>
        </table>
      </section>

      <section className="card p-4 mb-6 overflow-x-auto">
        <h2 className="font-semibold mb-1">📌 Apuestas de estrategia — posiciones abiertas ({open.length})</h2>
        <p style={{ color: "var(--muted)", fontSize: 12, marginBottom: 12 }}>Solo donde hay <b>valor real</b> (el momio paga más que la probabilidad). NO apostamos a todos los partidos — solo donde conviene. Stake por ¼ Kelly.</p>
        <table>
          <thead><tr><th>Fecha y hora (MX)</th><th>Partido</th><th>Liga</th><th>Mercado</th><th>Pick</th><th>Prob</th><th>Cuota</th><th>Edge</th><th>Stake</th><th>Gana</th></tr></thead>
          <tbody>
            {open.map((b) => (
              <tr key={b.id}>
                <td style={{ whiteSpace: "nowrap", color: "var(--muted)", fontSize: 12 }}>{fmtKO(b.kickoff)}</td>
                <td><b>{b.home}</b> vs {b.away}</td>
                <td><span className="chip">{b.league}</span></td>
                <td>{b.market}</td>
                <td><b>{b.selection}</b></td>
                <td>{pct(Number(b.model_prob))}</td>
                <td>{Number(b.odds_taken).toFixed(2)} <span className="chip" style={{ color: b.odds_source === "real" ? "var(--green)" : "var(--muted)" }}>{b.odds_source === "real" ? "real" : "sint"}</span></td>
                <td className={Number(b.edge) >= 0 ? "pos" : "neg"}>{pct(Number(b.edge))}</td>
                <td>{fmtMXN(Number(b.stake))}</td>
                <td className="pos">{fmtMXN(Number(b.potential_return))}</td>
              </tr>
            ))}
            {open.length === 0 && <tr><td colSpan={10} style={{ color: "var(--muted)" }}>Sin posiciones abiertas. Corre el análisis diario.</td></tr>}
          </tbody>
        </table>
      </section>

      <section className="card p-4 mb-6">
        <h2 className="font-semibold mb-1">🎯 Parleys Inteligentes <span className="chip">value · +EV</span></h2>
        <p style={{ color: "var(--muted)", fontSize: 12, marginBottom: 12 }}>Combina nuestras <b>apuestas de valor</b> (cada una +EV) de partidos distintos. Más pago que las individuales, con stake moderado. Rentable a la larga, mayor varianza.</p>
        {smart.length === 0 && <div style={{ color: "var(--muted)", fontSize: 13 }}>Sin parley inteligente hoy (se arma cuando hay ≥2 apuestas de valor en partidos distintos).</div>}
        <div className="grid md:grid-cols-2 gap-3">
          {smart.map((d) => (
            <div key={d.id} className="card p-3" style={{ background: "rgba(255,255,255,0.02)" }}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span style={{ fontSize: 22, fontWeight: 800, color: "var(--green)" }}>{Number(d.odds_taken).toFixed(2)}x</span>
                  <span style={{ color: "var(--muted)", fontSize: 12, marginLeft: 8 }}>prob {pct(Number(d.model_prob))} · {d.legs.length} legs</span>
                </div>
                <span className="chip" style={{ color: d.status === "won" ? "var(--green)" : d.status === "lost" ? "var(--red)" : "var(--muted)" }}>{d.status === "open" ? "vigente" : d.status}</span>
              </div>
              <div style={{ fontSize: 13, marginBottom: 8 }}>Stake <b>{fmtMXN(Number(d.stake))}</b> → gana <b className="pos">{fmtMXN(Number(d.stake) + Number(d.potential_return))}</b></div>
              <table><tbody>
                {d.legs.map((l, i) => (
                  <tr key={i}>
                    <td style={{ fontSize: 12 }}>{l.home} vs {l.away}</td>
                    <td style={{ fontSize: 12 }}><b>{l.selection}</b> @ {Number(l.odds).toFixed(2)}</td>
                    <td style={{ fontSize: 12 }}><span className="chip" style={{ color: l.status === "won" ? "var(--green)" : l.status === "lost" ? "var(--red)" : "var(--muted)" }}>{l.status === "open" || l.status === "leg" ? "pend" : l.status}</span></td>
                  </tr>
                ))}
              </tbody></table>
            </div>
          ))}
        </div>
      </section>

      <section className="card p-4 mb-6">
        <h2 className="font-semibold mb-1">🎰 Apuestas Soñadoras <span className="chip">$100 fijo · alto multiplicador</span></h2>
        <p style={{ color: "var(--muted)", fontSize: 12, marginBottom: 12 }}>Billete de lotería con cabeza: combina selecciones de prob media-alta de varios partidos. Stake mínimo, premio grande.</p>
        {dreams.length === 0 && <div style={{ color: "var(--muted)", fontSize: 13 }}>Aún no hay soñadoras (se arman cuando hay ≥4 legs de prob media-alta con multiplicador ≥7x).</div>}
        <div className="grid md:grid-cols-2 gap-3">
          {dreams.map((d) => (
            <div key={d.id} className="card p-3" style={{ background: "rgba(255,255,255,0.02)" }}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="chip" style={{ color: d.odds_source === "dream_value" ? "var(--green)" : "var(--muted)", marginRight: 8 }}>{d.odds_source === "dream_value" ? "💎 VALOR (+EV)" : "🎲 FAVORITOS"}</span>
                  <span style={{ fontSize: 22, fontWeight: 800, color: "var(--green)" }}>{Number(d.odds_taken).toFixed(1)}x</span>
                  <span style={{ color: "var(--muted)", fontSize: 12, marginLeft: 8 }}>prob {pct(Number(d.model_prob))} · {d.legs.length} legs</span>
                </div>
                <span className="chip" style={{ color: d.status === "won" ? "var(--green)" : d.status === "lost" ? "var(--red)" : "var(--muted)" }}>{d.status === "open" ? "vigente" : d.status}</span>
              </div>
              <div style={{ fontSize: 13, marginBottom: 8 }}>
                Stake <b>{fmtMXN(Number(d.stake))}</b> → gana <b className="pos">{fmtMXN(Number(d.stake) + Number(d.potential_return))}</b>
              </div>
              <table><tbody>
                {d.legs.map((l, i) => (
                  <tr key={i}>
                    <td style={{ fontSize: 12 }}>{l.home} vs {l.away}</td>
                    <td style={{ fontSize: 12 }}><b>{l.selection}</b> @ {Number(l.odds).toFixed(2)}</td>
                    <td style={{ fontSize: 12 }}><span className="chip" style={{ color: l.status === "won" ? "var(--green)" : l.status === "lost" ? "var(--red)" : "var(--muted)" }}>{l.status === "leg" || l.status === "open" ? "pend" : l.status}</span></td>
                  </tr>
                ))}
              </tbody></table>
            </div>
          ))}
        </div>
      </section>

      <section className="card p-4 overflow-x-auto">
        <h2 className="font-semibold mb-3">📊 Apuestas liquidadas</h2>
        <table>
          <thead><tr><th>Partido</th><th>Pick</th><th>Cuota</th><th>Stake</th><th>Resultado</th><th>P&L</th><th>CLV</th></tr></thead>
          <tbody>
            {settled.map((b) => (
              <tr key={b.id}>
                <td>{b.home} vs {b.away}</td>
                <td>{b.market}: <b>{b.selection}</b></td>
                <td>{Number(b.odds_taken).toFixed(2)}</td>
                <td>{fmtMXN(Number(b.stake))}</td>
                <td><span className="chip" style={{ color: b.status === "won" ? "var(--green)" : b.status === "lost" ? "var(--red)" : "var(--muted)" }}>{b.status}</span></td>
                <td className={Number(b.result_pnl) >= 0 ? "pos" : "neg"}>{fmtMXN(Number(b.result_pnl ?? 0))}</td>
                <td className={Number(b.clv ?? 0) >= 0 ? "pos" : "neg"}>{b.clv != null ? pct(Number(b.clv)) : "—"}</td>
              </tr>
            ))}
            {settled.length === 0 && <tr><td colSpan={7} style={{ color: "var(--muted)" }}>Aún no hay apuestas liquidadas.</td></tr>}
          </tbody>
        </table>
      </section>

      <footer style={{ color: "var(--muted)", fontSize: 11, marginTop: 24, textAlign: "center" }}>
        Wuru Bets · paper trading (dinero virtual) · stake por valor (¼ Kelly), nunca Martingale · juego responsable
      </footer>
    </main>
  );
}
