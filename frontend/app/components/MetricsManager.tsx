"use client";

import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { channels, weeklyData, totalRevenue, totalSpend } from "../lib/mock-data";
import Card, { StatCard } from "./Card";

const fmt = (n: number) => `R$${n.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}`;

export default function MetricsManager() {
  const last4Weeks = weeklyData.slice(-4);
  const prev4Weeks = weeklyData.slice(-8, -4);

  const recentRevenue = last4Weeks.reduce((s, w) => s + w.revenue, 0);
  const prevRevenue = prev4Weeks.reduce((s, w) => s + w.revenue, 0);
  const revenueChange = ((recentRevenue - prevRevenue) / prevRevenue) * 100;

  const weeklySpendData = weeklyData.slice(-12).map((w) => ({
    week: w.week,
    spend: w.google_ads + w.meta_ads + w.tv + w.tiktok + w.influencer + w.others,
    revenue: w.revenue,
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Receita (4 semanas)"
          value={fmt(recentRevenue)}
          sub={`${revenueChange > 0 ? "+" : ""}${revenueChange.toFixed(1)}% vs periodo anterior`}
          color={revenueChange > 0 ? "var(--success)" : "var(--accent)"}
        />
        <StatCard label="Spend Semanal Medio" value={fmt(Math.round(totalSpend / 52))} />
        <StatCard label="ROAS (4 sem)" value={`${(recentRevenue / (totalSpend / 52 * 4)).toFixed(2)}x`} color="var(--primary)" />
        <StatCard label="Canais Ativos" value={`${channels.length}`} sub="Digital + Offline + Influencer" />
      </div>

      {/* Revenue & Spend trend */}
      <Card title="Receita vs. Investimento (ultimas 12 semanas)">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={weeklySpendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="week" tick={{ fontSize: 11 }} />
            <YAxis yAxisId="revenue" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
            <YAxis yAxisId="spend" orientation="right" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: number) => fmt(v)} />
            <Line yAxisId="revenue" type="monotone" dataKey="revenue" stroke="var(--primary)" strokeWidth={2.5} name="Receita" dot={false} />
            <Line yAxisId="spend" type="monotone" dataKey="spend" stroke="var(--muted)" strokeWidth={1.5} strokeDasharray="5 5" name="Investimento" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Per-channel spend table */}
      <Card title="Spend por Canal (ultimas 4 semanas)">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ color: "var(--muted)" }}>
              <th className="text-left py-2 font-medium">Canal</th>
              <th className="text-right py-2 font-medium">Tipo</th>
              <th className="text-right py-2 font-medium">Spend Semanal</th>
              <th className="text-right py-2 font-medium">% do Total</th>
              <th className="text-right py-2 font-medium">Contribuicao</th>
              <th className="text-right py-2 font-medium">ROI</th>
            </tr>
          </thead>
          <tbody>
            {channels
              .sort((a, b) => b.spend - a.spend)
              .map((ch) => (
                <tr key={ch.name} className="border-t" style={{ borderColor: "var(--border)" }}>
                  <td className="py-2.5 flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full inline-block" style={{ background: ch.color }} />
                    {ch.name}
                  </td>
                  <td className="text-right text-xs" style={{ color: "var(--muted)" }}>{ch.type}</td>
                  <td className="text-right">{fmt(Math.round(ch.spend / 4))}/sem</td>
                  <td className="text-right">{((ch.spend / totalSpend) * 100).toFixed(1)}%</td>
                  <td className="text-right">{fmt(Math.round(ch.contribution / 4))}/sem</td>
                  <td className="text-right font-bold">{ch.roi.toFixed(2)}x</td>
                </tr>
              ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
