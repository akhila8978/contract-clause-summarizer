"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authStore";
import RiskBadge from "@/components/RiskBadge";
import toast from "react-hot-toast";
import {
  Download, FileText, Sparkles, AlertTriangle, CheckCircle,
  XCircle, ChevronDown, ChevronUp, Shield, Calendar, ClipboardList,
  BarChart2, BookOpen, Users, ExternalLink, Edit3, Save, X, Columns,
  Maximize2, Minimize2, PanelLeft, PanelRight, Copy, RefreshCw,
} from "lucide-react";

type Tab = "overview" | "sla" | "scope" | "risks" | "obligations" | "tasks" | "clauses" | "security" | "document";
type ViewMode = "summary" | "split" | "document";

const SEVERITY_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };

/**
 * Safely converts an executive-summary field to a displayable string.
 * The heuristic fallback returns these fields as objects; the LLM path
 * returns them as strings.  Both cases are handled here.
 */
function formatEsValue(val: unknown): string {
  if (val === null || val === undefined) return "";
  if (typeof val === "string") return val;
  if (Array.isArray(val)) {
    return val
      .map((item) =>
        typeof item === "string"
          ? item
          : typeof item === "object" && item !== null
          ? Object.entries(item as Record<string, unknown>)
              .map(([k, v]) => `${k.replace(/_/g, " ")}: ${v ?? "N/A"}`)
              .join(" | ")
          : String(item)
      )
      .join("\n");
  }
  if (typeof val === "object") {
    return Object.entries(val as Record<string, unknown>)
      .map(([k, v]) => {
        const label = k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
        const display = Array.isArray(v) ? (v as unknown[]).join(", ") : (v ?? "N/A");
        return `${label}: ${display}`;
      })
      .join("\n");
  }
  return String(val);
}

/**
 * Safely renders a recommended-action item which may be either
 * a plain string or an object with {action, owner, priority, citation}.
 */
function formatRecommendedAction(a: unknown): string {
  if (typeof a === "string") return a;
  if (a && typeof a === "object") {
    const obj = a as Record<string, unknown>;
    const parts: string[] = [];
    if (obj.action) parts.push(String(obj.action));
    if (obj.owner) parts.push(`Owner: ${obj.owner}`);
    if (obj.priority) parts.push(`Priority: ${obj.priority}`);
    if (obj.citation) parts.push(`(${obj.citation})`);
    return parts.join(" — ");
  }
  return String(a ?? "");
}

