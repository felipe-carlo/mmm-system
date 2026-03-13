// Mock data for dashboard visualization (replaced by API calls when backend is connected)

export const channels = [
  { name: "google_ads", type: "digital", roi: 2.8, roiLower: 2.1, roiUpper: 3.5, spend: 45000, contribution: 126000, decay: 0.28, color: "#4285F4" },
  { name: "meta_ads", type: "digital", roi: 2.1, roiLower: 1.5, roiUpper: 2.7, spend: 38000, contribution: 79800, decay: 0.32, color: "#1877F2" },
  { name: "tiktok", type: "digital", roi: 3.2, roiLower: 1.8, roiUpper: 4.6, spend: 12000, contribution: 38400, decay: 0.25, color: "#000000" },
  { name: "tv", type: "offline_tv", roi: 1.4, roiLower: 0.8, roiUpper: 2.0, spend: 80000, contribution: 112000, decay: 0.62, color: "#E91E63" },
  { name: "radio", type: "offline_radio", roi: 0.9, roiLower: 0.4, roiUpper: 1.4, spend: 15000, contribution: 13500, decay: 0.48, color: "#FF9800" },
  { name: "ooh", type: "offline_ooh", roi: 1.1, roiLower: 0.6, roiUpper: 1.6, spend: 20000, contribution: 22000, decay: 0.55, color: "#9C27B0" },
  { name: "influencer", type: "influencer", roi: 2.5, roiLower: 1.2, roiUpper: 3.8, spend: 18000, contribution: 45000, decay: 0.33, color: "#00BCD4" },
  { name: "events", type: "events", roi: 0.6, roiLower: 0.2, roiUpper: 1.0, spend: 25000, contribution: 15000, decay: 0.18, color: "#4CAF50" },
];

export const totalRevenue = 580000;
export const baselineRevenue = 128300;
export const totalSpend = channels.reduce((s, c) => s + c.spend, 0);

export const weeklyData = Array.from({ length: 52 }, (_, i) => {
  const week = i + 1;
  const seasonal = Math.sin((week / 52) * 2 * Math.PI) * 15000;
  const trend = week * 200;
  return {
    week: `S${week}`,
    revenue: Math.round(totalRevenue / 52 + seasonal + trend + (Math.random() - 0.5) * 8000),
    baseline: Math.round(baselineRevenue / 52 + seasonal * 0.3),
    google_ads: Math.round(126000 / 52 + (Math.random() - 0.5) * 2000),
    meta_ads: Math.round(79800 / 52 + (Math.random() - 0.5) * 1500),
    tv: Math.round(112000 / 52 + seasonal * 0.5),
    tiktok: Math.round(38400 / 52 + (Math.random() - 0.5) * 1000),
    influencer: Math.round(45000 / 52 + (Math.random() - 0.5) * 800),
    others: Math.round(50500 / 52 + (Math.random() - 0.5) * 600),
  };
});

export const optimizedAllocation = channels.map((ch) => {
  const roiWeight = ch.roi / channels.reduce((s, c) => s + c.roi, 0);
  const recommended = Math.round(totalSpend * roiWeight);
  return {
    ...ch,
    recommended,
    changePct: Math.round(((recommended - ch.spend) / ch.spend) * 100),
  };
});

export const syncStatus = {
  spreadsheet_connected: true,
  spreadsheet_title: "MMM Data - Q1 2026",
  tabs: {
    media_spend: { last_synced: "2026-03-13T10:30:00Z", rows: 416, status: "success" },
    kpi: { last_synced: "2026-03-13T10:30:00Z", rows: 416, status: "success" },
    external_factors: { last_synced: "2026-03-12T15:00:00Z", rows: 416, status: "success" },
    channel_config: { last_synced: "2026-03-10T09:00:00Z", rows: 8, status: "success" },
  },
  channels: {
    google_ads: { last_synced: "2026-03-13T10:30:00Z", rows: 416, status: "success" },
    meta_ads: { last_synced: "2026-03-13T10:30:00Z", rows: 416, status: "success" },
    tiktok: { last_synced: "2026-03-12T15:00:00Z", rows: 390, status: "success" },
    tv: { last_synced: "2026-03-11T12:00:00Z", rows: 416, status: "success" },
    radio: { last_synced: "2026-03-11T12:00:00Z", rows: 416, status: "success" },
    ooh: { last_synced: "2026-03-10T09:00:00Z", rows: 400, status: "warning" },
    influencer: { last_synced: "2026-03-10T09:00:00Z", rows: 350, status: "success" },
    events: { last_synced: null as string | null, rows: null as number | null, status: "never_synced" },
  },
};

export const channelColors: Record<string, string> = {
  google_ads: "#4285F4",
  meta_ads: "#1877F2",
  tiktok: "#000000",
  tv: "#E91E63",
  radio: "#FF9800",
  ooh: "#9C27B0",
  influencer: "#00BCD4",
  events: "#4CAF50",
};

export const insights = [
  { type: "recommendation", priority: 1, title: "Canal com maior ROI: tiktok", description: "TikTok tem o maior retorno (ROI: 3.20x). Considere aumentar investimento.", channel: "tiktok", impact: "ROI 3.2x" },
  { type: "alert", priority: 1, title: "Canal com baixo retorno: events", description: "Events tem ROI de apenas 0.60x. Considere reduzir investimento ou revisar estrategia.", channel: "events", impact: "ROI 0.6x" },
  { type: "opportunity", priority: 2, title: "Canal subutilizado: influencer", description: "Influencer tem ROI alto (2.50x) e pode estar abaixo do ponto de saturacao.", channel: "influencer", impact: "ROI 2.5x" },
  { type: "alert", priority: 2, title: "Alta incerteza: tiktok", description: "O intervalo de confianca de TikTok e muito amplo ([1.80, 4.60]). Recomendamos testes controlados.", channel: "tiktok", impact: null },
  { type: "recommendation", priority: 3, title: "Efeito de longo prazo: tv", description: "TV tem alto carryover (decay: 0.62). Investimentos geram retorno por varias semanas.", channel: "tv", impact: null },
];
