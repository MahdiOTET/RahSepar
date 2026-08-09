import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

const TOAST_DURATION_MS = 4500;
const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<Toast | null>(null);
  const nextId = useRef(0);

  const showToast = useCallback(
    (message: string, type: ToastType = "success") => {
      nextId.current += 1;
      setToast({ id: nextId.current, message, type });
    },
    [],
  );

  const dismissToast = useCallback(() => setToast(null), []);

  useEffect(() => {
    if (!toast) return;

    const timeout = window.setTimeout(() => {
      setToast((current) => (current?.id === toast.id ? null : current));
    }, TOAST_DURATION_MS);

    return () => window.clearTimeout(timeout);
  }, [toast]);

  const value = useMemo(() => ({ showToast }), [showToast]);
  const Icon =
    toast?.type === "success"
      ? CheckCircle2
      : toast?.type === "error"
        ? AlertCircle
        : Info;

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-viewport">
        {toast && (
          <div
            key={toast.id}
            className={`toast toast--${toast.type}`}
            data-testid="toast"
          >
            <span className="toast__icon" aria-hidden="true">
              <Icon size={21} />
            </span>
            <p
              className="toast__message"
              role={toast.type === "error" ? "alert" : "status"}
              aria-atomic="true"
            >
              {toast.message}
            </p>
            <button
              className="toast__dismiss"
              type="button"
              onClick={dismissToast}
              aria-label="بستن اعلان"
            >
              <X size={18} aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used inside ToastProvider");
  }
  return context;
}
