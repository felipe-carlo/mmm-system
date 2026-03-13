"use client";

import { useState } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import { channels, totalRevenue } from "../lib/mock-data";
import Card, { StatCard } from "./Card";

const fmt = (n: number) => `R$${n.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}`;

export default function Forecasting() {
  const [weeks, setWeeks] = useState(8);
  const [spendMultiplier, setSpendMultiplier] = useState(1.0);

  const avgWeeklyRevenue = totalRevenue / 52;
  const totalROI = channels.reduce((s, c) => s + c.roi * c.spend, 0) / channels.reduce((s, c) => s + c.spend, 0);

  const forecastData = Array.from({ length: weeks }, (_, i) => {
    const week = i + 1;
    const base = avgWeeklyRevenue * spendMultiplier * (1 + (Math.random() - 0.5) * 0.08);
    const seasonal = Math.sin((week / 52) * 2 * Math.PI) * avgWeeklyRevenue * 0.1;
    return {
      week: `S+${week}`,
      base: Math.round(base + seasonal),
      optimistic: Math.round((base + seasonal) * 1.15),
      pessimistic: Math.round((base + seasonal) * 0.85),
    };
  });

  const totalBase = forecastData.reduce((s, w) => s + w.base, 0);
  const totalOptimistic = forecastData.reduce((s, w) => s + w.optimistic, 0);
  const totalPessimistic = forecastData.reduce((s, w) => s + w.pessimistic, 0);

  return (
    <div className="space-y-6">
      {/* Controls */}
      <Card>
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-3 flex-1">
            <label className="text-sm font-medium whitespace-nowrap">Horizonte:</label>
            <input
              type="range" min={4} max={26} step={1} value={weeks}
              onChange={(e) => setWeeks(Number(e.target.value))}
              className="flex-1 h-2 rounded-lg cursor-pointer accent-[var(--primary)]"
            />
            <span className="text-sm font-bold w-20 text-right" style={{ color: "var(--primary)" }}>
              {weeks} semanas
            </span>
          </div>
          <div className="flex items-center gap-3 flex-1">
            <label className="text-sm font-medium whitespace-nowrap">Spend:</label>
            <input
              type="range" min={0.5} max={1.5} step={0.05} value={spendMultiplier}
              onChange={(e) => setSpendMultiplier(Number(e.target.value))}
              className="flex-1 h-2 rounded-lg cursor-pointer accent-[var(--primary)]"
            />
            <span className="text-sm font-bold w-20 text-right" style={{ color: "var(--primary)" }}>
              {(spendMultiplier * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Projecao Base" value={fmt(totalBase)} color="var(--primary)" sub={`${weeks} semanas`} />
        <StatCard label="Cenario Otimista" value={fmt(totalOptimistic)} color="var(--success)" sub="+15% upside" />
        <StatCard label="Cenario Pessimista" value={fmt(totalPessimistic)} color="var(--accent)" sub="-15% downside" />
      </div>

      {/* Forecast chart */}
      <Card title="Projecao de Receita Semanal">
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={forecastData} margin={{ left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="week" tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => fmt(Number(v))} />
            <Legend />
            <Area type="monotone" dataKey="optimistic" stroke="var(--success)" fill="var(--success)" fillOpacity={0.08} strokeWidth={1} name="Otimista" />
            <Area type="monotone" dataKey="base" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.15} strokeWidth={2.5} name="Base" />
            <Area type="monotone" dataKey="pessimistic" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.08} strokeWidth={1} name="Pessimista" />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      {/* Sensitivity analysis */}
      <Card title="Sensibilidade: Impacto de Variacao de Budget">
        <div className="grid grid-cols-5 gap-3">
          {[-20, -10, 0, 10, 20].map((pct) => {
            const multiplier = 1 + pct / 100;
            const projected = Math.round(avgWeeklyRevenue * weeks * multiplier);
            return (
              <div
                key={pct}
                className="rounded-lg p-3 text-center border"
                style={{
                  borderColor: pct === 0 ? "var(--primary)" : "var(--border)",
                  background: pct === 0 ? "rgba(67,97,238,0.05)" : "transparent",
                }}
              >
                <p className="text-xs font-medium mb-1" style={{ color: "var(--muted)" }}>
                  {pct > 0 ? "+" : ""}{pct}% spend
                </p>
                <p className="text-lg font-bold" style={{ color: pct === 0 ? "var(--primary)" : "var(--foreground)" }}>
                  {fmt(projected)}
                </p>
                <p className="text-[10px]" style={{ color: "var(--muted)" }}>
                  {weeks} semanas
                </p>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
