import { create } from "zustand";

interface AuthState {
  token: string | null;
  user: any | null;
  hydrated: boolean;
  hydrate: () => void;
  setSession: (token: string, user: any) => void;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  token: null,
  user: null,
  hydrated: false,
  hydrate: () => {
    if (typeof window === "undefined") return;
    const t = localStorage.getItem("token");
    const u = localStorage.getItem("user");
    set({ token: t, user: u ? JSON.parse(u) : null, hydrated: true });
  },
  setSession: (token, user) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
    set({ token, user });
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    set({ token: null, user: null });
  },
}));
