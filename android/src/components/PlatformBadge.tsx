import React from "react";
import { Text, View } from "react-native";
import { PLATFORMS } from "@/constants/platforms";
import type { PlatformValue } from "@/types/api";

export function PlatformBadge({ platform }: { platform: PlatformValue }) {
  const cfg = PLATFORMS[platform];
  return (
    <View
      className="rounded-full px-2 py-0.5 mr-1"
      style={{ backgroundColor: cfg.color + "20" }}
    >
      <Text className="text-xs font-medium" style={{ color: cfg.color }}>
        {cfg.label}
      </Text>
    </View>
  );
}
