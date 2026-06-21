// Synced from frontend/src/lib/queryKeys.ts
import type { QueryClient } from "@tanstack/react-query";

export const qk = {
  me: ["me"] as const,
  meta: ["meta"] as const,
  accounts: ["accounts"] as const,
  posts: ["posts"] as const,
  post: (id: number | string) => ["post", String(id)] as const,
  calendar: ["calendar"] as const,
  users: ["users"] as const,
};

export function invalidatePostCaches(client: QueryClient) {
  client.invalidateQueries({ queryKey: qk.posts });
  client.invalidateQueries({ queryKey: qk.calendar });
}
