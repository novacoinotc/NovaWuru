"use client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from "recharts";

export default function BankrollChart({
  data,
  starting,
}: {
  data: { label: string; balance: number }[];
  starting: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <YAxis
          tick={{ fill: "#94a3b8", fontSize: 11 }}
          domain={["auto", "auto"]}
          tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
          width={44}
        />
        <Tooltip
          contentStyle={{ background: "#0b0f17", border: "1px solid #1f2937", borderRadius: 8, color: "#e5e7eb" }}
          formatter={(v: number) => [`$${v.toLocaleString("es-MX")}`, "Saldo"]}
        />
        <ReferenceLine y={starting} stroke="#64748b" strokeDasharray="4 4" />
        <Line type="monotone" dataKey="balance" stroke="#22c55e" strokeWidth={2.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
