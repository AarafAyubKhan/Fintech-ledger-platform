/**
 * FinSight AI — Auth Store (Zustand)
 * Global authentication state management.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserProfile } from "@/lib/api";

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;

  setAuth: (token: string, refreshToken: string, user: UserProfile) => void;
  setUser: (user: UserProfile) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      setAuth: (token, refreshToken, user) =>
        set({
          token,
          refreshToken,
          user,
          isAuthenticated: true,
        }),

      setUser: (user) => set({ user }),

      logout: () =>
        set({
          token: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "finsight-auth",
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
