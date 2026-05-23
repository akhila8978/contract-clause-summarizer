"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authStore";
import StreamingPanel from "@/components/StreamingPanel";
import { openProgressWS, makeSessionId } from "@/lib/ws";
import toast from "react-hot-toast";
import { Upload, FileText, X, Building2, AlertCircle } from "lucide-react";

export default function UploadContract() {
  const router = useRouter();
  const { token, hydrated } = useAuth();
  const [company, setCompany] = useState("Acme Corp");
  const [events, setEvents] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => { if (hydrated && !token) router.replace("/"); }, [hydrated, token, router]);

  const handleFile = useCallback((f: File) => {
    const allowed = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"];
    const extOk = f.name.match(/\.(pdf|docx|txt)$/i);
    if (!allowed.includes(f.type) && !extOk) {
      toast.error("Only PDF, DOCX, or TXT files are supported");
      return;
    }
    if (f.size > 20 * 1024 * 1024) {
      toast.error("File too large. Max 20MB.");
      return;
    }
    setFile(f);
  }, []);

  async function go() {
    if (!file || busy) return;
    setBusy(true); setEvents([]);
    const sid = makeSessionId();
    const ws = openProgressWS(sid, (e) => {
      if (e.event === "progress") setEvents(prev => [...prev, e.data]);
    });
    await new Promise(r => setTimeout(r, 250));
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("company", company);
      fd.append("session_id", sid);
      const res = await api.post("/api/contracts/upload", fd);
      toast.success("Contract analyzed successfully!");
      router.push(`/contracts/${res.data.id}`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Upload failed");
      setBusy(false);
    } finally { ws.close(); }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Upload Contract</h1>
        <p className="text-sm opacity-60 mt-1">AI-powered analysis for IT maintenance and outsourcing contracts</p>
      </div>

      <div className="card p-6 space-y-5">
        {/* Company field */}
        <div>
          <label className="text-sm font-medium flex items-center gap-2 mb-2">
            <Building2 size={14} className="text-blue-500" /> Counterparty / Company Name
          </label>
          <input className="input" placeholder="e.g. Acme Corp" value={company}
            onChange={e => setCompany(e.target.value)} disabled={busy} />
        </div>

        {/* Drop zone */}
        <div>
          <label className="text-sm font-medium flex items-center gap-2 mb-2">
            <FileText size={14} className="text-blue-500" /> Contract Document
          </label>
          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer
              ${dragOver ? "border-blue-400 bg-blue-50 dark:bg-blue-950/20" : "border-gray-300 dark:border-gray-700"}
              ${file ? "border-green-400 bg-green-50 dark:bg-green-950/20" : ""}
              ${busy ? "opacity-50 cursor-not-allowed" : "hover:border-blue-300 hover:bg-blue-50/30 dark:hover:bg-white/5"}`}
            onDrop={e => { e.preventDefault(); setDragOver(false); if (!busy && e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); }}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onClick={() => { if (!busy) document.getElementById("file-input")?.click(); }}
          >
            {file ? (
              <div className="space-y-2">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto">
                  <FileText size={24} className="text-green-600" />
                </div>
                <div className="font-semibold text-green-700 dark:text-green-400">{file.name}</div>
                <div className="text-xs opacity-50">{(file.size / 1024).toFixed(1)} KB</div>
                {!busy && (
                  <button className="text-xs text-red-400 hover:text-red-600 flex items-center gap-1 mx-auto"
                    onClick={e => { e.stopPropagation(); setFile(null); }}>
                    <X size={11} /> Remove file
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto">
                  <Upload size={28} className="text-blue-500" />
                </div>
                <div>
                  <p className="font-semibold">Drop your contract here</p>
                  <p className="text-sm opacity-50 mt-1">or click to browse</p>
                </div>
                <p className="text-xs opacity-40">PDF, DOCX, or TXT · Max 20MB</p>
              </div>
            )}
          </div>
          <input id="file-input" type="file" className="hidden" accept=".pdf,.docx,.txt"
            onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />
        </div>

        {/* What will be analyzed */}
        <div className="border border-blue-200 dark:border-blue-900 rounded-xl p-4 bg-blue-50/50 dark:bg-blue-950/20">
          <div className="text-xs font-semibold text-blue-600 mb-2">What we analyze:</div>
          <div className="grid grid-cols-2 gap-1">
            {["Clause extraction & risk flags", "SLA & performance metrics", "Maintenance scope (in/out)", "Missing critical clauses", "Policy conflict detection", "Compliance task generation", "Executive summary", "Critical dates & obligations"].map(item => (
              <div key={item} className="flex items-center gap-1.5 text-xs opacity-70">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0"></div>{item}
              </div>
            ))}
          </div>
        </div>

        <button className="btn btn-primary w-full justify-center py-3 text-base"
          onClick={go} disabled={!file || busy || !company.trim()}>
          {busy ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z"/>
              </svg>
              Analyzing…
            </span>
          ) : (
            <span className="flex items-center gap-2"><Sparkles size={16}/> Analyze Contract</span>
          )}
        </button>
      </div>

      <StreamingPanel events={events} />
    </div>
  );
}

function Sparkles({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
    </svg>
  );
}
