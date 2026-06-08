import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, Send, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { toastError } from "@/lib/errors";
import { qk } from "@/lib/queryKeys";
import type { Account, AccountsResponse, DraftItem, Meta } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { PlatformIcon } from "@/components/PlatformBadge";
import { MediaUploader } from "@/components/MediaUploader";
import type { Media } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { Link } from "react-router-dom";

function StepBadge({ n }: { n: number }) {
  return (
    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
      {n}
    </span>
  );
}

export default function Compose() {
  const navigate = useNavigate();
  const meta = useQuery({ queryKey: qk.meta, queryFn: () => api.get<Meta>("/api/meta") });
  const accountsQ = useQuery({
    queryKey: qk.accounts,
    queryFn: () => api.get<AccountsResponse>("/api/accounts"),
  });

  const accounts = accountsQ.data?.accounts ?? [];
  const models = meta.data?.models ?? [];
  const tones = meta.data?.tones ?? [];

  const [brief, setBrief] = useState("");
  const [tone, setTone] = useState("professional");
  const [model, setModel] = useState("");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [drafts, setDrafts] = useState<DraftItem[]>([]);
  const [usedAi, setUsedAi] = useState(false);
  const [aiModel, setAiModel] = useState<string | null>(null);
  const [scheduledTime, setScheduledTime] = useState("");

  const activeModel = model || meta.data?.default_model || (models[0]?.id ?? "");
  const tone2 = tone || tones[0] || "professional";

  const limitFor = useMemo(() => {
    const map = new Map<string, number>();
    meta.data?.platforms.forEach((p) => map.set(p.value, p.char_limit));
    return (platform: string) => map.get(platform) ?? 1000;
  }, [meta.data]);

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  // Editors follow the selection: pick an account → its draft card (text box +
  // media uploader) appears immediately, preserving anything already typed or
  // attached. Deselecting removes its card.
  useEffect(() => {
    setDrafts((prev) => {
      const byId = new Map(prev.map((d) => [d.account_id, d]));
      return accounts
        .filter((a) => selected.has(a.id))
        .map((a) => {
          const existing = byId.get(a.id);
          if (existing) {
            return { ...existing, platform: a.platform, display_name: a.display_name, limit: limitFor(a.platform) };
          }
          return {
            account_id: a.id,
            platform: a.platform,
            display_name: a.display_name,
            body: "",
            limit: limitFor(a.platform),
            media: [],
          };
        });
    });
  }, [selected, accounts, limitFor]);

  const aiMutation = useMutation({
    mutationFn: () =>
      api.post<DraftItem[]>("/api/drafts/ai", {
        brief,
        tone: tone2,
        model: activeModel,
        account_ids: [...selected],
      }),
    onSuccess: (items) => {
      // Merge AI text into the existing draft cards by account; keep attached media.
      setDrafts((prev) =>
        prev.map((d) => {
          const found = items.find((i) => i.account_id === d.account_id);
          return found ? { ...d, body: found.body } : d;
        })
      );
      setUsedAi(true);
      setAiModel(activeModel);
      toast.success("Drafts generated");
    },
    onError: (err) => toastError(err, "Draft failed"),
  });

  function updateDraft(accountId: number, body: string) {
    setDrafts((prev) => prev.map((d) => (d.account_id === accountId ? { ...d, body } : d)));
  }

  function updateDraftMedia(accountId: number, media: Media[]) {
    setDrafts((prev) => prev.map((d) => (d.account_id === accountId ? { ...d, media } : d)));
  }

  const saveMutation = useMutation({
    mutationFn: (action: "review" | "schedule") =>
      api.post("/api/posts", {
        action,
        used_ai: usedAi,
        ai_model: aiModel,
        scheduled_time: scheduledTime || null,
        items: drafts
          .filter((d) => d.body.trim() || d.media.length)
          .map((d) => ({ account_id: d.account_id, body: d.body, media_ids: d.media.map((m) => m.id) })),
      }),
    onSuccess: (_data, action) => {
      toast.success(action === "schedule" ? "Scheduled" : "Saved for review");
      navigate("/queue");
    },
    onError: (err) => toastError(err, "Could not save"),
  });

  const hasContent = drafts.some((d) => d.body.trim() || d.media.length > 0);

  return (
    <>
      <PageHeader title="Compose" subtitle="Draft with AI or write your own, then schedule across platforms." />

      {accountsQ.isSuccess && accounts.length === 0 && (
        <Card className="mb-6 border-amber-300/60 bg-amber-50 dark:bg-amber-950/30">
          <CardContent className="flex items-center gap-3 py-4 text-sm">
            <span className="text-lg">⚠️</span>
            <p>
              No connected accounts yet.{" "}
              <Link to="/accounts" className="font-medium text-primary underline-offset-4 hover:underline">
                Connect an account
              </Link>{" "}
              to start posting.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Step 1 — pick accounts & draft */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <StepBadge n={1} /> Pick accounts &amp; draft
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5">
            <Label>Brief (for AI)</Label>
            <Textarea
              rows={3}
              placeholder="What should the post be about?"
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
            />
          </div>

          <div className="flex flex-wrap gap-4">
            <div className="space-y-1.5">
              <Label>Tone</Label>
              <Select value={tone2} onValueChange={setTone}>
                <SelectTrigger className="w-44 capitalize">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {tones.map((t) => (
                    <SelectItem key={t} value={t} className="capitalize">
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>AI model</Label>
              <Select value={activeModel} onValueChange={setModel} disabled={models.length === 0}>
                <SelectTrigger className="w-60">
                  <SelectValue placeholder={models.length === 0 ? "No AI provider configured" : "Select a model"} />
                </SelectTrigger>
                <SelectContent>
                  {models.map((m) => (
                    <SelectItem key={m.id} value={m.id}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Target accounts</Label>
            <div className="flex flex-wrap gap-2">
              {accounts.map((a: Account) => {
                const on = selected.has(a.id);
                return (
                  <button
                    key={a.id}
                    type="button"
                    onClick={() => toggle(a.id)}
                    className={cn(
                      "inline-flex items-center gap-2 rounded-xl border py-1.5 pl-2 pr-3 text-sm transition-colors",
                      on ? "border-primary bg-primary/10 text-foreground" : "border-border hover:bg-accent"
                    )}
                  >
                    <PlatformIcon platform={a.platform} className="h-6 w-6" />
                    {a.display_name}
                  </button>
                );
              })}
              {accounts.length === 0 && <span className="text-sm text-muted-foreground">No accounts to target.</span>}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button
              onClick={() => aiMutation.mutate()}
              disabled={models.length === 0 || aiMutation.isPending || !brief.trim() || selected.size === 0}
            >
              {aiMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Generate drafts (AI)
            </Button>
            <span className="text-xs text-muted-foreground">
              Optional — selecting an account already opens an editor below where you can write and attach media.
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Step 2 — review & schedule */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <StepBadge n={2} /> Review &amp; schedule
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {drafts.length === 0 && (
            <p className="rounded-lg border border-dashed py-8 text-center text-sm text-muted-foreground">
              Select an account above to start composing — a text box and an “Add media” button appear here.
            </p>
          )}

          {drafts.map((d) => {
            const over = d.body.length > d.limit;
            return (
              <div key={d.account_id} className="rounded-xl border p-3">
                <div className="mb-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <PlatformIcon platform={d.platform} className="h-7 w-7" />
                    <span className="text-sm font-medium">{d.display_name}</span>
                  </div>
                  <span className={cn("text-xs tabular-nums", over ? "font-semibold text-destructive" : "text-muted-foreground")}>
                    {d.body.length} / {d.limit}
                  </span>
                </div>
                <Textarea
                  rows={4}
                  value={d.body}
                  onChange={(e) => updateDraft(d.account_id, e.target.value)}
                  placeholder={`Write the ${d.platform} post…`}
                  className={cn(over && "border-destructive focus-visible:ring-destructive")}
                />
                <div className="mt-2">
                  <MediaUploader
                    platform={d.platform}
                    value={d.media}
                    onChange={(media) => updateDraftMedia(d.account_id, media)}
                  />
                </div>
              </div>
            );
          })}

          {drafts.length > 0 && (
            <div className="flex flex-wrap items-end justify-between gap-4 border-t pt-4">
              <div className="space-y-1.5">
                <Label>Schedule time (optional for review)</Label>
                <Input
                  type="datetime-local"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  className="w-60"
                />
              </div>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => saveMutation.mutate("review")}
                  disabled={!hasContent || saveMutation.isPending}
                >
                  Save for review
                </Button>
                <Button
                  onClick={() => saveMutation.mutate("schedule")}
                  disabled={!hasContent || !scheduledTime || saveMutation.isPending}
                >
                  {saveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  Schedule now
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}
