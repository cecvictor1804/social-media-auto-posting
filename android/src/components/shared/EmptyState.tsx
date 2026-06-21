import React from "react";
import { Text, View } from "react-native";

interface Props {
  message: string;
  sub?: string;
}

export function EmptyState({ message, sub }: Props) {
  return (
    <View className="flex-1 items-center justify-center py-20 px-8">
      <Text className="text-base font-medium text-gray-500 text-center">{message}</Text>
      {sub ? <Text className="mt-1 text-sm text-gray-400 text-center">{sub}</Text> : null}
    </View>
  );
}