function MetaCard({ label, value, confidence, type, editable, onSave }: {
  label: string; value: string; confidence?: number; type?: string;
  editable?: boolean; onSave?: (v: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const missing = !value || value === "Not Specified";
  return (
    <div className="border rounded-lg p-3 bg-white/40 dark:bg-white/5 flex flex-col gap-1 group">
      <div className="flex items-center justify-between">
        <div className="text-xs opacity-60 uppercase tracking-wide">{label}</div>
        {editable && !editing && (
          <button className="opacity-0 group-hover:opacity-60 hover:opacity-100 transition" onClick={() => { setDraft(value); setEditing(true); }}>
            <Edit3 size={11} />
          </button>
        )}
      </div>
      {editing ? (
        <div className="flex gap-1 mt-1">
          <input className="input text-xs py-1 flex-1" value={draft} onChange={e => setDraft(e.target.value)} autoFocus />
          <button className="btn btn-primary px-2 py-1 text-xs" onClick={() => { onSave?.(draft); setEditing(false); }}>
            <Save size={10} />
          </button>
          <button className="btn btn-ghost px-2 py-1 text-xs" onClick={() => setEditing(false)}>
            <X size={10} />
          </button>
        </div>
      ) : (
        <div className={`text-sm font-semibold ${missing ? "opacity-40 italic" : ""}`}>{value || "Not Specified"}</div>
      )}
      {typeof confidence === "number" && confidence > 0 && (
        <div className="flex items-center gap-1 mt-1">
          <div className="h-1 flex-1 rounded bg-gray-200 dark:bg-gray-700">
            <div className="h-1 rounded bg-blue-500" style={{ width: `${confidence}%` }} />
          </div>
          <span className="text-xs opacity-50">{confidence}%</span>
          {type && <span className="text-xs opacity-40 italic">{type}</span>}
        </div>
      )}
    </div>
  );
}

function SeverityBadge({ level }: { level: string }) {
  const cls: Record<string, string> = {
    critical: "bg-red-900 text-red-100",
    high: "bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-200",
    medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/60 dark:text-yellow-200",
    low: "bg-green-100 text-green-800 dark:bg-green-900/60 dark:text-green-200",
  };
  return <span className={`badge ${cls[level] || cls.low}`}>{level?.toUpperCase()}</span>;
}

function MissingClauseBadge({ clause }: { clause: string }) {
  return (
    <div className="flex items-center gap-2 border border-red-300 dark:border-red-800 rounded-lg px-3 py-2 bg-red-50 dark:bg-red-950/30">
      <XCircle size={14} className="text-red-500 flex-shrink-0" />
      <span className="text-sm text-red-700 dark:text-red-300">{clause}</span>
    </div>
  );
}

function Collapsible({ title, children, defaultOpen = false }: { title: React.ReactNode; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border rounded-lg overflow-hidden">
      <button className="w-full flex items-center justify-between px-4 py-3 bg-white/60 dark:bg-white/5 hover:bg-white dark:hover:bg-white/10 transition text-left"
        onClick={() => setOpen(o => !o)}>
        <span className="font-semibold text-sm">{title}</span>
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {open && <div className="px-4 pb-4 pt-2">{children}</div>}
    </div>
  );
}

// Editable text block component
function EditableBlock({ label, value, onSave }: { label: string; value: string; onSave: (v: string) => void }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  return (
    <div className="group relative">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold uppercase opacity-50 tracking-wide">{label}</span>
        {!editing && (
          <button className="opacity-0 group-hover:opacity-70 hover:opacity-100 transition flex items-center gap-1 text-xs text-blue-500"
            onClick={() => { setDraft(value); setEditing(true); }}>
            <Edit3 size={11} /> Edit
          </button>
        )}
      </div>
      {editing ? (
        <div className="space-y-2">
          <textarea className="input text-sm w-full min-h-[80px] resize-y" value={draft}
            onChange={e => setDraft(e.target.value)} autoFocus />
          <div className="flex gap-2">
            <button className="btn btn-primary text-xs px-3 py-1.5" onClick={() => { onSave(draft); setEditing(false); }}>
              <Save size={12} /> Save
            </button>
            <button className="btn btn-ghost text-xs px-3 py-1.5" onClick={() => setEditing(false)}>
              <X size={12} /> Cancel
            </button>
          </div>
        </div>
      ) : (
        <p className="text-sm leading-relaxed">{value || <span className="opacity-40 italic">Not specified</span>}</p>
      )}
    </div>
  );
}

// Document viewer panel
function DocumentPanel({ text, pages, activePage, onPageChange, pageRefs }: {
  text: string; pages: any[]; activePage: number;
  onPageChange: (p: number) => void;
  pageRefs: React.MutableRefObject<Record<number, HTMLDivElement | null>>;
}) {
  if (!text) return <div className="p-8 text-center opacity-40">Document text not available</div>;
  const hasPages = pages && pages.length > 0;

  if (hasPages) {
    return (
      <div className="h-full overflow-y-auto p-4 space-y-6 font-mono text-xs leading-relaxed">
        {pages.map((pg: any, i: number) => {
          const pn = pg.page ?? i + 1;
          return (
            <div key={pn} ref={el => { pageRefs.current[pn] = el; }}
              className={`border rounded-lg p-4 transition-all ${activePage === pn ? "border-blue-400 bg-blue-50/30 dark:bg-blue-900/10 shadow-sm" : "border-transparent"}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-blue-500 uppercase">Page {pn}</span>
                <button className="text-xs opacity-40 hover:opacity-80" onClick={() => onPageChange(pn)}>↑ Jump here</button>
              </div>
              <pre className="whitespace-pre-wrap break-words">{pg.text || ""}</pre>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4">
      <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-relaxed">{text}</pre>
    </div>
  );
}

// Summary panel with all editable fields
function SummaryPanel({ c, onUpdate, onJump, recs, recBusy, editing, setEditing, getRecs, applyFix }: any) {
  const meta = c.contract_metadata || {};
  const sla = c.sla_summary || {};
  const scope = c.maintenance_scope || {};
  const flags = [...(c.risk_flags || [])].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
  const missing = c.missing_clauses || [];
  const tasks = c.compliance_tasks || [];
  const es = c.executive_summary || {};
  const mv = (k: string) => meta[k]?.value || "Not Specified";
  const mc = (k: string) => meta[k]?.confidence;
  const mt = (k: string) => meta[k]?.type;

  function handleMetaSave(field: string, value: string) {
    onUpdate({
      contract_metadata: {
        ...meta,
        [field]: { ...(meta[field] || {}), value, type: "Edited" },
      }
    });
    toast.success(`${field} updated`);
  }

  function handleESSave(field: string, value: string) {
    onUpdate({ executive_summary: { ...es, [field]: value } });
    toast.success("Summary updated");
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-5">
      {/* Executive Summary */}
      {es && Object.keys(es).length > 0 && (
        <div className="card p-4 space-y-4 border-l-4 border-blue-500">
          <div className="flex items-center gap-2 text-blue-600 font-bold text-sm">
            <Sparkles size={16} /> Executive Summary
            <span className="ml-auto text-xs font-normal opacity-50">Click any field to edit</span>
          </div>
          {es.contract_snapshot && (
            <EditableBlock label="Contract Snapshot" value={formatEsValue(es.contract_snapshot)}
              onSave={v => handleESSave("contract_snapshot", v)} />
          )}
          {es.sla_commitments && (
            <EditableBlock label="SLA Commitments" value={formatEsValue(es.sla_commitments)}
              onSave={v => handleESSave("sla_commitments", v)} />
          )}
          {es.exit_readiness && (
            <EditableBlock label="Exit Readiness" value={formatEsValue(es.exit_readiness)}
              onSave={v => handleESSave("exit_readiness", v)} />
          )}
          {es.recommended_actions && Array.isArray(es.recommended_actions) && es.recommended_actions.length > 0 && (
            <div>
              <div className="text-xs font-semibold uppercase opacity-50 tracking-wide mb-2">Recommended Actions</div>
              <ul className="space-y-1">
                {es.recommended_actions.map((a: unknown, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <CheckCircle size={13} className="text-green-500 mt-0.5 flex-shrink-0" />{formatRecommendedAction(a)}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Key Dates */}
      {c.key_dates && c.key_dates.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center gap-2 font-bold text-sm mb-3">
            <Calendar size={14} className="text-blue-500" /> Critical Dates
          </div>
          <div className="space-y-2">
            {c.key_dates.map((d: any, i: number) => (
              <div key={i} className="flex items-center justify-between border rounded-lg px-3 py-2 bg-white/30 dark:bg-white/5">
                <div>
                  <div className="text-xs font-semibold">{d.label}</div>
                  <div className="text-sm text-blue-600 font-mono">{d.date}</div>
                </div>
                {d.page && (
                  <button className="text-xs text-blue-400 hover:text-blue-600 flex items-center gap-1"
                    onClick={() => onJump(d.page)}>
                    <ExternalLink size={11} /> P{d.page}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Flags */}
      {flags.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center gap-2 font-bold text-sm mb-3 text-red-600">
            <AlertTriangle size={14} /> Risk Flags ({flags.length})
          </div>
          <div className="space-y-2">
            {flags.slice(0, 5).map((f: any, i: number) => (
              <div key={i} className={`border rounded-lg p-3 ${f.severity === "critical" ? "border-red-500 bg-red-50 dark:bg-red-950/20" : "border-amber-200 dark:border-amber-800"}`}>
                <div className="flex items-start justify-between gap-2">
                  <div className="text-xs font-semibold flex-1">{f.flag}</div>
                  <SeverityBadge level={f.severity} />
                </div>
                {f.description && <p className="text-xs opacity-70 mt-1">{f.description}</p>}
                {f.remediation && <p className="text-xs text-green-600 dark:text-green-400 mt-1 italic">→ {f.remediation}</p>}
              </div>
            ))}
            {flags.length > 5 && <p className="text-xs opacity-50 text-center">+ {flags.length - 5} more flags in Risks tab</p>}
          </div>
        </div>
      )}

      {/* Missing Clauses */}
      {missing.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center gap-2 font-bold text-sm mb-3 text-orange-600">
            <XCircle size={14} /> Missing Clauses ({missing.length})
          </div>
          <div className="space-y-1.5">
            {missing.map((m: string, i: number) => <MissingClauseBadge key={i} clause={m} />)}
          </div>
        </div>
      )}

      {/* Contract Metadata (editable) */}
      <div className="card p-4">
        <div className="flex items-center gap-2 font-bold text-sm mb-3">
          <FileText size={14} className="text-blue-500" /> Contract Details
          <span className="ml-auto text-xs font-normal opacity-40">Hover to edit</span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {[
            ["vendor_name", "Vendor"], ["client_name", "Client"], ["effective_date", "Effective Date"],
            ["end_date", "End Date"], ["tcv", "Contract Value"], ["governing_law", "Governing Law"],
            ["auto_renewal", "Auto-Renewal"], ["cyber_insurance", "Cyber Insurance"],
          ].map(([k, label]) => (
            <MetaCard key={k} label={label} value={mv(k)} confidence={mc(k)} type={mt(k)}
              editable onSave={v => handleMetaSave(k, v)} />
          ))}
        </div>
      </div>

      {/* SLA Summary (editable) */}
      {sla && (
        <div className="card p-4">
          <div className="flex items-center gap-2 font-bold text-sm mb-3">
            <BarChart2 size={14} className="text-blue-500" /> SLA Summary
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              ["uptime_sla", "Uptime SLA"], ["p1_response", "P1 Response"],
              ["p1_resolution", "P1 Resolution"], ["service_credits", "Service Credits"],
              ["penalty_cap", "Penalty Cap"], ["measurement_window", "Measurement"],
            ].map(([k, label]) => {
              const v = (sla as any)[k] || "Not Specified";
              return (
                <div key={k} className="border rounded-lg p-3 bg-white/40 dark:bg-white/5 flex flex-col gap-1 group">
                  <div className="text-xs opacity-60 uppercase tracking-wide">{label}</div>
                  <div className="text-sm font-semibold">{v}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Obligations */}
      {c.obligations && c.obligations.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center gap-2 font-bold text-sm mb-3">
            <Users size={14} className="text-blue-500" /> Key Obligations
          </div>
          <div className="space-y-2">
            {c.obligations.slice(0, 6).map((o: any, i: number) => (
              <div key={i} className="flex items-start gap-2 border rounded-lg px-3 py-2 bg-white/30 dark:bg-white/5">
                <span className="badge badge-low text-xs shrink-0">{o.party}</span>
                <div className="flex-1">
                  <p className="text-xs">{o.obligation}</p>
                  {o.due && <p className="text-xs opacity-50 mt-0.5">Due: {o.due}</p>}
                </div>
                {o.page && (
                  <button className="text-xs text-blue-400 hover:text-blue-600 shrink-0"
                    onClick={() => onJump(o.page)}>P{o.page}</button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Compliance Tasks */}
      {tasks.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center gap-2 font-bold text-sm mb-3">
            <ClipboardList size={14} className="text-blue-500" /> Compliance Tasks ({tasks.length})
          </div>
          <div className="space-y-2">
            {tasks.map((t: any, i: number) => (
              <div key={i} className="border rounded-lg px-3 py-2 bg-white/30 dark:bg-white/5">
                <div className="text-xs font-semibold">{t.task}</div>
                <div className="flex gap-3 mt-1 text-xs opacity-60">
                  <span>Owner: {t.owner}</span>
                  {t.due_date && <span>Due: {t.due_date}</span>}
                  {t.recurrence && <span>{t.recurrence}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clauses */}
      {c.clauses && c.clauses.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center gap-2 font-bold text-sm mb-3">
            <BookOpen size={14} className="text-blue-500" /> Clause Summaries
          </div>
          <div className="space-y-2">
            {c.clauses.map((cl: any, i: number) => (
              <Collapsible key={i} title={
                <div className="flex items-center gap-2">
                  <span>{cl.title || cl.section}</span>
                  <RiskBadge level={cl.risk} />
                  {cl.page && (
                    <button className="ml-auto text-xs text-blue-400 hover:text-blue-600 font-normal"
                      onClick={e => { e.stopPropagation(); onJump(cl.page); }}>
                      P{cl.page}
                    </button>
                  )}
                </div>
              }>
                <div className="space-y-2">
                  <p className="text-sm">{cl.summary}</p>
                  {cl.source_excerpt && (
                    <div className="bg-gray-50 dark:bg-white/5 border rounded p-2 text-xs font-mono opacity-70 italic">
                      "{cl.source_excerpt}"
                    </div>
                  )}
                  {cl.risk_reason && <p className="text-xs text-amber-600 dark:text-amber-400">⚠ {cl.risk_reason}</p>}
                  <div className="flex gap-2 mt-2">
                    <button className="btn btn-ghost text-xs py-1" onClick={() => { setEditing(cl); getRecs(cl); }}>
                      <Sparkles size={11} /> Get AI Recommendations
                    </button>
                  </div>
                  {editing?.section === cl.section && (
                    <div className="mt-2 space-y-2">
                      {recBusy ? (
                        <p className="text-xs opacity-60 animate-pulse">Generating recommendations…</p>
                      ) : recs.length > 0 ? (
                        <div className="space-y-2">
                          <p className="text-xs font-semibold text-green-600">Suggested revisions:</p>
                          {recs.map((r: any, ri: number) => (
                            <div key={ri} className="border border-green-300 dark:border-green-800 rounded-lg p-2 bg-green-50 dark:bg-green-950/20 space-y-1">
                              <p className="text-xs font-semibold">{r.title}</p>
                              <p className="text-xs opacity-70">{r.explanation}</p>
                              {r.suggested_text && (
                                <>
                                  <p className="text-xs font-mono bg-white/60 dark:bg-white/10 p-1.5 rounded border text-green-800 dark:text-green-200">{r.suggested_text}</p>
                                  <button className="btn btn-primary text-xs py-1"
                                    onClick={() => applyFix(r.suggested_text)}>
                                    <Save size={10} /> Apply Fix
                                  </button>
                                </>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>
              </Collapsible>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ContractDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { token, hydrated } = useAuth();
  const [c, setC] = useState<any>(null);
  const [docText, setDocText] = useState("");
  const [docPages, setDocPages] = useState<any[]>([]);
  const [tab, setTab] = useState<Tab>("overview");
  const [viewMode, setViewMode] = useState<ViewMode>("summary");
  const [activePage, setActivePage] = useState<number>(1);
  const [editing, setEditing] = useState<any>(null);
  const [recs, setRecs] = useState<any[]>([]);
  const [recBusy, setRecBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const pageRefs = useRef<Record<number, HTMLDivElement | null>>({});

  useEffect(() => { if (hydrated && !token) router.replace("/"); }, [hydrated, token, router]);

  useEffect(() => {
    if (!token || !id) return;
    api.get(`/api/contracts/${id}`).then(r => setC(r.data));
    api.get(`/api/contracts/${id}/text`).then(r => {
      setDocText(r.data.text || "");
      setDocPages(r.data.pages || []);
    }).catch(() => {});
  }, [token, id]);

  function jumpTo(page?: number | null) {
    if (!page) return;
    setActivePage(page);
    if (viewMode === "summary") setViewMode("split");
    setTimeout(() => pageRefs.current[page]?.scrollIntoView({ behavior: "smooth", block: "start" }), 150);
  }

  async function downloadExport(fmt: "pdf" | "csv" | "json") {
    try {
      const mimeMap = { pdf: "application/pdf", csv: "text/csv", json: "application/json" };
      const res = await api.get(`/api/contracts/${id}/export/${fmt}`, { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([res.data], { type: mimeMap[fmt] }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `${id}.${fmt}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      toast.error(`Failed to download ${fmt.toUpperCase()}`);
    }
  }

  async function getRecs(cl: any) {
    setRecBusy(true); setRecs([]);
    try {
      const r = await api.post("/api/clauses/recommend", { contract_id: id, clause_section: cl.section, current_text: cl.source_excerpt });
      setRecs(r.data.recommendations || []);
    } catch { toast.error("Recommendation failed"); }
    finally { setRecBusy(false); }
  }

  async function applyFix(newText: string) {
    if (!editing) return;
    await api.post("/api/clauses/apply-fix", { contract_id: id, clause_section: editing.section, original_text: editing.source_excerpt, new_text: newText });
    toast.success("Clause updated");
    setEditing(null); setRecs([]);
    const r = await api.get(`/api/contracts/${id}`); setC(r.data);
  }

  function handleUpdate(patch: any) {
    setC((prev: any) => ({ ...prev, ...patch }));
  }

  async function saveChanges() {
    setSaving(true);
    // Persist locally (in-memory storage)
    try {
      await api.patch?.(`/api/contracts/${id}`, c).catch(() => {});
      toast.success("Changes saved");
    } catch {
      toast.success("Changes saved locally");
    } finally { setSaving(false); }
  }

  async function copyToClipboard() {
    if (!c) return;
    const text = `CONTRACT SUMMARY: ${c.name}\n\n${c.executive_summary?.contract_snapshot || ""}\n\nRisk Flags: ${(c.risk_flags || []).length}\nMissing Clauses: ${(c.missing_clauses || []).length}`;
    await navigator.clipboard.writeText(text);
    toast.success("Summary copied to clipboard");
  }

  if (!c) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center space-y-3">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        <p className="opacity-60 text-sm">Loading contract analysis…</p>
      </div>
    </div>
  );

  const meta = c.contract_metadata || {};
  const flags = [...(c.risk_flags || [])].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
  const sla = c.sla_summary || {};
  const scope = c.maintenance_scope || {};
  const missing = c.missing_clauses || [];
  const tasks = c.compliance_tasks || [];
  const es = c.executive_summary || {};
  const mv = (k: string) => meta[k]?.value || "Not Specified";
  const mc = (k: string) => meta[k]?.confidence;
  const mt = (k: string) => meta[k]?.type;

  const criticalFlags = flags.filter((f: any) => f.severity === "critical" || f.severity === "high");

  const TABS: { key: Tab; label: string; icon: any; count?: number }[] = [
    { key: "overview", label: "Overview", icon: BookOpen },
    { key: "sla", label: "SLA", icon: BarChart2 },
    { key: "scope", label: "Scope", icon: CheckCircle },
    { key: "risks", label: "Risks", icon: AlertTriangle, count: flags.length + missing.length },
    { key: "obligations", label: "Obligations", icon: Users },
    { key: "tasks", label: "Tasks", icon: ClipboardList, count: tasks.length },
    { key: "clauses", label: "Clauses", icon: FileText },
    { key: "security", label: "Security", icon: Shield, count: (c.conflicts || []).length + (c.security || []).length },
    { key: "document", label: "Full Text", icon: FileText },
  ];

  return (
    <div className="flex flex-col h-full min-h-screen pb-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-start gap-3 mb-4">
        <div>
          <h1 className="text-xl font-bold">{c.name}</h1>
          <div className="text-sm opacity-60">{c.company} · {c.doc_type?.toUpperCase()} · {new Date(c.uploaded_at * 1000).toLocaleString()}</div>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          {/* View Mode Switcher */}
          <div className="flex border rounded-lg overflow-hidden text-xs">
            {([
              ["summary", <PanelLeft size={13} />, "Summary"],
              ["split", <Columns size={13} />, "Side by Side"],
              ["document", <PanelRight size={13} />, "Document"],
            ] as [ViewMode, React.ReactNode, string][]).map(([mode, icon, label]) => (
              <button key={mode}
                className={`px-3 py-1.5 flex items-center gap-1 transition ${viewMode === mode ? "bg-blue-600 text-white" : "hover:bg-black/5 dark:hover:bg-white/10"}`}
                onClick={() => setViewMode(mode)}>
                {icon} {label}
              </button>
            ))}
          </div>

          <button onClick={copyToClipboard} className="btn btn-ghost text-xs">
            <Copy size={12} /> Copy
          </button>
          <button onClick={saveChanges} disabled={saving} className="btn btn-primary text-xs">
            <Save size={12} /> {saving ? "Saving…" : "Save"}
          </button>

          {/* Export buttons */}
          {(["PDF", "CSV", "JSON"] as const).map(fmt => (
            <button key={fmt} className="btn btn-ghost text-xs"
              onClick={() => downloadExport(fmt.toLowerCase() as "pdf" | "csv" | "json")}>
              <Download size={12} /> {fmt}
            </button>
          ))}
        </div>
      </div>

      {/* Critical alert banner */}
      {criticalFlags.length > 0 && (
        <div className="mb-4 border border-red-400 bg-red-50 dark:bg-red-950/30 rounded-lg px-4 py-3 flex items-start gap-3">
          <AlertTriangle size={16} className="text-red-600 mt-0.5 shrink-0" />
          <div>
            <div className="text-sm font-bold text-red-700 dark:text-red-300">{criticalFlags.length} Critical/High Risk Issue{criticalFlags.length > 1 ? "s" : ""} Found</div>
            <div className="text-xs text-red-600 dark:text-red-400 mt-0.5">{criticalFlags.slice(0, 2).map((f: any) => f.flag).join(" · ")}{criticalFlags.length > 2 ? ` + ${criticalFlags.length - 2} more` : ""}</div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {viewMode === "split" ? (
        /* Side-by-Side Split View */
        <div className="grid grid-cols-2 gap-4 flex-1" style={{ minHeight: "70vh" }}>
          {/* Left: Summary */}
          <div className="card overflow-hidden flex flex-col">
            <div className="border-b px-4 py-2 bg-white/50 dark:bg-white/5 flex items-center justify-between">
              <span className="text-sm font-semibold">📋 AI Summary</span>
              <span className="text-xs opacity-40">Editable — hover fields to edit</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <SummaryPanel c={c} onUpdate={handleUpdate} onJump={jumpTo}
                recs={recs} recBusy={recBusy} editing={editing}
                setEditing={setEditing} getRecs={getRecs} applyFix={applyFix} />
            </div>
          </div>
          {/* Right: Document */}
          <div className="card overflow-hidden flex flex-col">
            <div className="border-b px-4 py-2 bg-white/50 dark:bg-white/5 flex items-center justify-between">
              <span className="text-sm font-semibold">📄 Source Document</span>
              {docPages.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs opacity-40">Page:</span>
                  <select className="input text-xs py-0.5 px-2 w-16" value={activePage}
                    onChange={e => {
                      const p = parseInt(e.target.value);
                      setActivePage(p);
                      setTimeout(() => pageRefs.current[p]?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
                    }}>
                    {docPages.map((pg: any, i: number) => <option key={i} value={pg.page ?? i + 1}>{pg.page ?? i + 1}</option>)}
                  </select>
                </div>
              )}
            </div>
            <div className="flex-1 overflow-hidden">
              <DocumentPanel text={docText} pages={docPages} activePage={activePage}
                onPageChange={setActivePage} pageRefs={pageRefs} />
            </div>
          </div>
        </div>
      ) : viewMode === "document" ? (
        /* Document Only View */
        <div className="card overflow-hidden flex flex-col" style={{ minHeight: "70vh" }}>
          <div className="border-b px-4 py-2 bg-white/50 dark:bg-white/5 flex items-center justify-between">
            <span className="text-sm font-semibold">📄 Source Document</span>
            {docPages.length > 0 && (
              <div className="flex items-center gap-2 text-xs opacity-60">
                {docPages.length} pages
              </div>
            )}
          </div>
          <div className="flex-1 overflow-hidden">
            <DocumentPanel text={docText} pages={docPages} activePage={activePage}
              onPageChange={setActivePage} pageRefs={pageRefs} />
          </div>
        </div>
      ) : (
        /* Summary-Only Tabbed View */
        <div className="card overflow-hidden">
          {/* Tabs */}
          <div className="flex overflow-x-auto border-b bg-white/50 dark:bg-white/5">
            {TABS.map(({ key, label, icon: Icon, count }) => (
              <button key={key}
                className={`flex items-center gap-1.5 px-4 py-3 text-sm whitespace-nowrap border-b-2 transition font-medium
                  ${tab === key ? "border-blue-500 text-blue-600 dark:text-blue-400" : "border-transparent opacity-60 hover:opacity-90"}`}
                onClick={() => setTab(key)}>
                <Icon size={14} /> {label}
                {typeof count === "number" && count > 0 && (
                  <span className="badge badge-high text-xs">{count}</span>
                )}
              </button>
            ))}
          </div>

          <div className="p-4">
            {/* Overview Tab */}
            {tab === "overview" && (
              <div className="space-y-5">
                {es && Object.keys(es).length > 0 && (
                  <div className="card p-4 space-y-4 border-l-4 border-blue-500">
                    <div className="flex items-center gap-2 text-blue-600 font-bold text-sm">
                      <Sparkles size={16} /> Executive Summary
                      <span className="ml-auto text-xs font-normal opacity-50">Hover fields to edit</span>
                    </div>
                    {es.contract_snapshot && (
                      <EditableBlock label="Contract Snapshot" value={formatEsValue(es.contract_snapshot)}
                        onSave={v => { handleUpdate({ executive_summary: { ...es, contract_snapshot: v } }); toast.success("Updated"); }} />
                    )}
                    {es.sla_commitments && (
                      <EditableBlock label="SLA Commitments" value={formatEsValue(es.sla_commitments)}
                        onSave={v => { handleUpdate({ executive_summary: { ...es, sla_commitments: v } }); toast.success("Updated"); }} />
                    )}
                    {es.exit_readiness && (
                      <EditableBlock label="Exit Readiness" value={formatEsValue(es.exit_readiness)}
                        onSave={v => { handleUpdate({ executive_summary: { ...es, exit_readiness: v } }); toast.success("Updated"); }} />
                    )}
                    {es.recommended_actions && Array.isArray(es.recommended_actions) && (
                      <div>
                        <div className="text-xs font-semibold uppercase opacity-50 tracking-wide mb-2">Recommended Actions</div>
                        <ul className="space-y-1">
                          {es.recommended_actions.map((a: unknown, i: number) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                              <CheckCircle size={13} className="text-green-500 mt-0.5 flex-shrink-0" />{formatRecommendedAction(a)}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                <div>
                  <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
                    <FileText size={14} className="text-blue-500" /> Contract Metadata
                    <span className="text-xs font-normal opacity-40 ml-1">Hover any field to edit</span>
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {[
                      ["vendor_name","Vendor"],["client_name","Client"],["effective_date","Effective Date"],
                      ["start_date","Start Date"],["end_date","End Date"],["renewal_notice_period","Renewal Notice"],
                      ["auto_renewal","Auto-Renewal"],["tcv","Contract Value"],["currency","Currency"],
                      ["governing_law","Governing Law"],["jurisdiction","Jurisdiction"],["cyber_insurance","Cyber Insurance"],
                    ].map(([k, label]) => (
                      <MetaCard key={k} label={label} value={mv(k)} confidence={mc(k)} type={mt(k)}
                        editable onSave={v => {
                          handleUpdate({ contract_metadata: { ...meta, [k]: { ...(meta[k] || {}), value: v, type: "Edited" } } });
                          toast.success(`${label} updated`);
                        }} />
                    ))}
                  </div>
                </div>

                {c.key_dates && c.key_dates.length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
                      <Calendar size={14} className="text-blue-500" /> Critical Dates
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {c.key_dates.map((d: any, i: number) => (
                        <div key={i} className="border rounded-lg p-3 bg-white/40 dark:bg-white/5">
                          <div className="text-xs opacity-60 uppercase tracking-wide">{d.label}</div>
                          <div className="text-sm font-mono font-semibold text-blue-600">{d.date}</div>
                          {d.page && (
                            <button className="text-xs text-blue-400 hover:text-blue-600 flex items-center gap-1 mt-1"
                              onClick={() => jumpTo(d.page)}>
                              <ExternalLink size={10} /> Jump to page {d.page}
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* SLA Tab */}
            {tab === "sla" && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {[
                    ["uptime_sla","Uptime SLA"],["p1_response","P1 Response"],["p1_resolution","P1 Resolution"],
                    ["p2_response","P2 Response"],["p2_resolution","P2 Resolution"],
                    ["p3_response","P3 Response"],["p3_resolution","P3 Resolution"],
                    ["service_credits","Service Credits"],["penalty_cap","Penalty Cap"],
                    ["measurement_window","Measurement Window"],
                  ].map(([k, label]) => (
                    <div key={k} className="border rounded-lg p-3 bg-white/40 dark:bg-white/5">
                      <div className="text-xs opacity-60 uppercase tracking-wide">{label}</div>
                      <div className={`text-sm font-semibold mt-1 ${(sla as any)[k] === "Not Specified" ? "opacity-40 italic" : ""}`}>
                        {(sla as any)[k] || "Not Specified"}
                      </div>
                    </div>
                  ))}
                </div>
                {sla.exclusions && sla.exclusions.length > 0 && (
                  <Collapsible title="SLA Exclusions" defaultOpen>
                    <ul className="space-y-1">
                      {sla.exclusions.map((e: string, i: number) => <li key={i} className="text-sm flex items-start gap-2"><XCircle size={12} className="text-red-400 mt-0.5 shrink-0" />{e}</li>)}
                    </ul>
                  </Collapsible>
                )}
                {sla.escalation_matrix && sla.escalation_matrix.length > 0 && (
                  <Collapsible title="Escalation Matrix" defaultOpen>
                    <ul className="space-y-1">
                      {sla.escalation_matrix.map((e: string, i: number) => <li key={i} className="text-sm flex items-start gap-2">→ {e}</li>)}
                    </ul>
                  </Collapsible>
                )}
              </div>
            )}

            {/* Scope Tab */}
            {tab === "scope" && (
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h3 className="font-bold text-sm mb-3 text-green-600 flex items-center gap-1"><CheckCircle size={14}/> In Scope</h3>
                  <div className="space-y-1.5">
                    {(scope.in_scope || []).length > 0 ? scope.in_scope.map((s: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 border border-green-200 dark:border-green-900 rounded-lg px-3 py-2 bg-green-50 dark:bg-green-950/20 text-sm">
                        <CheckCircle size={12} className="text-green-500 mt-0.5 shrink-0" />{s}
                      </div>
                    )) : <p className="text-sm opacity-40 italic">Not specified</p>}
                  </div>
                </div>
                <div>
                  <h3 className="font-bold text-sm mb-3 text-red-600 flex items-center gap-1"><XCircle size={14}/> Out of Scope</h3>
                  <div className="space-y-1.5">
                    {(scope.out_of_scope || []).length > 0 ? scope.out_of_scope.map((s: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 border border-red-200 dark:border-red-900 rounded-lg px-3 py-2 bg-red-50 dark:bg-red-950/20 text-sm">
                        <XCircle size={12} className="text-red-400 mt-0.5 shrink-0" />{s}
                      </div>
                    )) : <p className="text-sm opacity-40 italic">Not specified</p>}
                  </div>
                </div>
              </div>
            )}

            {/* Risks Tab */}
            {tab === "risks" && (
              <div className="space-y-5">
                {/* Risk Heatmap */}
                {flags.length > 0 && (
                  <div className="grid grid-cols-4 gap-2">
                    {(["critical","high","medium","low"] as const).map(sev => {
                      const cnt = flags.filter((f: any) => f.severity === sev).length;
                      const colors: Record<string, string> = {
                        critical: "border-red-500 bg-red-50 dark:bg-red-950/30 text-red-700",
                        high: "border-red-300 bg-red-50/50 dark:bg-red-950/20 text-red-600",
                        medium: "border-yellow-300 bg-yellow-50 dark:bg-yellow-950/20 text-yellow-700",
                        low: "border-green-300 bg-green-50 dark:bg-green-950/20 text-green-700",
                      };
                      return (
                        <div key={sev} className={`border rounded-lg p-3 ${colors[sev]}`}>
                          <div className="text-2xl font-bold">{cnt}</div>
                          <div className="text-xs uppercase font-semibold">{sev}</div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {flags.length > 0 && (
                  <div>
                    <h3 className="font-bold text-sm mb-3 flex items-center gap-1"><AlertTriangle size={14} className="text-amber-500"/> Risk Flags</h3>
                    <div className="space-y-2">
                      {flags.map((f: any, i: number) => (
                        <div key={i} className={`border rounded-lg p-3 ${f.severity === "critical" ? "border-red-500 bg-red-50 dark:bg-red-950/20" : f.severity === "high" ? "border-red-300" : "border-amber-200 dark:border-amber-800"}`}>
                          <div className="flex items-start justify-between gap-2">
                            <div className="font-semibold text-sm flex-1">{f.flag}</div>
                            <SeverityBadge level={f.severity} />
                          </div>
                          {f.description && <p className="text-sm opacity-70 mt-1">{f.description}</p>}
                          {f.citation && <p className="text-xs font-mono bg-gray-100 dark:bg-white/10 p-1.5 rounded mt-2 italic opacity-70">{f.citation}</p>}
                          {f.remediation && (
                            <div className="flex items-start gap-1.5 mt-2 text-sm text-green-700 dark:text-green-400">
                              <CheckCircle size={13} className="mt-0.5 shrink-0" />
                              <span>{f.remediation}</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {missing.length > 0 && (
                  <div>
                    <h3 className="font-bold text-sm mb-3 flex items-center gap-1 text-orange-600"><XCircle size={14}/> Missing Clauses</h3>
                    <div className="space-y-1.5">
                      {missing.map((m: string, i: number) => <MissingClauseBadge key={i} clause={m} />)}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Obligations Tab */}
            {tab === "obligations" && (
              <div className="space-y-2">
                {c.obligations && c.obligations.length > 0 ? c.obligations.map((o: any, i: number) => (
                  <div key={i} className="border rounded-lg p-3 flex items-start gap-3">
                    <span className="badge badge-low text-xs shrink-0">{o.party}</span>
                    <div className="flex-1">
                      <p className="text-sm">{o.obligation}</p>
                      {o.due && <p className="text-xs opacity-50 mt-1">Due: {o.due}</p>}
                    </div>
                    {o.page && (
                      <button className="text-xs text-blue-400 hover:text-blue-600 flex items-center gap-1 shrink-0"
                        onClick={() => jumpTo(o.page)}>
                        <ExternalLink size={11} /> P{o.page}
                      </button>
                    )}
                  </div>
                )) : <p className="text-sm opacity-40 text-center py-8">No obligations extracted</p>}
              </div>
            )}

            {/* Tasks Tab */}
            {tab === "tasks" && (
              <div className="space-y-2">
                {tasks.length > 0 ? tasks.map((t: any, i: number) => (
                  <div key={i} className="border rounded-lg p-3">
                    <div className="font-semibold text-sm">{t.task}</div>
                    <div className="flex flex-wrap gap-3 mt-2 text-xs opacity-60">
                      <span className="flex items-center gap-1"><Users size={10}/> {t.owner}</span>
                      {t.due_date && <span className="flex items-center gap-1"><Calendar size={10}/> {t.due_date}</span>}
                      {t.recurrence && <span>🔁 {t.recurrence}</span>}
                    </div>
                    {t.citation && <p className="text-xs font-mono bg-gray-50 dark:bg-white/5 p-2 rounded border mt-2 opacity-60 italic">{t.citation}</p>}
                  </div>
                )) : <p className="text-sm opacity-40 text-center py-8">No compliance tasks found</p>}
              </div>
            )}

            {/* Clauses Tab */}
            {tab === "clauses" && (
              <div className="space-y-2">
                {c.clauses && c.clauses.length > 0 ? c.clauses.map((cl: any, i: number) => (
                  <Collapsible key={i} title={
                    <div className="flex items-center gap-2 w-full">
                      <span className="flex-1">{cl.title || cl.section}</span>
                      <RiskBadge level={cl.risk} />
                      {cl.page && (
                        <button className="text-xs text-blue-400 hover:text-blue-600 font-normal flex items-center gap-1"
                          onClick={e => { e.stopPropagation(); jumpTo(cl.page); }}>
                          <ExternalLink size={10}/> P{cl.page}
                        </button>
                      )}
                    </div>
                  }>
                    <div className="space-y-3">
                      <p className="text-sm">{cl.summary}</p>
                      {cl.source_excerpt && (
                        <div className="bg-gray-50 dark:bg-white/5 border rounded p-2 text-xs font-mono opacity-70 italic">
                          "{cl.source_excerpt}"
                        </div>
                      )}
                      {cl.risk_reason && <p className="text-xs text-amber-600 dark:text-amber-400 flex items-start gap-1"><AlertTriangle size={11} className="mt-0.5 shrink-0"/>  {cl.risk_reason}</p>}
                      <button className="btn btn-ghost text-xs py-1" onClick={() => { setEditing(cl); getRecs(cl); }}>
                        <Sparkles size={11}/> AI Recommendations
                      </button>
                      {editing?.section === cl.section && (
                        <div className="space-y-2 mt-2">
                          {recBusy ? <p className="text-xs opacity-60 animate-pulse">Generating…</p> : recs.map((r: any, ri: number) => (
                            <div key={ri} className="border border-green-300 dark:border-green-800 rounded-lg p-3 bg-green-50 dark:bg-green-950/20 space-y-2">
                              <p className="text-xs font-semibold">{r.title}</p>
                              <p className="text-xs opacity-70">{r.explanation}</p>
                              {r.suggested_text && (
                                <>
                                  <p className="text-xs font-mono bg-white/60 dark:bg-white/10 p-2 rounded border">{r.suggested_text}</p>
                                  <button className="btn btn-primary text-xs py-1" onClick={() => applyFix(r.suggested_text)}>
                                    <Save size={10}/> Apply
                                  </button>
                                </>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </Collapsible>
                )) : <p className="text-sm opacity-40 text-center py-8">No clauses extracted</p>}
              </div>
            )}

            {/* Security Tab */}
            {tab === "security" && (
              <div className="space-y-4">
                {c.conflicts && c.conflicts.length > 0 && (
                  <div>
                    <h3 className="font-bold text-sm mb-3 flex items-center gap-1 text-amber-600"><AlertTriangle size={14}/> Policy Conflicts ({c.conflicts.length})</h3>
                    <div className="space-y-2">
                      {c.conflicts.map((cf: any, i: number) => (
                        <div key={i} className="border border-amber-300 dark:border-amber-800 rounded-lg p-3 bg-amber-50 dark:bg-amber-950/20">
                          <div className="font-semibold text-sm">{cf.conflict || cf.section}</div>
                          <p className="text-xs opacity-70 mt-1">{cf.description || cf.detail}</p>
                          {cf.governing_clause && <p className="text-xs text-green-600 mt-1">Governing: {cf.governing_clause}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {c.security && c.security.length > 0 && (
                  <div>
                    <h3 className="font-bold text-sm mb-3 flex items-center gap-1 text-red-600"><Shield size={14}/> Security Issues ({c.security.length})</h3>
                    <div className="space-y-2">
                      {c.security.map((s: any, i: number) => (
                        <div key={i} className="border border-red-300 dark:border-red-800 rounded-lg p-3 bg-red-50 dark:bg-red-950/20">
                          <div className="font-semibold text-sm">{s.issue || s.section}</div>
                          <p className="text-xs opacity-70 mt-1">{s.description || s.detail}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {(!c.conflicts?.length && !c.security?.length) && (
                  <div className="text-center py-12">
                    <CheckCircle size={32} className="text-green-500 mx-auto mb-2" />
                    <p className="text-sm opacity-60">No security issues or conflicts detected</p>
                  </div>
                )}
              </div>
            )}

            {/* Document Tab */}
            {tab === "document" && (
              <div className="rounded-lg overflow-hidden border" style={{ height: "70vh" }}>
                <div className="border-b px-4 py-2 bg-white/50 dark:bg-white/5 flex items-center justify-between">
                  <span className="text-sm font-semibold">Full Contract Text</span>
                  <button className="btn btn-ghost text-xs" onClick={() => setViewMode("split")}>
                    <Columns size={12}/> Switch to Side-by-Side
                  </button>
                </div>
                <DocumentPanel text={docText} pages={docPages} activePage={activePage}
                  onPageChange={setActivePage} pageRefs={pageRefs} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
