import React, { useEffect, useRef, useState } from "react";
import { Text, TextInput, TouchableOpacity, View } from "react-native";
import BottomSheet, { BottomSheetScrollView } from "@gorhom/bottom-sheet";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Toast from "react-native-toast-message";

import { api } from "@/lib/api";
import { qk } from "@/constants/queryKeys";
import { getErrorMessage } from "@/lib/errors";
import type { Account, PlatformValue } from "@/types/api";

interface Props {
  platform: PlatformValue;
  onClose: () => void;
}

const EMPTY = {
  display_name: "",
  platform_account_id: "",
  access_token: "",
  refresh_token: "",
  token_expires_at: "",
};

const ID_LABEL: Record<PlatformValue, string> = {
  facebook: "Page ID",
  linkedin: "Author URN",
  threads: "User ID",
};

export function ManualAccountSheet({ platform, onClose }: Props) {
  const ref = useRef<BottomSheet>(null);
  const qc = useQueryClient();
  const [form, setForm] = useState(EMPTY);

  useEffect(() => {
    ref.current?.expand();
  }, []);

  function field(key: keyof typeof EMPTY) {
    return (v: string) => setForm((f) => ({ ...f, [key]: v }));
  }

  const save = useMutation({
    mutationFn: (action: "save" | "verify") =>
      api.post<Account>(`/api/accounts/${platform}/manual`, { ...form, action }),
    onSuccess: (_, action) => {
      qc.invalidateQueries({ queryKey: qk.accounts });
      Toast.show({
        type: "success",
        text1: action === "verify" ? "Account verified & saved" : "Account saved",
      });
      onClose();
    },
    onError: (err) =>
      Toast.show({ type: "error", text1: getErrorMessage(err, "Failed to save account") }),
  });

  return (
    <BottomSheet
      ref={ref}
      index={0}
      snapPoints={["75%", "90%"]}
      enablePanDownToClose
      onClose={onClose}
    >
      <BottomSheetScrollView contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>
        <Text className="text-base font-semibold text-gray-900 mb-4">
          Add {platform} account manually
        </Text>

        <Field label="Display name" value={form.display_name} onChange={field("display_name")} />
        <Field
          label={ID_LABEL[platform]}
          value={form.platform_account_id}
          onChange={field("platform_account_id")}
        />
        <Field
          label="Access token"
          value={form.access_token}
          onChange={field("access_token")}
          multiline
        />
        {platform === "linkedin" && (
          <Field
            label="Refresh token"
            value={form.refresh_token}
            onChange={field("refresh_token")}
          />
        )}
        <Field
          label="Token expires at (ISO 8601, optional)"
          value={form.token_expires_at}
          onChange={field("token_expires_at")}
          placeholder="2025-12-31T00:00:00Z"
        />

        <View className="flex-row gap-3 mt-4">
          <TouchableOpacity
            onPress={() => save.mutate("verify")}
            disabled={save.isPending}
            className="flex-1 bg-blue-600 rounded-xl py-3 items-center"
            style={{ opacity: save.isPending ? 0.6 : 1 }}
          >
            <Text className="text-white font-medium text-sm">Verify & save</Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => save.mutate("save")}
            disabled={save.isPending}
            className="flex-1 bg-gray-100 rounded-xl py-3 items-center"
          >
            <Text className="text-gray-700 font-medium text-sm">Save without checking</Text>
          </TouchableOpacity>
        </View>
      </BottomSheetScrollView>
    </BottomSheet>
  );
}

function Field({
  label,
  value,
  onChange,
  multiline,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  multiline?: boolean;
  placeholder?: string;
}) {
  return (
    <View className="mb-3">
      <Text className="text-sm font-medium text-gray-700 mb-1">{label}</Text>
      <TextInput
        className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-800"
        value={value}
        onChangeText={onChange}
        multiline={multiline}
        textAlignVertical={multiline ? "top" : "center"}
        style={multiline ? { minHeight: 72 } : {}}
        placeholder={placeholder}
        placeholderTextColor="#9ca3af"
        autoCapitalize="none"
        autoCorrect={false}
      />
    </View>
  );
}
