"use client";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/authStore";
import { useTheme } from "@/lib/theme";
import { LogOut, Moon, Sun, FileText, Shield, RefreshCcw, Upload, MessageSquare, LayoutDashboard } from "lucide-react";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/contracts", label: "Contracts", icon: FileText },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/renewals", label: "Renewals", icon: RefreshCcw },
  { href: "/policies", label: "Policies", icon: Shield },
  { href: "/chat", label: "Ask AI", icon: MessageSquare },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const router = useRouter();
  const pathname = usePathname();
  if (!user) return null;

  return (
    <header className="navbar mx-4 mt-4 px-4 py-2.5 flex items-center justify-between sticky top-4 z-50">
      <div className="flex items-center gap-1">
        <Link href="/dashboard" className="text-base font-bold tracking-tight mr-4 flex items-center gap-2">
          <span className="text-xl">📜</span>
          <span>ContractSense</span>
        </Link>
        <nav className="hidden md:flex items-center">
          {NAV_LINKS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href !== "/dashboard" && pathname?.startsWith(href));
            return (
              <Link key={href} href={href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all font-medium
                  ${active ? "bg-blue-600 text-white shadow-sm" : "opacity-60 hover:opacity-100 hover:bg-black/5 dark:hover:bg-white/10"}`}>
                <Icon size={14} /> {label}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="flex items-center gap-2">
        <button className="btn btn-ghost p-2" onClick={toggle} title="Toggle theme">
          {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
        </button>
        <div className="hidden sm:flex items-center gap-1 text-sm opacity-70 border rounded-lg px-3 py-1.5">
          <span className="w-2 h-2 rounded-full bg-green-400 inline-block"></span>
          <span>{user.name || user.username}</span>
        </div>
        <button className="btn btn-ghost text-xs" onClick={() => { logout(); router.push("/"); }}>
          <LogOut size={14} />
        </button>
      </div>
    </header>
  );
}
