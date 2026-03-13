"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  AreaChart, Area, CartesianGrid, Legend,
} from "recharts";
import { channels, weeklyData, totalRevenue, baselineRevenue, totalSpend } from "../lib/mock-data";
import Card, { StatCard } from "./Card";

const fmt = (n: number) =>
  `R$${n.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}`;

export default function ROI360() {
  // Waterfall decomposition data
  const waterfall = [
    { name: "Baseline", value: baselineRevenue, color: "#94a3b8" },
    ...channels
      .sort((a, b) => b.contribution - a.contribution)
      .map((c) => ({ name: c.name, value: c.contribution, color: c.color })),
  ];

  // ROI with confidence intervals
  const roiData = channels
    .sort((a, b) => b.roi - a.roi)
    .map((c) => ({
      name: c.name,
      roi: c.roi,
      lower: c.roiLower,
      upper: c.roiUpper,
      color: c.color,
    }));

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Receita Total" value={fmt(totalRevenue)} sub="Ultimas 52 semanas" />
        <StatCard label="Investimento Total" value={fmt(totalSpend)} sub="Todos os canais" />
        <StatCard
          label="ROAS Geral"
          value={`${(totalRevenue / totalSpend).toFixed(2)}x`}
          color="var(--primary)"
        />
        <StatCard label="Baseline" value={fmt(baselineRevenue)} sub={`${((baselineRevenue / totalRevenue) * 100).toFixed(0)}% da receita`} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Waterfall Decomposition */}
        <Card title="Decomposicao de Receita (Waterfall)">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={waterfall} margin={{ left: 10, right: 10 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" height={60} />
              <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => fmt(Number(v))} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {waterfall.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* ROI by Channel */}
        <Card title="ROI por Canal (com intervalo de confianca 90%)">
          <div className="space-y-3">
            {roiData.map((ch) => (
              <div key={ch.name} className="flex items-center gap-3">
                <span className="text-xs font-mono w-24 text-right" style={{ color: "var(--muted)" }}>
                  {ch.name}
                </span>
                <div className="flex-1 relative h-6">
                  {/* CI bar */}
                  <div
                    className="absolute top-2 h-2 rounded-full opacity-25"
                    style={{
                      left: `${(ch.lower / 5) * 100}%`,
                      width: `${((ch.upper - ch.lower) / 5) * 100}%`,
                      background: ch.color,
                    }}
                  />
                  {/* Mean dot */}
                  <div
                    className="absolute top-1 w-4 h-4 rounded-full border-2 border-white"
                    style={{
                      left: `${(ch.roi / 5) * 100}%`,
                      transform: "translateX(-50%)",
                      background: ch.color,
                    }}
                  />
                </div>
                <span className="text-sm font-bold w-12 text-right">{ch.roi.toFixed(1)}x</span>
              </div>
            ))}
            <div className="flex justify-between text-[10px] px-24 pt-2" style={{ color: "var(--muted)" }}>
              <span>0x</span><span>1x</span><span>2x</span><span>3x</span><span>4x</span><span>5x</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Revenue over time */}
      <Card title="Receita Semanal e Contribuicoes">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={weeklyData.slice(-26)} margin={{ left: 10, right: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="week" tick={{ fontSize: 10 }} />
            <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => fmt(Number(v))} />
            <Legend />
            <Area type="monotone" dataKey="baseline" stackId="1" fill="#94a3b8" stroke="#94a3b8" name="Baseline" />
            <Area type="monotone" dataKey="google_ads" stackId="1" fill="#4285F4" stroke="#4285F4" name="Google Ads" />
            <Area type="monotone" dataKey="meta_ads" stackId="1" fill="#1877F2" stroke="#1877F2" name="Meta Ads" />
            <Area type="monotone" dataKey="tv" stackId="1" fill="#E91E63" stroke="#E91E63" name="TV" />
            <Area type="monotone" dataKey="tiktok" stackId="1" fill="#000" stroke="#000" name="TikTok" />
            <Area type="monotone" dataKey="influencer" stackId="1" fill="#00BCD4" stroke="#00BCD4" name="Influencer" />
            <Area type="monotone" dataKey="others" stackId="1" fill="#9C27B0" stroke="#9C27B0" name="Outros" />
          </AreaChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
