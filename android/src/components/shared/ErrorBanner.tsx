import React from "react";
import { Text, View } from "react-native";
import { getErrorMessage } from "@/lib/errors";

export function ErrorBanner({ error, fallback = "Something went wrong" }: { error: unknown; fallback?: string }) {
  return (
    <View className="mx-4 mt-3 rounded-lg bg-red-50 border border-red-200 px-4 py-3">
      <Text className="text-sm text-red-700">{getErrorMessage(error, fallback)}</Text>
    </View>
  );
}
