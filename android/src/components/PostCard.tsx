import React from "react";
import { Text, TouchableOpacity, View } from "react-native";
import { PlatformBadge } from "./PlatformBadge";
import { StatusPill } from "./StatusPill";
import type { Post } from "@/types/api";

interface Props {
  post: Post;
  onPress?: () => void;
}

export function PostCard({ post, onPress }: Props) {
  const preview = post.body.length > 120 ? post.body.slice(0, 120) + "…" : post.body;
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      className="bg-white rounded-xl border border-gray-100 p-4 mb-3 shadow-sm"
    >
      <View className="flex-row items-center flex-wrap gap-1 mb-2">
        {post.targets.map((t) => (
          <PlatformBadge key={t.id} platform={t.platform} />
        ))}
        <StatusPill status={post.status} />
      </View>
      <Text className="text-sm text-gray-800 leading-5" numberOfLines={3}>
        {preview}
      </Text>
      {post.media.length > 0 && (
        <Text className="mt-1.5 text-xs text-gray-400">
          {post.media.length} media file{post.media.length !== 1 ? "s" : ""}
        </Text>
      )}
      {post.scheduled_time_display ? (
        <Text className="mt-1 text-xs text-indigo-500">{post.scheduled_time_display}</Text>
      ) : null}
    </TouchableOpacity>
  );
}
