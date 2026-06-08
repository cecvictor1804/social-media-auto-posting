import { useEffect, useState, type ChangeEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { CheckCircle2, ExternalLink, KeyRound, Loader2, Plus, Unplug } from "lucide-react";
import { api } from "@/lib/api";
import { toastError } from "@/lib/errors";
import { qk } from "@/lib/queryKeys";
import type { Account, AccountsResponse, ManualAccountForm, PlatformValue } from "@/lib/types";
import { PLATFORMS } from "@/lib/platforms";
import { PageHeader } from "@/components/PageHeader";
import { PlatformIcon } from "@/components/PlatformBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";

const ORDER: PlatformValue[] = ["facebook", "linkedin", "threads"];

// Per-platform wording for the account-id field.
const ID_FIELD: Record<PlatformValue, { label: string; hint: string }> = {
  facebook: { label: "Page ID", hint: "Your Facebook Page's numeric ID" },
  linkedin: { label: "Author URN", hint: "urn:li:person:… or urn:li:organization:…" },
  threads: { label: "Threads user ID", hint: "Your Threads account's numeric ID" },
};

const EMPTY: ManualAccountForm = {
  display_name: "",
  platform_account_id: "",
  access_token: "",
  refresh_token: "",
  token_expires_at: "",
};

function ManualDialog({
  platform,
  open,
  onOpenChange,
}: {
  platform: PlatformValue;
  open: boolean;
  onOpenChange: (o: boolean) => void;
}) {
  const qc = useQueryClient();
  const [form, setForm] = useState<ManualAccountForm>(EMPTY);

  useEffect(() => {
    if (open) setForm(EMPTY);
  }, [open]);

  const save = useMutation({
    mutationFn: (action: "save" | "verify") =>
      api.post<Account>(`/api/accounts/${platform}/manual`, {
        display_name: form.display_name,
        platform_account_id: form.platform_account_id,
        access_token: form.access_token,
        refresh_token: form.refresh_token || null,
        token_expires_at: form.token_expires_at || null,
        action,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.accounts });
      toast.success(`${PLATFORMS[platform].label} account saved`);
      onOpenChange(false);
    },
    onError: (err) => toastError(err, "Could not save account"),
  });

  const set = (k: keyof ManualAccountForm) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <PlatformIcon platform={platform} className="h-7 w-7" />
            Add {PLATFORMS[platform].label} manually
          </DialogTitle>
          <DialogDescription>
            Paste credentials directly. Tokens are encrypted at rest and never shown again.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label>Display name</Label>
            <Input value={form.display_name} onChange={set("display_name")} placeholder="e.g. Acme Brand Page" />
          </div>
          <div className="space-y-1.5">
            <Label>{ID_FIELD[platform].label}</Label>
            <Input
              value={form.platform_account_id}
              onChange={set("platform_account_id")}
              placeholder={ID_FIELD[platform].hint}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Access token</Label>
            <Input value={form.access_token} onChange={set("access_token")} type="password" placeholder="Paste token" />
          </div>
          {platform === "linkedin" && (
            <div className="space-y-1.5">
              <Label>Refresh token (optional)</Label>
              <Input value={form.refresh_token} onChange={set("refresh_token")} type="password" />
            </div>
          )}
          <div className="space-y-1.5">
            <Label>Token expiry (optional)</Label>
            <Input type="date" value={form.token_expires_at} onChange={set("token_expires_at")} className="w-48" />
          </div>
        </div>

        <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="outline" onClick={() => save.mutate("save")} disabled={save.isPending}>
            Save without checking
          </Button>
          <Button onClick={() => save.mutate("verify")} disabled={save.isPending}>
            {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
            Verify &amp; save
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function PlatformCard({
  platform,
  configured,
  accounts,
}: {
  platform: PlatformValue;
  configured: boolean;
  accounts: Account[];
}) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);

  const disconnect = useMutation({
    mutationFn: (id: number) => api.post(`/api/accounts/${id}/disconnect`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.accounts });
      toast.success("Disconnected");
    },
    onError: (err) => toastError(err, "Could not disconnect"),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-3 text-base">
          <PlatformIcon platform={platform} />
          {PLATFORMS[platform].label}
        </CardTitle>
        <div className="flex items-center gap-2">
          {configured ? (
            <Button variant="outline" size="sm" asChild>
              <a href={`/oauth/${platform}/start`}>
                <ExternalLink className="h-4 w-4" /> Connect via OAuth
              </a>
            </Button>
          ) : (
            <Badge variant="muted">OAuth not configured</Badge>
          )}
          <Button size="sm" onClick={() => setOpen(true)}>
            <Plus className="h-4 w-4" /> Add manually
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {accounts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No accounts connected yet.</p>
        ) : (
          <ul className="divide-y">
            {accounts.map((a) => (
              <li key={a.id} className="flex items-center justify-between gap-3 py-2.5">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{a.display_name}</div>
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <KeyRound className="h-3 w-3" />
                    token set
                    {a.token_expires_display ? ` · expires ${a.token_expires_display}` : ""}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                  onClick={() => disconnect.mutate(a.id)}
                  disabled={disconnect.isPending}
                >
                  <Unplug className="h-4 w-4" /> Disconnect
                </Button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
      <ManualDialog platform={platform} open={open} onOpenChange={setOpen} />
    </Card>
  );
}

export default function Accounts() {
  const [params, setParams] = useSearchParams();
  const { data } = useQuery({ queryKey: qk.accounts, queryFn: () => api.get<AccountsResponse>("/api/accounts") });

  // Surface OAuth callback outcomes (?connected=1 / ?error=…).
  useEffect(() => {
    if (params.get("connected")) {
      toast.success("Account connected");
      params.delete("connected");
      setParams(params, { replace: true });
    }
    const err = params.get("error");
    if (err) {
      toast.error(`OAuth: ${err}`);
      params.delete("error");
      setParams(params, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const accounts = data?.accounts ?? [];
  const configured = data?.configured ?? { facebook: false, linkedin: false, threads: false };

  return (
    <>
      <PageHeader title="Accounts" subtitle="Connect platforms via OAuth or by pasting credentials." />
      <div className="space-y-4">
        {ORDER.map((p) => (
          <PlatformCard
            key={p}
            platform={p}
            configured={configured[p]}
            accounts={accounts.filter((a) => a.platform === p)}
          />
        ))}
      </div>
    </>
  );
}
