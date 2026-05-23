"use client";

interface ProgressEvent {
  stage: string;
  message: string;
  pct: number;
}

const STAGE_ICONS: Record<string, string> = {
  parsing: "📄", extracting: "🔍", summarizing: "📝",
  executive: "✨", indexing: "🗂️", done: "✅", error: "❌",
};

export default function StreamingPanel({ events }: { events: ProgressEvent[] }) {
  if (!events.length) return null;
  const latest = events[events.length - 1];
  const isDone = latest?.stage === "done";

  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold">Analysis Progress</span>
        <span className="text-xs font-mono opacity-60">{latest?.pct ?? 0}%</span>
      </div>

      {/* Progress bar */}
      <div className="risk-bar">
        <div className="risk-bar-fill" style={{ width: `${latest?.pct ?? 0}%`, background: isDone ? "#22c55e" : "#2563eb" }} />
      </div>

      {/* Steps */}
      <div className="space-y-1.5">
        {events.map((e, i) => (
          <div key={i} className={`flex items-center gap-2.5 text-sm transition-opacity ${i === events.length - 1 ? "opacity-100" : "opacity-50"}`}>
            <span className="text-base w-5 text-center shrink-0">{STAGE_ICONS[e.stage] || "⚙️"}</span>
            <span className="flex-1">{e.message}</span>
            <span className="text-xs opacity-40 font-mono">{e.pct}%</span>
          </div>
        ))}
      </div>

      {isDone && (
        <div className="flex items-center gap-2 text-green-600 text-sm font-semibold">
          <span>✅</span> Analysis complete! Redirecting…
        </div>
      )}
    </div>
  );
}
