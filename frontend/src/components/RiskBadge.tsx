export default function RiskBadge({ level }: { level?: string }) {
  const l = (level || "low").toLowerCase();
  return <span className={`badge badge-${l}`}>{l.toUpperCase()}</span>;
}
