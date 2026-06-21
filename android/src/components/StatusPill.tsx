import React from "react";
import { Text, View } from "react-native";
import type { PostStatus, TargetStatus } from "@/types/api";

type AnyStatus = PostStatus | TargetStatus;

const STATUS_STYLES: Record<AnyStatus, { bg: string; text: string; label: string }> = {
  draft:          { bg: "#f3f4f6", text: "#6b7280", label: "Draft" },
  pending_review: { bg: "#fef9c3", text: "#854d0e", label: "Pending review" },
  approved:       { bg: "#dbeafe", text: "#1d4ed8", label: "Approved" },
  scheduled:      { bg: "#ede9fe", text: "#6d28d9", label: "Scheduled" },
  publishing:     { bg: "#e0f2fe", text: "#0369a1", label: "Publishing" },
  published:      { bg: "#dcfce7", text: "#15803d", label: "Published" },
  failed:         { bg: "#fee2e2", text: "#b91c1c", label: "Failed" },
  pending:        { bg: "#f3f4f6", text: "#6b7280", label: "Pending" },
};

export function StatusPill({ status }: { status: AnyStatus }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.draft;
  return (
    <View className="rounded-full px-2 py-0.5" style={{ backgroundColor: s.bg }}>
      <Text className="text-xs font-medium" style={{ color: s.text }}>
        {s.label}
      </Text>
    </View>
  );
}
