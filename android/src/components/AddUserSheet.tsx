import React, { useEffect, useRef, useState } from "react";
import { Switch, Text, TextInput, TouchableOpacity, View } from "react-native";
import BottomSheet, { BottomSheetScrollView } from "@gorhom/bottom-sheet";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Toast from "react-native-toast-message";

import { api } from "@/lib/api";
import { qk } from "@/constants/queryKeys";
import { getErrorMessage } from "@/lib/errors";
import type { AdminUser } from "@/types/api";

interface Props {
  onClose: () => void;
}

export function AddUserSheet({ onClose }: Props) {
  const ref = useRef<BottomSheet>(null);
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    ref.current?.expand();
  }, []);

  const create = useMutation({
    mutationFn: () =>
      api.post<AdminUser>("/api/users", { email: email.trim(), password, is_admin: isAdmin }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.users });
      Toast.show({ type: "success", text1: "User created" });
      onClose();
    },
    onError: (err) =>
      Toast.show({ type: "error", text1: getErrorMessage(err, "Failed to create user") }),
  });

  return (
    <BottomSheet
      ref={ref}
      index={0}
      snapPoints={["60%"]}
      enablePanDownToClose
      onClose={onClose}
    >
      <BottomSheetScrollView contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>
        <Text className="text-base font-semibold text-gray-900 mb-4">Add user</Text>

        <Text className="text-sm font-medium text-gray-700 mb-1">Email</Text>
        <TextInput
          className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-800 mb-3"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
          placeholder="user@example.com"
          placeholderTextColor="#9ca3af"
        />

        <Text className="text-sm font-medium text-gray-700 mb-1">Password</Text>
        <TextInput
          className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-800 mb-4"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          placeholder="••••••••"
          placeholderTextColor="#9ca3af"
        />

        <View className="flex-row items-center justify-between mb-4">
          <Text className="text-sm text-gray-700">Grant admin privileges</Text>
          <Switch value={isAdmin} onValueChange={setIsAdmin} />
        </View>

        <TouchableOpacity
          onPress={() => create.mutate()}
          disabled={create.isPending || !email.trim() || !password}
          className="bg-blue-600 rounded-xl py-3 items-center"
          style={{ opacity: create.isPending || !email.trim() || !password ? 0.5 : 1 }}
        >
          <Text className="text-white font-semibold">
            {create.isPending ? "Creating…" : "Create user"}
          </Text>
        </TouchableOpacity>
      </BottomSheetScrollView>
    </BottomSheet>
  );
}
