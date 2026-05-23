import { create } from "zustand";

interface ThemeState {
  theme: "light" | "dark";
  hydrated: boolean;
  hydrate: () => void;
  toggle: () => void;
}
export const useTheme = create<ThemeState>((set, get) => ({
  theme: "light",
  hydrated: false,
  hydrate: () => {
    if (typeof window === "undefined") return;
    const t = (localStorage.getItem("theme") as "light" | "dark") || "light";
    document.documentElement.classList.toggle("dark", t === "dark");
    set({ theme: t, hydrated: true });
  },
  toggle: () => {
    const t = get().theme === "light" ? "dark" : "light";
    localStorage.setItem("theme", t);
    document.documentElement.classList.toggle("dark", t === "dark");
    set({ theme: t });
  },
}));
