import React, { useState } from "react";
import { FlatList, RefreshControl, Text, TouchableOpacity, View } from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Toast from "react-native-toast-message";

import { api } from "@/lib/api";
import { qk } from "@/constants/queryKeys";
import { AddUserSheet } from "@/components/AddUserSheet";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { getErrorMessage } from "@/lib/errors";
import type { AdminUser, User } from "@/types/api";
import { useQueryClient as useQC } from "@tanstack/react-query";

export function UsersScreen() {
  const qc = useQueryClient();
  const me = qc.getQueryData<User>(qk.me);
  const [addOpen, setAddOpen] = useState(false);

  const { data: users, isLoading, refetch, isRefetching } = useQuery<AdminUser[]>({
    queryKey: qk.users,
    queryFn: () => api.get<AdminUser[]>("/api/users"),
  });

  const toggleAdmin = useMutation({
    mutationFn: ({ id, is_admin }: { id: number; is_admin: boolean }) =>
      api.patch<AdminUser>(`/api/users/${id}`, { is_admin }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.users }),
    onError: (err) =>
      Toast.show({ type: "error", text1: getErrorMessage(err, "Failed to update user") }),
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      api.patch<AdminUser>(`/api/users/${id}`, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.users }),
    onError: (err) =>
      Toast.show({ type: "error", text1: getErrorMessage(err, "Failed to update user") }),
  });

  if (!me?.is_admin) {
    return <EmptyState message="Admin access required" />;
  }

  if (isLoading) return <LoadingSpinner />;

  return (
    <>
      <FlatList
        data={users ?? []}
        keyExtractor={(u) => String(u.id)}
        contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
        ListHeaderComponent={
          <TouchableOpacity
            onPress={() => setAddOpen(true)}
            className="bg-blue-600 rounded-xl py-3 items-center mb-4"
          >
            <Text className="text-white font-semibold">+ Add user</Text>
          </TouchableOpacity>
        }
        ListEmptyComponent={<EmptyState message="No users found" />}
        renderItem={({ item: u }) => {
          const isSelf = u.id === me.id;
          const busy = toggleAdmin.isPending || toggleActive.isPending;
          return (
            <View className="bg-white rounded-xl border border-gray-100 p-4 mb-3 shadow-sm">
              <View className="flex-row items-center justify-between mb-2">
                <View className="flex-1 mr-2">
                  <Text className="text-sm font-medium text-gray-900" numberOfLines={1}>
                    {u.email}
                    {isSelf ? <Text className="text-gray-400"> (you)</Text> : null}
                  </Text>
                  <Text className="text-xs text-gray-400 mt-0.5">
                    {u.is_admin ? "Admin" : "User"} · {u.is_active ? "Active" : "Inactive"}
                  </Text>
                </View>
              </View>

              {!isSelf && (
                <View className="flex-row gap-2 mt-1">
                  <TouchableOpacity
                    onPress={() => toggleAdmin.mutate({ id: u.id, is_admin: !u.is_admin })}
                    disabled={busy}
                    className="flex-1 border border-gray-200 rounded-lg py-2 items-center"
                    style={{ opacity: busy ? 0.5 : 1 }}
                  >
                    <Text className="text-xs text-gray-600">
                      {u.is_admin ? "Remove admin" : "Make admin"}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => toggleActive.mutate({ id: u.id, is_active: !u.is_active })}
                    disabled={busy}
                    className="flex-1 border border-gray-200 rounded-lg py-2 items-center"
                    style={{ opacity: busy ? 0.5 : 1 }}
                  >
                    <Text className="text-xs text-gray-600">
                      {u.is_active ? "Deactivate" : "Reactivate"}
                    </Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          );
        }}
      />
      {addOpen && <AddUserSheet onClose={() => setAddOpen(false)} />}
    </>
  );
}
