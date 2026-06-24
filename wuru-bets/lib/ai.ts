// ===== Conectores de IA: GLM 5.2 (investigación barata) + Claude (estrategia) =====

type Msg = { role: "system" | "user" | "assistant"; content: string };

/** GLM 5.2 / glm-4.6 via z.ai Coding Plan (endpoint Anthropic-compatible). Investigación barata. */
export async function glm(messages: Msg[], opts: { maxTokens?: number } = {}): Promise<string> {
  const key = process.env.GLM_API_KEY;
  const base = process.env.GLM_BASE_URL || "https://api.z.ai/api/anthropic";
  const model = process.env.GLM_MODEL || "glm-4.6";
  if (!key) throw new Error("GLM_API_KEY no configurada");
  const system = messages.filter((m) => m.role === "system").map((m) => m.content).join("\n\n");
  const msgs = messages.filter((m) => m.role !== "system").map((m) => ({ role: m.role, content: m.content }));
  if (msgs.length === 0) msgs.push({ role: "user", content: system || "Hola" });
  const res = await fetch(`${base}/v1/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01" },
    body: JSON.stringify({ model, max_tokens: opts.maxTokens ?? 4000, ...(system ? { system } : {}), messages: msgs }),
  });
  if (!res.ok) throw new Error(`GLM ${res.status}: ${await res.text()}`);
  const data = await res.json();
  return data.content?.[0]?.text ?? "";
}

/** Claude (Anthropic) para la capa de estrategia / decisiones de valor. */
export async function claude(system: string, user: string): Promise<string> {
  const key = process.env.ANTHROPIC_API_KEY;
  const model = process.env.ANTHROPIC_MODEL || "claude-sonnet-4-6";
  if (!key) throw new Error("ANTHROPIC_API_KEY no configurada");
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": key,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model,
      max_tokens: 2000,
      system,
      messages: [{ role: "user", content: user }],
    }),
  });
  if (!res.ok) throw new Error(`Claude ${res.status}: ${await res.text()}`);
  const data = await res.json();
  return data.content?.[0]?.text ?? "";
}

export const aiReady = () => ({ glm: !!process.env.GLM_API_KEY, claude: !!process.env.ANTHROPIC_API_KEY });
