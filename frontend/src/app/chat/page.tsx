"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authStore";
import { Send, ThumbsUp, ThumbsDown } from "lucide-react";
import toast from "react-hot-toast";

export default function ChatPage() {
  const router = useRouter();
  const { token, hydrated } = useAuth();
  const [contracts, setContracts] = useState<any[]>([]);
  const [contract, setContract] = useState<string>("");
  const [sessionId] = useState<string>("chat_" + Math.random().toString(36).slice(2, 9));
  const [history, setHistory] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { if (hydrated && !token) router.replace("/"); }, [hydrated, token, router]);
  useEffect(() => { if (token) api.get("/api/contracts").then(r => setContracts(r.data.contracts)); }, [token]);

  async function send() {
    if (!input.trim()) return;
    setBusy(true);
    const msg = input; setInput("");
    setHistory(h => [...h, { role: "user", content: msg }]);
    try {
      const r = await api.post("/api/chat", { contract_id: contract || null, session_id: sessionId, message: msg });
      setHistory(r.data.history);
    } catch (e: any) { toast.error("Chat failed"); }
    finally { setBusy(false); }
  }

  async function feedback(rating: number, target_id: string) {
    await api.post("/api/feedback", { target: "answer", target_id, rating });
    toast.success("Thanks!");
  }

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">Ask AI about your contracts</h1>
      <div className="card p-3 flex gap-2 items-center">
        <span className="text-sm">Scope:</span>
        <select className="input" value={contract} onChange={e => setContract(e.target.value)}>
          <option value="">All indexed contracts + policies</option>
          {contracts.map(c => <option key={c.id} value={c.id}>{c.company} — {c.name}</option>)}
        </select>
      </div>
      <div className="card p-4 min-h-[55vh] max-h-[65vh] overflow-y-auto space-y-3">
        {history.length === 0 && <div className="opacity-60 text-sm">Ask about clauses, dates, conflicts, obligations…</div>}
        {history.map((m, i) => (
          <div key={i} className={`text-sm ${m.role === "user" ? "text-right" : ""}`}>
            <div className={`inline-block px-3 py-2 rounded-lg ${m.role === "user" ? "bg-brand-500 text-white" : "border"}`}>
              {m.content}
            </div>
            {m.role === "assistant" && (
              <div className="mt-1 flex gap-1 text-xs opacity-60">
                <button onClick={() => feedback(1, `${sessionId}_${i}`)}><ThumbsUp size={12} /></button>
                <button onClick={() => feedback(-1, `${sessionId}_${i}`)}><ThumbsDown size={12} /></button>
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="card p-2 flex gap-2">
        <input className="input" placeholder="Ask a question…" value={input}
               onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} />
        <button className="btn btn-primary" onClick={send} disabled={busy}><Send size={14} /> Send</button>
      </div>
    </div>
  );
}
