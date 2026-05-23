"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authStore";
import FileDrop from "@/components/FileDrop";
import StreamingPanel from "@/components/StreamingPanel";
import ClarityMeter from "@/components/ClarityMeter";
import { openProgressWS, makeSessionId } from "@/lib/ws";
import toast from "react-hot-toast";

export default function RenewalsPage() {
  const router = useRouter();
  const { token, hydrated } = useAuth();
  const [contracts, setContracts] = useState<any[]>([]);
  const [old, setOld] = useState<string>("");
  const [events, setEvents] = useState<any[]>([]);
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { if (hydrated && !token) router.replace("/"); }, [hydrated, token, router]);
  useEffect(() => { if (token) api.get("/api/contracts").then(r => setContracts(r.data.contracts)); }, [token]);

  async function go(f: File) {
    if (!old) { toast.error("Pick an existing contract first"); return; }
    setBusy(true); setEvents([]); setResult(null);
    const sid = makeSessionId();
    const ws = openProgressWS(sid, e => { if (e.event === "progress") setEvents(p => [...p, e.data]); });
    await new Promise(r => setTimeout(r, 250));
    try {
      const fd = new FormData();
      fd.append("file", f); fd.append("old_contract_id", old); fd.append("session_id", sid);
      const r = await api.post("/api/renewals/analyze", fd);
      setResult(r.data);
      toast.success("Renewal analyzed");
    } catch (e: any) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { ws.close(); setBusy(false); }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Contract Renewals</h1>
      <div className="card p-4 space-y-3 max-w-3xl">
        <label className="text-sm">Existing contract</label>
        <select className="input" value={old} onChange={e => setOld(e.target.value)}>
          <option value="">— select —</option>
          {contracts.map(c => <option key={c.id} value={c.id}>{c.company} — {c.name}</option>)}
        </select>
        <FileDrop onFile={go} label="Drop the renewal PDF/DOCX" />
      </div>
      <StreamingPanel events={events} />
      {result && (
        <div className="grid md:grid-cols-3 gap-4">
          <div className="card p-4 flex items-center justify-center">
            <ClarityMeter value={result.diff?.clarity?.overall_pct || 0} />
          </div>
          <div className="card p-4 md:col-span-2 max-h-[60vh] overflow-y-auto">
            <div className="font-semibold mb-2">Changed clauses</div>
            <ul className="space-y-2 text-sm">
              {(result.diff?.changed || []).map((c: any, i: number) => (
                <li key={i} className="border rounded p-2">
                  <b>{c.section}</b>
                  <div className="text-xs"><span className="text-red-500 line-through">{c.before}</span></div>
                  <div className="text-xs"><span className="text-green-600">{c.after}</span></div>
                  <div className="text-xs italic opacity-80 mt-1">{c.impact}</div>
                </li>
              ))}
            </ul>
            <div className="font-semibold mt-3 mb-1">Added</div>
            <ul className="text-xs list-disc ml-5">{(result.diff?.added || []).map((a:any,i:number) => <li key={i}>{typeof a === "string" ? a : JSON.stringify(a)}</li>)}</ul>
            <div className="font-semibold mt-3 mb-1">Removed</div>
            <ul className="text-xs list-disc ml-5">{(result.diff?.removed || []).map((a:any,i:number) => <li key={i}>{typeof a === "string" ? a : JSON.stringify(a)}</li>)}</ul>
            <div className="font-semibold mt-3 mb-1">Risks</div>
            <ul className="text-xs list-disc ml-5">{(result.diff?.risks || []).map((a:any,i:number) => <li key={i}>{typeof a === "string" ? a : JSON.stringify(a)}</li>)}</ul>
            <div className="font-semibold mt-3 mb-1">Key dates</div>
            <ul className="text-xs list-disc ml-5">{(result.diff?.key_dates || []).map((a:any,i:number) => <li key={i}>{typeof a === "string" ? a : JSON.stringify(a)}</li>)}</ul>
          </div>
        </div>
      )}
    </div>
  );
}
