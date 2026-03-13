"use client";

import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend,
  LineChart, Line, CartesianGrid,
} from "recharts";
import { channels, optimizedAllocation, totalSpend } from "../lib/mock-data";
import Card, { StatCard } from "./Card";

const fmt = (n: number) => `R$${n.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}`;

export default function MediaOptimizer() {
  const [budget, setBudget] = useState(totalSpend);

  const allocationData = optimizedAllocation.map((ch) => ({
    name: ch.name,
    current: ch.spend,
    recommended: Math.round(ch.recommended * (budget / totalSpend)),
    color: ch.color,
  }));

  // Saturation curves (simulated Hill function)
  const saturationData = channels.slice(0, 4).map((ch) => {
    const points = Array.from({ length: 20 }, (_, i) => {
      const spend = (i / 19) * ch.spend * 2;
      const halfSat = ch.spend * 0.6;
      const response = (ch.contribution * 1.3 * spend) / (halfSat + spend);
      return { spend: Math.round(spend), [ch.name]: Math.round(response) };
    });
    return { channel: ch, points };
  });

  const mergedSaturation = saturationData[0].points.map((_, i) => {
    const merged: Record<string, number> = { spend: saturationData[0].points[i].spend };
    saturationData.forEach((s) => {
      merged[s.channel.name] = Object.values(s.points[i]).find(
        (v) => typeof v === "number" && v !== s.points[i].spend
      ) as number;
    });
    return merged;
  });

  const totalRecommended = allocationData.reduce((s, a) => s + a.recommended, 0);

  return (
    <div className="space-y-6">
      {/* Budget slider */}
      <Card>
        <div className="flex items-center gap-6">
          <label className="text-sm font-medium" style={{ color: "var(--foreground)" }}>
            Budget Total Semanal:
          </label>
          <input
            type="range"
            min={totalSpend * 0.5}
            max={totalSpend * 1.5}
            step={1000}
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            className="flex-1 h-2 rounded-lg cursor-pointer accent-[var(--primary)]"
          />
          <span className="text-lg font-bold min-w-[140px] text-right" style={{ color: "var(--primary)" }}>
            {fmt(budget)}
          </span>
        </div>
      </Card>

      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Budget Atual" value={fmt(totalSpend)} />
        <StatCard label="Recomendado" value={fmt(totalRecommended)} color="var(--primary)" />
        <StatCard
          label="Diferenca"
          value={`${totalRecommended > totalSpend ? "+" : ""}${fmt(totalRecommended - totalSpend)}`}
          color={totalRecommended > totalSpend ? "var(--accent)" : "var(--success)"}
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Current vs Recommended */}
        <Card title="Alocacao Atual vs. Recomendada">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={allocationData} layout="vertical" margin={{ left: 70 }}>
              <XAxis type="number" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => fmt(v)} />
              <Legend />
              <Bar dataKey="current" fill="#cbd5e1" name="Atual" radius={[0, 4, 4, 0]} />
              <Bar dataKey="recommended" name="Recomendado" radius={[0, 4, 4, 0]}>
                {allocationData.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Saturation Curves */}
        <Card title="Curvas de Saturacao (Top 4 Canais)">
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={mergedSaturation} margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="spend" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => fmt(v)} />
              <Legend />
              {saturationData.map((s) => (
                <Line
                  key={s.channel.name}
                  type="monotone"
                  dataKey={s.channel.name}
                  stroke={s.channel.color}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Change table */}
      <Card title="Detalhamento por Canal">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ color: "var(--muted)" }}>
              <th className="text-left py-2 font-medium">Canal</th>
              <th className="text-right py-2 font-medium">Atual</th>
              <th className="text-right py-2 font-medium">Recomendado</th>
              <th className="text-right py-2 font-medium">Variacao</th>
              <th className="text-right py-2 font-medium">ROI</th>
            </tr>
          </thead>
          <tbody>
            {optimizedAllocation
              .sort((a, b) => b.recommended - a.recommended)
              .map((ch) => (
                <tr key={ch.name} className="border-t" style={{ borderColor: "var(--border)" }}>
                  <td className="py-2.5 flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full inline-block" style={{ background: ch.color }} />
                    {ch.name}
                  </td>
                  <td className="text-right">{fmt(ch.spend)}</td>
                  <td className="text-right font-medium">{fmt(Math.round(ch.recommended * (budget / totalSpend)))}</td>
                  <td className="text-right">
                    <span
                      className="font-medium"
                      style={{ color: ch.changePct > 0 ? "var(--success)" : "var(--accent)" }}
                    >
                      {ch.changePct > 0 ? "+" : ""}{ch.changePct}%
                    </span>
                  </td>
                  <td className="text-right font-bold">{ch.roi.toFixed(2)}x</td>
                </tr>
              ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
