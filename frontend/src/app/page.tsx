"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authStore";
import toast from "react-hot-toast";

export default function LoginPage() {
  const router = useRouter();
  const { setSession, token, hydrated } = useAuth();
  const [u, setU] = useState("dev@example.ai");
  const [p, setP] = useState("developer123");
  const [loading, setLoading] = useState(false);

  useEffect(() => { if (hydrated && token) router.replace("/dashboard"); }, [hydrated, token, router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post("/api/auth/login", { username: u, password: p });
      setSession(res.data.access_token, res.data.user);
      toast.success("Welcome!");
      router.push("/dashboard");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Login failed");
    } finally { setLoading(false); }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <form onSubmit={submit} className="card p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold">📜 ContractSense</h1>
        <p className="text-sm opacity-70 mt-1">AI contract review for IT maintenance teams</p>
        <div className="mt-6 space-y-3">
          <input className="input" placeholder="Email or username" value={u} onChange={e => setU(e.target.value)} />
          <input className="input" type="password" placeholder="Password" value={p} onChange={e => setP(e.target.value)} />
          <button className="btn btn-primary w-full justify-center" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </div>
        <div className="mt-4 text-xs opacity-70">
          <div><b>Demo:</b> dev@example.ai / developer123</div>
          <div>legal@example.ai / legal123</div>
        </div>
      </form>
    </div>
  );
}
