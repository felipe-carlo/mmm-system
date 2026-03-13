"use client";

import { useState } from "react";
import { syncStatus, channelColors } from "../lib/mock-data";
import Card from "./Card";

type TabInfo = { last_synced: string | null; rows: number | null; status: string };
type SyncData = typeof syncStatus;

const TAB_CONFIG: { key: string; label: string; icon: string }[] = [
  { key: "media_spend", label: "Media Spend", icon: "💰" },
  { key: "kpi", label: "KPI", icon: "📊" },
  { key: "external_factors", label: "Fatores Externos", icon: "🌍" },
  { key: "channel_config", label: "Configuracao de Canais", icon: "⚙️" },
];

function formatChannelName(name: string): string {
  return name
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function formatTimestamp(iso: string | null): string {
  if (!iso) return "Nunca sincronizado";
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "Agora mesmo";
  if (diffMin < 60) return `ha ${diffMin} min`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `ha ${diffHours}h`;
  const diffDays = Math.floor(diffHours / 24);
  return `ha ${diffDays}d`;
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "success"
      ? "var(--success)"
      : status === "warning"
        ? "var(--warning)"
        : status === "error"
          ? "var(--accent)"
          : "var(--border)";
  return (
    <span
      className="inline-block w-2 h-2 rounded-full flex-shrink-0"
      style={{ background: color }}
    />
  );
}

function SyncButton({
  loading,
  onClick,
  small,
}: {
  loading: boolean;
  onClick: () => void;
  small?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`font-medium rounded-lg transition-all whitespace-nowrap ${
        small ? "text-xs px-3 py-1.5" : "text-sm px-4 py-2"
      }`}
      style={{
        background: loading ? "var(--border)" : "var(--primary)",
        color: loading ? "var(--muted)" : "#fff",
        cursor: loading ? "not-allowed" : "pointer",
      }}
    >
      {loading ? "Sincronizando..." : "Sincronizar"}
    </button>
  );
}

function TabRow({
  info,
  label,
}: {
  info: TabInfo;
  label?: string;
}) {
  return (
    <div className="flex items-center gap-3 text-xs" style={{ color: "var(--muted)" }}>
      <StatusDot status={info.status} />
      {label && (
        <span className="font-medium" style={{ color: "var(--foreground)" }}>
          {label}
        </span>
      )}
      {info.rows != null && (
        <span
          className="px-2 py-0.5 rounded-full text-[10px] font-medium"
          style={{ background: "rgba(67,97,238,0.08)", color: "var(--primary)" }}
        >
          {info.rows} linhas
        </span>
      )}
      <span>{formatTimestamp(info.last_synced)}</span>
    </div>
  );
}

