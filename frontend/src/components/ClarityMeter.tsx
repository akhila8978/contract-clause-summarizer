"use client";
export default function ClarityMeter({ value }: { value: number }) {
  const v = Math.max(0, Math.min(100, value || 0));
  const angle = (v / 100) * 180 - 90;
  const color = v >= 75 ? "#16a34a" : v >= 50 ? "#eab308" : "#dc2626";
  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 120" className="w-64">
        <path d="M10 110 A 90 90 0 0 1 190 110" fill="none" stroke="#e5e7eb" strokeWidth="14" />
        <path d="M10 110 A 90 90 0 0 1 190 110" fill="none" stroke={color} strokeWidth="14"
              strokeDasharray={`${(v / 100) * 283} 283`} strokeLinecap="round" />
        <g transform={`translate(100,110) rotate(${angle})`}>
          <line x1="0" y1="0" x2="0" y2="-78" stroke={color} strokeWidth="3" />
          <circle cx="0" cy="0" r="6" fill={color} />
        </g>
      </svg>
      <div className="text-2xl font-bold" style={{ color }}>{v.toFixed(1)}%</div>
      <div className="text-xs opacity-70">Contract Clarity</div>
    </div>
  );
}
