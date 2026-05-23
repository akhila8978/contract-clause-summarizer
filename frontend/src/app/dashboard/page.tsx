"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/authStore";
import { api } from "@/lib/api";
import {
  FileText, Upload, RefreshCcw, Shield, MessageSquare, Database,
  AlertTriangle, CheckCircle, XCircle, TrendingUp, Calendar, ArrowRight,
  Clock, DollarSign, Layers,
} from "lucide-react";
import toast from "react-hot-toast";

function StatCard({ label, value, icon: Icon, color, sub }: { label: string; value: number | string; icon: any; color: string; sub?: string }) {
  return (
    <div className="card p-5 flex flex-col gap-2">
      <div className={`flex items-center gap-2 ${color} opacity-80`}>
        <Icon size={16} />
        <span className="text-xs font-semibold uppercase tracking-wide">{label}</span>
      </div>
      <div className={`text-4xl font-bold ${color}`}>{value}</div>
      {sub && <div className="text-xs opacity-50">{sub}</div>}
    </div>
  );
}

function NavTile({ href, icon: Icon, title, sub, count, accent }: {
  href: string; icon: any; title: string; sub: string; count?: number; accent?: string;
}) {
  return (
    <Link href={href} className="card p-5 hover:shadow-lg transition-all cursor-pointer group flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${accent || "bg-blue-50 dark:bg-blue-900/30"}`}>
          <Icon size={18} className={accent ? "text-white" : "text-blue-500"} />
        </div>
        {typeof count === "number" && (
          <span className="text-sm font-bold opacity-70">{count}</span>
        )}
      </div>
      <div>
        <div className="font-semibold">{title}</div>
        <div className="text-xs opacity-50 mt-0.5">{sub}</div>
      </div>
      <div className="text-blue-500 text-xs flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
        Open <ArrowRight size={11} />
      </div>
    </Link>
  );
}

