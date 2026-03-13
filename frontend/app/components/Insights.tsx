"use client";

import { insights } from "../lib/mock-data";
import Card from "./Card";

const typeConfig: Record<string, { bg: string; border: string; icon: string; label: string }> = {
  recommendation: { bg: "rgba(67,97,238,0.06)", border: "var(--primary)", icon: "🎯", label: "Recomendacao" },
  alert: { bg: "rgba(247,37,133,0.06)", border: "var(--accent)", icon: "⚠️", label: "Alerta" },
  opportunity: { bg: "rgba(6,214,160,0.06)", border: "var(--success)", icon: "🚀", label: "Oportunidade" },
};

const priorityLabel: Record<number, string> = {
  1: "Alta",
  2: "Media",
  3: "Baixa",
};

export default function Insights() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold" style={{ color: "var(--foreground)" }}>
              Insights Semanais
            </h2>
            <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>
              Top recomendacoes baseadas no modelo mais recente
            </p>
          </div>
          <div className="flex gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: "var(--primary)" }} />
              Recomendacao
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: "var(--accent)" }} />
              Alerta
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: "var(--success)" }} />
              Oportunidade
            </div>
          </div>
        </div>
      </Card>

      {/* Insights list */}
      <div className="space-y-3">
        {insights.map((insight, i) => {
          const config = typeConfig[insight.type] || typeConfig.recommendation;
          return (
            <div
              key={i}
              className="rounded-xl border-l-4 p-5"
              style={{
                background: config.bg,
                borderLeftColor: config.border,
                borderTop: "1px solid var(--border)",
                borderRight: "1px solid var(--border)",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <span className="text-xl">{config.icon}</span>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>
                        {insight.title}
                      </h3>
                      <span
                        className="text-[10px] font-medium px-2 py-0.5 rounded-full"
                        style={{
                          background: "rgba(0,0,0,0.05)",
                          color: "var(--muted)",
                        }}
                      >
                        Prioridade {priorityLabel[insight.priority]}
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed" style={{ color: "var(--muted)" }}>
                      {insight.description}
                    </p>
                  </div>
                </div>
                {insight.impact && (
                  <span
                    className="text-sm font-bold whitespace-nowrap ml-4 px-3 py-1 rounded-lg"
                    style={{ background: "rgba(67,97,238,0.1)", color: "var(--primary)" }}
                  >
                    {insight.impact}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <p className="text-3xl font-bold" style={{ color: "var(--primary)" }}>
            {insights.filter((i) => i.type === "recommendation").length}
          </p>
          <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>Recomendacoes</p>
        </Card>
        <Card>
          <p className="text-3xl font-bold" style={{ color: "var(--accent)" }}>
            {insights.filter((i) => i.type === "alert").length}
          </p>
          <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>Alertas</p>
        </Card>
        <Card>
          <p className="text-3xl font-bold" style={{ color: "var(--success)" }}>
            {insights.filter((i) => i.type === "opportunity").length}
          </p>
          <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>Oportunidades</p>
        </Card>
      </div>
    </div>
  );
}
