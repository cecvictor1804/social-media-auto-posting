import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ArrowLeft, Loader2, Send, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { toastError } from "@/lib/errors";
import { invalidatePostCaches, qk } from "@/lib/queryKeys";
import type { Post } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { PlatformChip } from "@/components/PlatformBadge";
import { StatusPill } from "@/components/StatusPill";
import { MediaThumbnail } from "@/components/MediaThumbnail";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";

export default function Review() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data: post, isLoading } = useQuery({
    queryKey: qk.post(id ?? ""),
    queryFn: () => api.get<Post>(`/api/posts/${id}`),
  });

  const [body, setBody] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");

  useEffect(() => {
    if (post) setBody(post.body);
  }, [post]);

  const approve = useMutation({
    mutationFn: () => api.post(`/api/posts/${id}/approve`, { body, scheduled_time: scheduledTime }),
    onSuccess: () => {
      invalidatePostCaches(qc);
      toast.success("Approved & scheduled");
      navigate("/queue");
    },
    onError: (err) => toastError(err, "Could not approve"),
  });

  return (
    <>
      <PageHeader
        title="Review & approve"
        subtitle="Edit the content and pick a time. Nothing publishes without your sign-off."
        action={
          <Button variant="ghost" size="sm" asChild>
            <Link to="/queue">
              <ArrowLeft className="h-4 w-4" /> Back to queue
            </Link>
          </Button>
        }
      />

      {isLoading && <Skeleton className="h-72 w-full" />}

      {post && (
        <Card className="fade-in">
          <CardContent className="space-y-5 pt-6">
            <div className="flex flex-wrap items-center gap-2">
              <StatusPill status={post.status} />
              {post.targets.map((t) => (
                <PlatformChip key={t.id} platform={t.platform} name={t.display_name} />
              ))}
              {post.ai_model && (
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                  <Sparkles className="h-3 w-3" /> {post.ai_model}
                </span>
              )}
            </div>

            <div className="space-y-1.5">
              <Label>Content</Label>
              <Textarea rows={8} value={body} onChange={(e) => setBody(e.target.value)} />
            </div>

            {post.media.length > 0 && (
              <div className="space-y-1.5">
                <Label>Attached media</Label>
                <div className="flex flex-wrap gap-2">
                  {post.media.map((m) => (
                    <MediaThumbnail key={m.id} media={m} videoLink />
                  ))}
                </div>
              </div>
            )}

            <div className="flex flex-wrap items-end justify-between gap-4 border-t pt-4">
              <div className="space-y-1.5">
                <Label>Schedule time</Label>
                <Input
                  type="datetime-local"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  className="w-60"
                />
              </div>
              <Button onClick={() => approve.mutate()} disabled={!body.trim() || !scheduledTime || approve.isPending}>
                {approve.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Approve &amp; schedule
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}
