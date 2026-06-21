import React from "react";
import { ActivityIndicator, View } from "react-native";

export function LoadingSpinner({ size = "large" }: { size?: "small" | "large" }) {
  return (
    <View className="flex-1 items-center justify-center py-16">
      <ActivityIndicator size={size} color="#2563eb" />
    </View>
  );
}
