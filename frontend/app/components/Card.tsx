export default function Card({
  children,
  className = "",
  title,
}: {
  children: React.ReactNode;
  className?: string;
  title?: string;
}) {
  return (
    <div
      className={`rounded-xl border p-5 ${className}`}
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      {title && (
        <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--foreground)" }}>
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}

export function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div
      className="rounded-xl border p-4"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <p className="text-xs font-medium mb-1" style={{ color: "var(--muted)" }}>
        {label}
      </p>
      <p className="text-2xl font-bold" style={{ color: color || "var(--foreground)" }}>
        {value}
      </p>
      {sub && (
        <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>
          {sub}
        </p>
      )}
    </div>
  );
}
