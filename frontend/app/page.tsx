"use client";

import { useState } from "react";
import ROI360 from "./components/ROI360";
import MediaOptimizer from "./components/MediaOptimizer";
import MetricsManager from "./components/MetricsManager";
import Forecasting from "./components/Forecasting";
import Insights from "./components/Insights";
import GoogleSheetsSync from "./components/GoogleSheetsSync";

const tabs = [
  { id: "roi360", label: "ROI 360", icon: "📊" },
  { id: "optimizer", label: "Media Optimizer", icon: "⚡" },
  { id: "metrics", label: "Metrics", icon: "📈" },
  { id: "forecast", label: "Forecasting", icon: "🔮" },
  { id: "insights", label: "Insights", icon: "💡" },
  { id: "sheets", label: "Google Sheets", icon: "📋" },
];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("roi360");

  return (
    <div className="min-h-screen" style={{ background: "var(--background)" }}>
      <header
        className="sticky top-0 z-10 border-b backdrop-blur-sm"
        style={{ background: "rgba(255,255,255,0.9)", borderColor: "var(--border)" }}
      >
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center font-bold text-white text-sm"
              style={{ background: "var(--primary)" }}
            >
              M
            </div>
            <div>
              <h1 className="text-lg font-semibold" style={{ color: "var(--foreground)" }}>
                MMM System
              </h1>
              <p className="text-xs" style={{ color: "var(--muted)" }}>
                Marketing Mix Modeling
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs" style={{ color: "var(--muted)" }}>
            <span className="inline-block w-2 h-2 rounded-full" style={{ background: "var(--success)" }} />
            Modelo atualizado em 13/03/2026
          </div>
        </div>
        <div className="max-w-[1400px] mx-auto px-6 flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="px-4 py-2.5 text-sm font-medium rounded-t-lg transition-all"
              style={{
                color: activeTab === tab.id ? "var(--primary)" : "var(--muted)",
                background: activeTab === tab.id ? "var(--background)" : "transparent",
                borderBottom: activeTab === tab.id ? "2px solid var(--primary)" : "2px solid transparent",
              }}
            >
              <span className="mr-1.5">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-6 py-6">
        {activeTab === "roi360" && <ROI360 />}
        {activeTab === "optimizer" && <MediaOptimizer />}
        {activeTab === "metrics" && <MetricsManager />}
        {activeTab === "forecast" && <Forecasting />}
        {activeTab === "insights" && <Insights />}
        {activeTab === "sheets" && <GoogleSheetsSync />}
      </main>
    </div>
  );
}
