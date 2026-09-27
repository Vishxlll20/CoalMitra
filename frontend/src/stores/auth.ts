import { create } from "zustand";
import { api } from "../lib/api";
import type { AuthUser } from "../types";
import { useRoleStore } from "./role";

interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  initialized: boolean;
  initialize: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

let initialization: Promise<void> | null = null;

function setUser(user: AuthUser | null) {
  useRoleStore.getState().setRole(user?.role ?? "GEOLOGIST");
  useAuthStore.setState({ user });
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  loading: true,
  initialized: false,
  initialize: () => {
    if (get().initialized) return Promise.resolve();
    if (!initialization) {
      initialization = api.auth.me()
        .then(setUser)
        .catch(() => setUser(null))
        .finally(() => {
          set({ loading: false, initialized: true });
          initialization = null;
        });
    }
    return initialization;
  },
  login: async (email, password) => {
    set({ loading: true });
    try {
      setUser(await api.auth.login(email, password));
      set({ loading: false, initialized: true });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },
  register: async (name, email, password) => {
    set({ loading: true });
    try {
      setUser(await api.auth.register(name, email, password));
      set({ loading: false, initialized: true });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },
  logout: async () => {
    try {
      await api.auth.logout();
    } finally {
      setUser(null);
      set({ loading: false, initialized: true });
    }
  },
}));