export default function GoogleSheetsSync() {
  const [data, setData] = useState<SyncData>(syncStatus);
  const [loadingAll, setLoadingAll] = useState(false);
  const [loadingTab, setLoadingTab] = useState<string | null>(null);
  const [loadingChannel, setLoadingChannel] = useState<string | null>(null);
  const [expandedMedia, setExpandedMedia] = useState(true);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  async function handleSyncAll() {
    setLoadingAll(true);
    try {
      const res = await fetch(`${API_BASE}/api/sync`, { method: "POST" });
      if (res.ok) {
        // Refresh status
        const statusRes = await fetch(`${API_BASE}/api/sync/status`);
        if (statusRes.ok) {
          const updated = await statusRes.json();
          setData((prev) => ({ ...prev, tabs: updated.tabs, channels: updated.channels }));
        }
      }
    } catch {
      // Network error - status stays unchanged
    } finally {
      setLoadingAll(false);
    }
  }

  async function handleSyncTab(tabName: string) {
    setLoadingTab(tabName);
    try {
      const res = await fetch(`${API_BASE}/api/sync/tab/${tabName}`, { method: "POST" });
      if (res.ok) {
        const result = await res.json();
        setData((prev) => ({
          ...prev,
          tabs: {
            ...prev.tabs,
            [tabName]: {
              last_synced: result.last_synced,
              rows: result.rows_fetched,
              status: "success",
            },
          },
        }));
      }
    } catch {
      // Network error
    } finally {
      setLoadingTab(null);
    }
  }

  async function handleSyncChannel(channelName: string) {
    setLoadingChannel(channelName);
    try {
      const res = await fetch(`${API_BASE}/api/sync/channel/${channelName}`, { method: "POST" });
      if (res.ok) {
        const result = await res.json();
        setData((prev) => ({
          ...prev,
          channels: {
            ...prev.channels,
            [channelName]: {
              last_synced: result.last_synced,
              rows: result.rows_fetched,
              status: "success",
            },
          },
        }));
      }
    } catch {
      // Network error
    } finally {
      setLoadingChannel(null);
    }
  }

  const channelEntries = Object.entries(data.channels) as [string, TabInfo][];

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold" style={{ color: "var(--foreground)" }}>
              Google Sheets
            </h2>
            <div className="flex items-center gap-2 mt-1">
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{
                  background: data.spreadsheet_connected ? "var(--success)" : "var(--accent)",
                }}
              />
              <p className="text-sm" style={{ color: "var(--muted)" }}>
                {data.spreadsheet_connected
                  ? data.spreadsheet_title || "Conectado"
                  : "Desconectado"}
              </p>
            </div>
          </div>
          <SyncButton loading={loadingAll} onClick={handleSyncAll} />
        </div>
      </Card>

      {/* Tab cards */}
      <div className="space-y-4">
        {TAB_CONFIG.map((tab) => {
          const info = (data.tabs as Record<string, TabInfo>)[tab.key] || {
            last_synced: null,
            rows: null,
            status: "never_synced",
          };
          const isMedia = tab.key === "media_spend";

          return (
            <Card key={tab.key}>
              {/* Tab header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xl">{tab.icon}</span>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3
                        className="text-sm font-semibold"
                        style={{ color: "var(--foreground)" }}
                      >
                        {tab.label}
                      </h3>
                      {isMedia && (
                        <button
                          onClick={() => setExpandedMedia(!expandedMedia)}
                          className="text-xs px-2 py-0.5 rounded transition-all"
                          style={{
                            background: "rgba(67,97,238,0.08)",
                            color: "var(--primary)",
                          }}
                        >
                          {channelEntries.length} canais {expandedMedia ? "▲" : "▼"}
                        </button>
                      )}
                    </div>
                    <TabRow info={info} />
                  </div>
                </div>
                <SyncButton
                  loading={loadingTab === tab.key}
                  onClick={() => handleSyncTab(tab.key)}
                />
              </div>

              {/* Expanded channel list for media_spend */}
              {isMedia && expandedMedia && (
                <div className="mt-4 pt-4 space-y-3" style={{ borderTop: "1px solid var(--border)" }}>
                  {channelEntries.map(([name, chInfo]) => (
                    <div
                      key={name}
                      className="flex items-center justify-between py-2 px-3 rounded-lg"
                      style={{ background: "var(--background)" }}
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className="inline-block w-3 h-3 rounded-full flex-shrink-0"
                          style={{ background: channelColors[name] || "var(--muted)" }}
                        />
                        <div>
                          <p
                            className="text-sm font-medium"
                            style={{ color: "var(--foreground)" }}
                          >
                            {formatChannelName(name)}
                          </p>
                          <TabRow info={chInfo} />
                        </div>
                      </div>
                      <SyncButton
                        small
                        loading={loadingChannel === name}
                        onClick={() => handleSyncChannel(name)}
                      />
                    </div>
                  ))}
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <p className="text-3xl font-bold" style={{ color: "var(--primary)" }}>
            {Object.values(data.tabs).filter((t) => (t as TabInfo).status === "success").length}
          </p>
          <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>
            Tabs sincronizadas
          </p>
        </Card>
        <Card>
          <p className="text-3xl font-bold" style={{ color: "var(--success)" }}>
            {channelEntries.filter(([, c]) => c.status === "success").length}
          </p>
          <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>
            Canais ativos
          </p>
        </Card>
        <Card>
          <p className="text-3xl font-bold" style={{ color: "var(--warning)" }}>
            {channelEntries.filter(([, c]) => c.status === "never_synced" || c.status === "warning").length}
          </p>
          <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>
            Pendentes
          </p>
        </Card>
      </div>
    </div>
  );
}
