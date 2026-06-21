import React from "react";
import { RefreshControl, SectionList, Text, TouchableOpacity, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";

import { api } from "@/lib/api";
import { qk } from "@/constants/queryKeys";
import { PlatformBadge } from "@/components/PlatformBadge";
import { StatusPill } from "@/components/StatusPill";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import type { CalendarDay, Post } from "@/types/api";
import type { PostsStackParamList } from "@/navigation/PostsStack";

// The Calendar tab navigates into the Queue tab's stack to reuse ReviewScreen
type Nav = NativeStackNavigationProp<PostsStackParamList, "Queue">;

export function CalendarScreen() {
  const nav = useNavigation<Nav>();
  const { data, isLoading, refetch, isRefetching } = useQuery<CalendarDay[]>({
    queryKey: qk.calendar,
    queryFn: () => api.get<CalendarDay[]>("/api/calendar"),
  });

  if (isLoading) return <LoadingSpinner />;

  const sections = (data ?? []).map((d) => ({
    title: d.day,
    data: d.posts,
  }));

  return (
    <SectionList
      sections={sections}
      keyExtractor={(post) => String(post.id)}
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
      ListEmptyComponent={
        <EmptyState
          message="No scheduled posts"
          sub="Approved and scheduled posts appear here."
        />
      }
      renderSectionHeader={({ section: { title } }) => (
        <View className="bg-gray-50 py-2 mb-1 mt-3">
          <Text className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            {title}
          </Text>
        </View>
      )}
      renderItem={({ item: post }) => <CalendarRow post={post} onPress={() => nav.push("Review", { postId: post.id })} />}
    />
  );
}

function CalendarRow({ post, onPress }: { post: Post; onPress: () => void }) {
  const preview = post.body.length > 80 ? post.body.slice(0, 80) + "…" : post.body;
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      className="bg-white rounded-xl border border-gray-100 px-4 py-3 mb-2 shadow-sm"
    >
      <View className="flex-row items-center gap-1.5 mb-1.5 flex-wrap">
        {post.targets.map((t) => (
          <PlatformBadge key={t.id} platform={t.platform} />
        ))}
        <StatusPill status={post.status} />
      </View>
      <Text className="text-sm text-gray-700" numberOfLines={2}>{preview}</Text>
      {post.scheduled_time_display && (
        <Text className="mt-1 text-xs text-indigo-500">{post.scheduled_time_display}</Text>
      )}
    </TouchableOpacity>
  );
}
