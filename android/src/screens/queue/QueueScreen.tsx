import React from "react";
import { FlatList, RefreshControl, Text, TouchableOpacity, View } from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import Toast from "react-native-toast-message";

import { api } from "@/lib/api";
import { qk, invalidatePostCaches } from "@/constants/queryKeys";
import { PostCard } from "@/components/PostCard";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { showConfirm } from "@/components/ConfirmDialog";
import type { Post } from "@/types/api";
import type { PostsStackParamList } from "@/navigation/PostsStack";

type Nav = NativeStackNavigationProp<PostsStackParamList, "Queue">;

const REVIEWABLE: Post["status"][] = ["draft", "pending_review", "approved"];

export function QueueScreen() {
  const nav = useNavigation<Nav>();
  const qc = useQueryClient();

  const { data: posts, isLoading, refetch, isRefetching } = useQuery<Post[]>({
    queryKey: qk.posts,
    queryFn: () => api.get<Post[]>("/api/posts"),
  });

  const del = useMutation({
    mutationFn: (id: number) => api.del(`/api/posts/${id}`),
    onSuccess: () => {
      invalidatePostCaches(qc);
      Toast.show({ type: "success", text1: "Post deleted" });
    },
    onError: () => Toast.show({ type: "error", text1: "Failed to delete post" }),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <FlatList
      data={posts ?? []}
      keyExtractor={(p) => String(p.id)}
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
      ListEmptyComponent={
        <EmptyState message="No posts yet" sub="Compose your first post from the Compose tab." />
      }
      renderItem={({ item: post }) => (
        <View>
          <PostCard
            post={post}
            onPress={
              REVIEWABLE.includes(post.status)
                ? () => nav.push("Review", { postId: post.id })
                : undefined
            }
          />
          <TouchableOpacity
            onPress={() =>
              showConfirm({
                title: "Delete post?",
                message: "This cannot be undone.",
                confirmLabel: "Delete",
                onConfirm: () => del.mutate(post.id),
              })
            }
            className="mb-4 -mt-2 items-end pr-1"
          >
            <Text className="text-xs text-gray-400">Delete</Text>
          </TouchableOpacity>
        </View>
      )}
    />
  );
}