export default function Dashboard() {
  const router = useRouter();
  const { token, hydrated, user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [contracts, setContracts] = useState<any[]>([]);
  const [counts, setCounts] = useState({ contracts: 0, policies: 0, renewals: 0 });
  const [reindexing, setReindexing] = useState(false);

  useEffect(() => { if (hydrated && !token) router.replace("/"); }, [hydrated, token, router]);
  useEffect(() => {
    if (!token) return;
    Promise.all([
      api.get("/api/contracts"), api.get("/api/policies"), api.get("/api/renewals"), api.get("/api/rag/stats"),
    ]).then(([c, p, r, s]) => {
      const ctrs = c.data.contracts || [];
      setContracts(ctrs);
      setCounts({ contracts: ctrs.length, policies: p.data.policies.length, renewals: r.data.renewals.length });
      setStats(s.data);
    }).catch(() => {});
  }, [token]);

  async function reindex() {
    setReindexing(true);
    try {
      const res = await api.post("/api/rag/reindex");
      toast.success("Vector index rebuilt from /data folder");
      setStats(res.data.stats);
    } catch (e: any) { toast.error(e?.response?.data?.detail || "Reindex failed"); }
    finally { setReindexing(false); }
  }

  const totalFlags = contracts.reduce((s, c) => s + (c.risk_flag_count || 0), 0);
  const totalCritical = contracts.reduce((s, c) => s + (c.high_risk || 0), 0);
  const totalMissing = contracts.reduce((s, c) => s + (c.missing_count || 0), 0);
  const totalConflicts = contracts.reduce((s, c) => s + (c.conflict_count || 0), 0);
  const recentRisk = contracts.filter(c => c.high_risk > 0).slice(0, 5);
  const soonExpiring = contracts.filter(c => c.end_date && c.end_date !== "Not Specified").slice(0, 3);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="space-y-6 pb-8">
      {/* Welcome */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{greeting}, {user?.name?.split(" ")[0] || "there"} 👋</h1>
          <p className="text-sm opacity-50 mt-1">IT Contract Intelligence Platform</p>
        </div>
        <Link href="/upload" className="btn btn-primary">
          <Upload size={16} /> Upload Contract
        </Link>
      </div>

      {/* Risk Stats */}
      {contracts.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Contracts" value={counts.contracts} icon={FileText} color="text-blue-600" />
          <StatCard label="Critical/High Risks" value={totalCritical} icon={AlertTriangle} color="text-red-600"
            sub={totalCritical > 0 ? "Needs attention" : "All clear"} />
          <StatCard label="Missing Clauses" value={totalMissing} icon={XCircle} color="text-orange-600" />
          <StatCard label="Policy Conflicts" value={totalConflicts} icon={Layers} color="text-purple-600" />
        </div>
      )}

      {/* Quick Actions */}
      <div>
        <h2 className="text-sm font-bold uppercase opacity-50 tracking-wide mb-3">Quick Actions</h2>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
          <NavTile href="/contracts" icon={FileText} title="Browse Contracts" sub="View all analyzed contracts" count={counts.contracts} />
          <NavTile href="/upload" icon={Upload} title="Upload New Contract" sub="AI parsing & risk analysis" accent="bg-blue-600" />
          <NavTile href="/renewals" icon={RefreshCcw} title="Renewal Tracker" sub="Compare old vs new versions" count={counts.renewals} />
          <NavTile href="/policies" icon={Shield} title="Company Policies" sub="Manage & compare policies" count={counts.policies} />
          <NavTile href="/chat" icon={MessageSquare} title="Legal Q&A" sub="Ask AI about your contracts" />
          <div className="card p-5 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-xl bg-purple-50 dark:bg-purple-900/30 flex items-center justify-center">
                <Database size={18} className="text-purple-500" />
              </div>
              <span className="text-xs opacity-40 font-semibold">RAG</span>
            </div>
            <div>
              <div className="font-semibold">Vector Index</div>
              <div className="text-xs opacity-50 mt-0.5">
                {stats ? Object.entries(stats).map(([k, v]: any) => `${k}: ${v}`).join(" · ") : "Loading…"}
              </div>
            </div>
            <button onClick={reindex} disabled={reindexing}
              className="btn btn-ghost text-xs justify-center mt-auto">
              {reindexing ? "Indexing…" : "Rebuild Index"}
            </button>
          </div>
        </div>
      </div>

      {/* Contracts needing attention */}
      {recentRisk.length > 0 && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold flex items-center gap-2 text-red-600">
              <AlertTriangle size={16} /> Contracts Needing Attention
            </h2>
            <Link href="/contracts?sort=high_risk" className="text-xs text-blue-500 hover:underline">View all →</Link>
          </div>
          <div className="space-y-2">
            {recentRisk.map(c => (
              <Link key={c.id} href={`/contracts/${c.id}`}
                className="flex items-center justify-between py-3 px-3 rounded-xl hover:bg-black/3 dark:hover:bg-white/5 transition cursor-pointer border border-transparent hover:border-red-200 dark:hover:border-red-900">
                <div>
                  <div className="text-sm font-semibold">{c.name}</div>
                  <div className="text-xs opacity-50">{c.company}{c.vendor ? ` · ${c.vendor}` : ""}</div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {c.high_risk > 0 && <span className="badge badge-critical">{c.high_risk} critical/high</span>}
                  {c.missing_count > 0 && <span className="badge badge-high">{c.missing_count} missing</span>}
                  <ArrowRight size={14} className="opacity-30" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recent contracts */}
      {contracts.length > 0 && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold flex items-center gap-2">
              <Clock size={16} className="text-blue-500" /> Recently Uploaded
            </h2>
            <Link href="/contracts" className="text-xs text-blue-500 hover:underline">See all →</Link>
          </div>
          <div className="space-y-2">
            {contracts.slice(0, 5).map(c => (
              <Link key={c.id} href={`/contracts/${c.id}`}
                className="flex items-center justify-between py-2.5 px-3 rounded-xl hover:bg-black/3 dark:hover:bg-white/5 transition cursor-pointer">
                <div className="flex items-center gap-3">
                  <FileText size={16} className="text-blue-400 shrink-0" />
                  <div>
                    <div className="text-sm font-medium">{c.name}</div>
                    <div className="text-xs opacity-50">{c.company} · {new Date(c.uploaded_at * 1000).toLocaleDateString()}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {c.tcv && c.tcv !== "Not Specified" && (
                    <span className="text-xs opacity-60 flex items-center gap-1"><DollarSign size={10}/>{c.tcv}</span>
                  )}
                  {c.risk_flag_count > 0 && <span className="badge badge-medium">{c.risk_flag_count} flags</span>}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {contracts.length === 0 && (
        <div className="card p-12 text-center">
          <div className="w-20 h-20 bg-blue-50 dark:bg-blue-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText size={36} className="text-blue-400" />
          </div>
          <h3 className="font-bold text-lg mb-2">No contracts yet</h3>
          <p className="text-sm opacity-50 mb-5">Upload your first contract to get started with AI-powered analysis</p>
          <Link href="/upload" className="btn btn-primary mx-auto">
            <Upload size={15}/> Upload Your First Contract
          </Link>
        </div>
      )}
    </div>
  );
}
