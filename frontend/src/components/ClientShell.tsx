"use client";
import Navbar from "./Navbar";
import { Toaster } from "react-hot-toast";
import { useTheme } from "@/lib/theme";

export default function ClientShell({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();
  return (
    <div className={theme}>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: "var(--card)", color: "var(--fg)", border: "1px solid var(--border)", borderRadius: "10px", fontSize: "0.875rem" },
          success: { iconTheme: { primary: "#22c55e", secondary: "white" } },
          error: { iconTheme: { primary: "#ef4444", secondary: "white" } },
        }}
      />
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}
