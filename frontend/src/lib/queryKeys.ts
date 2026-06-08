import type { QueryClient } from "@tanstack/react-query";

// Single source of truth for React Query cache keys (avoids typo'd magic strings
// and makes invalidation consistent).
export const qk = {
  me: ["me"] as const,
  meta: ["meta"] as const,
  accounts: ["accounts"] as const,
  posts: ["posts"] as const,
  post: (id: string | number) => ["post", String(id)] as const,
  calendar: ["calendar"] as const,
};

/** Invalidate everything that a post mutation can affect (queue + calendar). */
export function invalidatePostCaches(client: QueryClient) {
  return Promise.all([
    client.invalidateQueries({ queryKey: qk.posts }),
    client.invalidateQueries({ queryKey: qk.calendar }),
  ]);
}
