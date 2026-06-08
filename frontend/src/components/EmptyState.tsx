import type { ComponentType, ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";

export function EmptyState({
  Icon,
  children,
  action,
}: {
  Icon?: ComponentType<{ className?: string }>;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-2 py-14 text-center text-muted-foreground">
        {Icon && <Icon className="h-9 w-9" />}
        <div>{children}</div>
        {action}
      </CardContent>
    </Card>
  );
}
