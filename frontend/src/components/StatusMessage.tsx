import { AlertCircle, CheckCircle2, Info } from "lucide-react";

interface StatusMessageProps {
  type?: "success" | "error" | "info";
  children: React.ReactNode;
}

export function StatusMessage({ type = "info", children }: StatusMessageProps) {
  const Icon =
    type === "success" ? CheckCircle2 : type === "error" ? AlertCircle : Info;
  return (
    <div
      className={`status-message status-message--${type}`}
      role={type === "error" ? "alert" : "status"}
    >
      <Icon size={20} aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}
