import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { AlertTriangle, Film, ImageIcon, Inbox, Sparkles, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { toastError } from "@/lib/errors";
import { invalidatePostCaches, qk } from "@/lib/queryKeys";
import type { Post } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { PlatformChip } from "@/components/PlatformBadge";
import { StatusPill } from "@/components/StatusPill";
import { EmptyState } from "@/components/EmptyState";
import { LoadingSkeletons } from "@/components/Skeletons";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function Queue() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: qk.posts, queryFn: () => api.get<Post[]>("/api/posts") });
  const [toDelete, setToDelete] = useState<Post | null>(null);

  const del = useMutation({
    mutationFn: (id: number) => api.del(`/api/posts/${id}`),
    onSuccess: () => {
      invalidatePostCaches(qc);
      setToDelete(null);
      toast.success("Post deleted");
    },
    onError: (err) => toastError(err, "Delete failed"),
  });

  const posts = data ?? [];

  return (
    <>
      <PageHeader title="Queue" subtitle="Everything drafted, scheduled, and published." />

      {isLoading && <LoadingSkeletons count={3} />}

      {!isLoading && posts.length === 0 && (
        <EmptyState Icon={Inbox}>
          Nothing here yet.{" "}
          <Link to="/" className="font-medium text-primary underline-offset-4 hover:underline">
            Compose a post
          </Link>
          .
        </EmptyState>
      )}

      <div className="space-y-3">
        {posts.map((post) => (
          <Card key={post.id} className="fade-in">
            <CardContent className="p-4">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <StatusPill status={post.status} />
                {post.targets.map((t) => (
                  <span key={t.id} className="inline-flex items-center gap-1">
                    <PlatformChip platform={t.platform} name={t.display_name} />
                    <StatusPill status={t.status} />
                    {t.error_message && (
                      <span className="text-destructive" title={t.error_message}>
                        <AlertTriangle className="h-3.5 w-3.5" />
                      </span>
                    )}
                  </span>
                ))}
                <span className="ml-auto text-xs text-muted-foreground">⏱ {post.scheduled_time_display}</span>
              </div>

              <p className="whitespace-pre-wrap text-sm text-foreground/90">
                {post.body.slice(0, 280)}
                {post.body.length > 280 ? "…" : ""}
              </p>

              <div className="mt-3 flex items-center gap-4 text-sm">
                {(post.status === "pending_review" || post.status === "draft") && (
                  <Link to={`/posts/${post.id}`} className="font-medium text-primary underline-offset-4 hover:underline">
                    Review &amp; schedule →
                  </Link>
                )}
                {post.ai_model && (
                  <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                    <Sparkles className="h-3 w-3" /> {post.ai_model}
                  </span>
                )}
                {post.media.length > 0 && (
                  <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                    {post.media.some((m) => m.kind === "video") ? (
                      <Film className="h-3 w-3" />
                    ) : (
                      <ImageIcon className="h-3 w-3" />
                    )}
                    {post.media.length}
                  </span>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  className="ml-auto text-destructive hover:bg-destructive/10 hover:text-destructive"
                  onClick={() => setToDelete(post)}
                >
                  <Trash2 className="h-4 w-4" /> Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={!!toDelete} onOpenChange={(o) => !o && setToDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete this post?</DialogTitle>
            <DialogDescription>This permanently removes the post and its platform targets.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setToDelete(null)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={del.isPending} onClick={() => toDelete && del.mutate(toDelete.id)}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
