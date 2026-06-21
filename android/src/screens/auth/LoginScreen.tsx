import React, { useState } from "react";
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";

import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { getErrorMessage } from "@/lib/errors";
import { qk } from "@/constants/queryKeys";
import type { User } from "@/types/api";
import type { RootStackParamList } from "@/navigation/RootNavigator";

interface TokenOut {
  access_token: string;
  token_type: string;
  user: User;
}

type Nav = NativeStackNavigationProp<RootStackParamList, "Login">;

export function LoginScreen() {
  const nav = useNavigation<Nav>();
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const login = useMutation({
    mutationFn: () =>
      api.post<TokenOut>("/api/auth/token", { email: email.trim(), password }),
    onSuccess: async (data) => {
      await setToken(data.access_token);
      qc.setQueryData(qk.me, data.user);
      nav.replace("App");
    },
    onError: (err) => {
      Alert.alert("Login failed", getErrorMessage(err, "Incorrect email or password"));
    },
  });

  function submit() {
    if (!email.trim() || !password) return;
    login.mutate();
  }

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-gray-50"
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        contentContainerStyle={{ flexGrow: 1 }}
        keyboardShouldPersistTaps="handled"
      >
        <View className="flex-1 justify-center px-6 py-12">
          <Text className="text-2xl font-bold text-gray-900 mb-1">Social Poster</Text>
          <Text className="text-sm text-gray-500 mb-8">Sign in to your account</Text>

          <View className="gap-4">
            <View>
              <Text className="text-sm font-medium text-gray-700 mb-1">Email</Text>
              <TextInput
                className="bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900"
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                autoComplete="email"
                value={email}
                onChangeText={setEmail}
                placeholder="you@example.com"
                placeholderTextColor="#9ca3af"
              />
            </View>

            <View>
              <Text className="text-sm font-medium text-gray-700 mb-1">Password</Text>
              <TextInput
                className="bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900"
                secureTextEntry
                autoComplete="password"
                value={password}
                onChangeText={setPassword}
                placeholder="••••••••"
                placeholderTextColor="#9ca3af"
                onSubmitEditing={submit}
                returnKeyType="go"
              />
            </View>

            <TouchableOpacity
              onPress={submit}
              disabled={login.isPending}
              className="bg-blue-600 rounded-xl py-3.5 items-center mt-2"
              style={{ opacity: login.isPending ? 0.6 : 1 }}
            >
              <Text className="text-white font-semibold text-sm">
                {login.isPending ? "Signing in…" : "Sign in"}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
