"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authStore";
import { AlertTriangle, FileText, Search, Upload, Calendar, DollarSign } from "lucide-react";

export default function Contracts() {
  const router = useRouter();
  const { token, hydrated } = useAuth();
  const [contracts, setContracts] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"uploaded_at"|"high_risk"|"end_date">("uploaded_at");

  useEffect(() => { if (hydrated && !token) router.replace("/"); }, [hydrated, token, router]);
  useEffect(() => {
    if (!token) return;
    api.get("/api/contracts").then(r => setContracts(r.data.contracts || []));
  }, [token]);

  const filtered = contracts
    .filter(c => !search || c.name.toLowerCase().includes(search.toLowerCase()) || c.company.toLowerCase().includes(search.toLowerCase()) || c.vendor?.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === "high_risk") return b.high_risk - a.high_risk;
      if (sortBy === "end_date") return (a.end_date || "z").localeCompare(b.end_date || "z");
      return b.uploaded_at - a.uploaded_at;
    });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <h1 className="text-xl font-bold">Contracts ({contracts.length})</h1>
        <Link href="/upload" className="btn btn-primary text-sm"><Upload size={14}/> Upload New</Link>
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="flex items-center gap-2 border rounded-lg px-3 py-2 flex-1 min-w-[200px] bg-white/50 dark:bg-white/5">
          <Search size={14} className="opacity-50"/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name, company, vendor…" className="bg-transparent outline-none flex-1 text-sm"/>
        </div>
        <select value={sortBy} onChange={e => setSortBy(e.target.value as any)} className="input text-sm max-w-[180px]">
          <option value="uploaded_at">Latest first</option>
          <option value="high_risk">Highest risk</option>
          <option value="end_date">End date</option>
        </select>
      </div>

      {filtered.length === 0 && (
        <div className="card p-8 text-center opacity-50">
          <FileText size={32} className="mx-auto mb-2"/><div>No contracts found.</div>
        </div>
      )}

      <div className="space-y-2">
        {filtered.map(c => (
          <Link key={c.id} href={`/contracts/${c.id}`}
            className="card p-4 flex flex-wrap gap-4 items-center hover:shadow-md transition cursor-pointer">
            <div className="flex-1 min-w-[200px]">
              <div className="font-semibold text-sm">{c.name}</div>
              <div className="text-xs opacity-60">{c.company} {c.vendor ? `· ${c.vendor}` : ""}</div>
              <div className="text-xs opacity-40 mt-0.5">{c.doc_type?.toUpperCase()} · {new Date(c.uploaded_at*1000).toLocaleDateString()}</div>
            </div>

            <div className="flex flex-wrap gap-3 text-xs">
              {c.tcv && c.tcv !== "Not Specified" && (
                <div className="flex items-center gap-1 opacity-70"><DollarSign size={11}/>{c.tcv}</div>
              )}
              {c.end_date && c.end_date !== "Not Specified" && (
                <div className="flex items-center gap-1 opacity-70"><Calendar size={11}/>Ends: {c.end_date}</div>
              )}
              {c.high_risk > 0 && (
                <div className="flex items-center gap-1 text-red-600 font-semibold"><AlertTriangle size={11}/>{c.high_risk} High/Critical</div>
              )}
              {c.missing_count > 0 && (
                <div className="badge badge-high">{c.missing_count} missing clauses</div>
              )}
              {c.conflict_count > 0 && (
                <div className="badge badge-medium">{c.conflict_count} conflicts</div>
              )}
              {c.risk_flag_count > 0 && (
                <div className="badge badge-medium">{c.risk_flag_count} flags</div>
              )}
            </div>

            <div className="text-blue-500 text-xs">View →</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
