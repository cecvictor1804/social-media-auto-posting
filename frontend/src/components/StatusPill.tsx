import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Clock, Loader2, PencilLine, Send, XCircle } from "lucide-react";
import type { ComponentType } from "react";

type Variant = "default" | "secondary" | "success" | "warning" | "info" | "danger" | "muted";

const MAP: Record<string, { variant: Variant; Icon: ComponentType<{ className?: string }>; label: string }> = {
  draft: { variant: "muted", Icon: PencilLine, label: "draft" },
  pending_review: { variant: "warning", Icon: PencilLine, label: "pending review" },
  pending: { variant: "muted", Icon: Clock, label: "pending" },
  approved: { variant: "info", Icon: CheckCircle2, label: "approved" },
  scheduled: { variant: "default", Icon: Clock, label: "scheduled" },
  publishing: { variant: "info", Icon: Loader2, label: "publishing" },
  published: { variant: "success", Icon: CheckCircle2, label: "published" },
  failed: { variant: "danger", Icon: XCircle, label: "failed" },
};

export function StatusPill({ status }: { status: string }) {
  const cfg = MAP[status] ?? { variant: "muted" as Variant, Icon: Send, label: status.replace(/_/g, " ") };
  const { variant, Icon, label } = cfg;
  return (
    <Badge variant={variant}>
      <Icon className={status === "publishing" ? "h-3 w-3 animate-spin" : "h-3 w-3"} />
      {label}
    </Badge>
  );
}
