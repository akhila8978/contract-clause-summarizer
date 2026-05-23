"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authStore";
import { useRouter } from "next/navigation";
import FileDrop from "@/components/FileDrop";
import toast from "react-hot-toast";

export default function PoliciesPage() {
  const router = useRouter();
  const { token, hydrated } = useAuth();
  const [policies, setPolicies] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [compareWith, setCompareWith] = useState<any>(null);
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { if (hydrated && !token) router.replace("/"); }, [hydrated, token, router]);
  useEffect(() => { if (token) load(); }, [token]);

  async function load() {
    const r = await api.get("/api/policies");
    setPolicies(r.data.policies);
  }

  async function upload(f: File) {
    setBusy(true);
    try {
      const fd = new FormData(); fd.append("file", f); fd.append("title", title || f.name);
      await api.post("/api/policies/upload", fd);
      toast.success("Policy uploaded & indexed");
      setTitle("");
      await load();
    } catch (e: any) { toast.error(e?.response?.data?.detail || "Upload failed"); }
    finally { setBusy(false); }
  }

  async function pick(p: any, side: "left" | "right") {
    const r = await api.get(`/api/policies/${p.id}`);
    if (side === "left") setSelected(r.data); else setCompareWith(r.data);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Company Policies</h1>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="font-semibold mb-2">Upload New Policy</div>
          <input className="input mb-2" placeholder="Title (optional)" value={title} onChange={e => setTitle(e.target.value)} />
          <FileDrop onFile={upload} />
          {busy && <div className="text-xs mt-2 opacity-70">Uploading…</div>}
          <div className="font-semibold mt-4 mb-2">Existing Policies</div>
          <ul className="space-y-1 text-sm max-h-80 overflow-y-auto">
            {policies.length === 0 && <li className="opacity-60 text-xs">None yet. Drop one above or seed the /data folder.</li>}
            {policies.map(p => (
              <li key={p.id} className="flex items-center gap-2">
                <button className="btn btn-ghost flex-1 justify-between" onClick={() => pick(p, "left")}>
                  <span className="truncate">{p.title}</span><span className="text-xs opacity-60">view</span>
                </button>
                <button className="btn btn-ghost" onClick={() => pick(p, "right")} title="Compare">⇄</button>
              </li>
            ))}
          </ul>
        </div>
        <div className="card p-4 md:col-span-2">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <div className="font-semibold mb-2 text-sm">📄 {selected?.title || "(select a policy)"}</div>
              <pre className="text-xs whitespace-pre-wrap max-h-[60vh] overflow-y-auto opacity-90">{selected?.text || ""}</pre>
            </div>
            <div>
              <div className="font-semibold mb-2 text-sm">🆚 {compareWith?.title || "(compare with)"}</div>
              <pre className="text-xs whitespace-pre-wrap max-h-[60vh] overflow-y-auto opacity-90">{compareWith?.text || ""}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
