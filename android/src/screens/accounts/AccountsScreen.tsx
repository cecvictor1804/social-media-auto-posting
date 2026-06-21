import React, { useEffect, useState } from "react";
import { RefreshControl, ScrollView, Text, TouchableOpacity, View } from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRoute } from "@react-navigation/native";
import type { RouteProp } from "@react-navigation/native";
import * as WebBrowser from "expo-web-browser";
import Toast from "react-native-toast-message";

import { api } from "@/lib/api";
import { qk } from "@/constants/queryKeys";
import { PLATFORM_LIST } from "@/constants/platforms";
import { ManualAccountSheet } from "@/components/ManualAccountSheet";
import { showConfirm } from "@/components/ConfirmDialog";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { getErrorMessage } from "@/lib/errors";
import type { Account, AccountsResponse, PlatformValue } from "@/types/api";
import type { AppTabsParamList } from "@/navigation/AppTabs";

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://10.0.2.2:8000";

type Route = RouteProp<AppTabsParamList, "Accounts">;

export function AccountsScreen() {
  const route = useRoute<Route>();
  const qc = useQueryClient();
  const [manualPlatform, setManualPlatform] = useState<PlatformValue | null>(null);

  // Handle deep-link from OAuth callback
  useEffect(() => {
    if (route.params?.connected) {
      qc.invalidateQueries({ queryKey: qk.accounts });
      Toast.show({ type: "success", text1: "Account connected" });
    }
    if (route.params?.error) {
      Toast.show({ type: "error", text1: `OAuth error: ${route.params.error}` });
    }
  }, [route.params]);

  const { data, isLoading, refetch, isRefetching } = useQuery<AccountsResponse>({
    queryKey: qk.accounts,
    queryFn: () => api.get<AccountsResponse>("/api/accounts"),
  });

  const disconnect = useMutation({
    mutationFn: (id: number) => api.post(`/api/accounts/${id}/disconnect`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.accounts });
      Toast.show({ type: "success", text1: "Account disconnected" });
    },
    onError: (err) =>
      Toast.show({ type: "error", text1: getErrorMessage(err, "Failed to disconnect") }),
  });

  if (isLoading) return <LoadingSpinner />;

  const accounts = data?.accounts ?? [];
  const configured = data?.configured ?? ({} as Record<PlatformValue, boolean>);

  async function startOAuth(platform: PlatformValue) {
    const url = `${API_URL}/oauth/${platform}/start?mobile=1`;
    const result = await WebBrowser.openAuthSessionAsync(url, "socialposter://oauth/callback");
    if (result.type === "success") {
      qc.invalidateQueries({ queryKey: qk.accounts });
      Toast.show({ type: "success", text1: "Account connected" });
    }
  }

  return (
    <>
      <ScrollView
        className="flex-1 bg-gray-50"
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
      >
        {PLATFORM_LIST.map((cfg) => {
          const platformAccounts = accounts.filter((a) => a.platform === cfg.value && a.is_active);
          return (
            <View
              key={cfg.value}
              className="bg-white rounded-xl border border-gray-100 p-4 mb-4 shadow-sm"
            >
              <View className="flex-row items-center justify-between mb-3">
                <Text
                  className="text-base font-semibold"
                  style={{ color: cfg.color }}
                >
                  {cfg.label}
                </Text>
                <View className="flex-row gap-2">
                  {configured[cfg.value] && (
                    <TouchableOpacity
                      onPress={() => startOAuth(cfg.value)}
                      className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-1.5"
                    >
                      <Text className="text-xs text-blue-600 font-medium">Connect via OAuth</Text>
                    </TouchableOpacity>
                  )}
                  <TouchableOpacity
                    onPress={() => setManualPlatform(cfg.value)}
                    className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5"
                  >
                    <Text className="text-xs text-gray-600 font-medium">Add manually</Text>
                  </TouchableOpacity>
                </View>
              </View>

              {platformAccounts.length === 0 ? (
                <Text className="text-sm text-gray-400 italic">No accounts connected</Text>
              ) : (
                platformAccounts.map((acc) => (
                  <AccountRow
                    key={acc.id}
                    account={acc}
                    onDisconnect={() =>
                      showConfirm({
                        title: "Disconnect account?",
                        message: acc.display_name,
                        confirmLabel: "Disconnect",
                        onConfirm: () => disconnect.mutate(acc.id),
                      })
                    }
                  />
                ))
              )}
            </View>
          );
        })}
      </ScrollView>

      {manualPlatform && (
        <ManualAccountSheet
          platform={manualPlatform}
          onClose={() => setManualPlatform(null)}
        />
      )}
    </>
  );
}

function AccountRow({ account, onDisconnect }: { account: Account; onDisconnect: () => void }) {
  return (
    <View className="flex-row items-center justify-between py-2 border-t border-gray-50">
      <View>
        <Text className="text-sm font-medium text-gray-800">{account.display_name}</Text>
        {account.token_expires_display && (
          <Text className="text-xs text-gray-400 mt-0.5">
            Expires: {account.token_expires_display}
          </Text>
        )}
      </View>
      <TouchableOpacity onPress={onDisconnect}>
        <Text className="text-xs text-red-500 font-medium">Disconnect</Text>
      </TouchableOpacity>
    </View>
  );
}
