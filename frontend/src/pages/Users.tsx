import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, ShieldCheck, UserPlus, Users as UsersIcon } from "lucide-react";
import { api } from "@/lib/api";
import { toastError } from "@/lib/errors";
import { qk } from "@/lib/queryKeys";
import type { AdminUser, User } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

// ── Add-user dialog ─────────────────────────────────────────────────────────

interface AddUserForm {
  email: string;
  password: string;
  is_admin: boolean;
}

const EMPTY_FORM: AddUserForm = { email: "", password: "", is_admin: false };

function AddUserDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState<AddUserForm>(EMPTY_FORM);

  useEffect(() => {
    if (open) setForm(EMPTY_FORM);
  }, [open]);

  const create = useMutation({
    mutationFn: (data: AddUserForm) => api.post<AdminUser>("/api/users", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.users });
      toast.success("User created");
      onOpenChange(false);
    },
    onError: (err) => toastError(err, "Failed to create user"),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.email.trim() || !form.password) return;
    create.mutate(form);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Add user</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="mt-2 flex flex-col gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="off"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              required
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
              required
            />
          </div>
          <label className="flex cursor-pointer items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-border accent-primary"
              checked={form.is_admin}
              onChange={(e) => setForm((f) => ({ ...f, is_admin: e.target.checked }))}
            />
            Grant admin privileges
          </label>
          <Button type="submit" disabled={create.isPending} className="mt-1">
            {create.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create user
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function Users() {
  const qc = useQueryClient();
  const me = qc.getQueryData<User>(qk.me);
  const [addOpen, setAddOpen] = useState(false);

  const { data: users, isLoading } = useQuery({
    queryKey: qk.users,
    queryFn: () => api.get<AdminUser[]>("/api/users"),
  });

  const toggleAdmin = useMutation({
    mutationFn: ({ id, is_admin }: { id: number; is_admin: boolean }) =>
      api.patch<AdminUser>(`/api/users/${id}`, { is_admin }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.users }),
    onError: (err) => toastError(err, "Failed to update user"),
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      api.patch<AdminUser>(`/api/users/${id}`, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.users }),
    onError: (err) => toastError(err, "Failed to update user"),
  });

  if (!me?.is_admin) {
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-center text-muted-foreground">
        <UsersIcon className="h-10 w-10 opacity-30" />
        <p className="text-sm">You don&apos;t have permission to manage users.</p>
      </div>
    );
  }

  return (
    <>
      <PageHeader
        title="Users"
        subtitle="Manage who can access the dashboard"
        action={
          <Button size="sm" onClick={() => setAddOpen(true)}>
            <UserPlus className="mr-2 h-4 w-4" />
            Add user
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-3 text-left font-medium">Email</th>
                  <th className="px-4 py-3 text-left font-medium">Role</th>
                  <th className="px-4 py-3 text-left font-medium">Status</th>
                  <th className="px-4 py-3 text-left font-medium">Joined</th>
                  <th className="px-4 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {(users ?? []).map((u) => {
                  const isSelf = u.id === me.id;
                  const busy = toggleAdmin.isPending || toggleActive.isPending;
                  return (
                    <tr key={u.id} className="hover:bg-muted/20">
                      <td className="px-4 py-3 font-medium">
                        {u.email}
                        {isSelf && (
                          <span className="ml-2 text-xs text-muted-foreground">(you)</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {u.is_admin ? (
                          <Badge className="gap-1 bg-primary/10 text-primary hover:bg-primary/10">
                            <ShieldCheck className="h-3 w-3" />
                            Admin
                          </Badge>
                        ) : (
                          <Badge variant="secondary">User</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {u.is_active ? (
                          <Badge variant="outline" className="text-green-600 dark:text-green-400">
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="danger">Inactive</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={isSelf || busy}
                            onClick={() =>
                              toggleAdmin.mutate({ id: u.id, is_admin: !u.is_admin })
                            }
                          >
                            {u.is_admin ? "Remove admin" : "Make admin"}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={isSelf || busy}
                            onClick={() =>
                              toggleActive.mutate({ id: u.id, is_active: !u.is_active })
                            }
                          >
                            {u.is_active ? "Deactivate" : "Reactivate"}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      <AddUserDialog open={addOpen} onOpenChange={setAddOpen} />
    </>
  );
}
