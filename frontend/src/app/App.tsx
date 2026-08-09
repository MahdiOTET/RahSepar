import { lazy, Suspense, useCallback, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./AppShell";
import { AuthProvider } from "./AuthContext";
import { ThemeProvider } from "./ThemeContext";
import { LoadingState } from "../components/LoadingState";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { hasSeenSplash, SplashScreen } from "../components/SplashScreen";

const TripsPage = lazy(() => import("../features/trips/TripsPage"));
const LoginPage = lazy(() => import("../features/auth/LoginPage"));
const BookingsPage = lazy(() => import("../features/bookings/BookingsPage"));
const AccountPage = lazy(() => import("../features/account/AccountPage"));
const ManagementPage = lazy(
  () => import("../features/operator/ManagementPage"),
);

function AppContent() {
  const [showSplash, setShowSplash] = useState(() => !hasSeenSplash());
  const completeSplash = useCallback(() => setShowSplash(false), []);

  if (showSplash) {
    return <SplashScreen onComplete={completeSplash} />;
  }

  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingState />}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<TripsPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route
              path="bookings"
              element={
                <ProtectedRoute>
                  <BookingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="account"
              element={
                <ProtectedRoute>
                  <AccountPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="manage"
              element={
                <ProtectedRoute operator>
                  <ManagementPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}
