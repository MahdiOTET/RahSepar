import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "../app/AuthContext";
import { LoadingState } from "./LoadingState";

interface ProtectedRouteProps {
  children: ReactNode;
  operator?: boolean;
}

export function ProtectedRoute({
  children,
  operator = false,
}: ProtectedRouteProps) {
  const { user, loading, isOperator } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingState label="در حال بررسی حساب…" />;
  }
  if (!user) {
    return (
      <Navigate
        to={`/login?returnTo=${encodeURIComponent(location.pathname)}`}
        replace
      />
    );
  }
  if (operator && !isOperator) {
    return <Navigate to="/" replace />;
  }
  return children;
}
