import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Navigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { qk } from "@/lib/queryKeys";
import type { User } from "@/lib/types";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: qk.me,
    queryFn: () => api.get<User>("/api/auth/me", { noRedirect: true }),
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }
  if (isError || !data) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
