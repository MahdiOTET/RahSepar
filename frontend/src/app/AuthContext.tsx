import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";

import {
  api,
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "../lib/api";
import type { CurrentUser, TokenResponse } from "../types/api";

interface AuthContextValue {
  user: CurrentUser | null;
  loading: boolean;
  isOperator: boolean;
  login: (mobile: string, password: string) => Promise<CurrentUser>;
  logout: () => void;
  refreshUser: () => Promise<CurrentUser | null>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async (): Promise<CurrentUser | null> => {
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return null;
    }

    try {
      const currentUser = await api.get<CurrentUser>("/users/me", true);
      setUser(currentUser);
      return currentUser;
    } catch (error) {
      clearAccessToken();
      setUser(null);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshUser().catch(() => undefined);
  }, [refreshUser]);

  const login = useCallback(
    async (mobile: string, password: string): Promise<CurrentUser> => {
      const token = await api.post<TokenResponse>("/auth/login", {
        mobile,
        password,
      });
      setAccessToken(token.access_token);
      const currentUser = await refreshUser();
      if (!currentUser) {
        throw new Error("ورود به حساب کامل نشد.");
      }
      return currentUser;
    },
    [refreshUser],
  );

  const logout = useCallback(() => {
    clearAccessToken();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isOperator: Boolean(user?.profiles.includes("operator")),
      login,
      logout,
      refreshUser,
    }),
    [user, loading, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
