import React, { useEffect, useState } from "react";
import {
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigation, useRoute } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import type { RouteProp } from "@react-navigation/native";
import DateTimePicker, { DateTimePickerEvent } from "@react-native-community/datetimepicker";
import Toast from "react-native-toast-message";

import { api } from "@/lib/api";
import { qk, invalidatePostCaches } from "@/constants/queryKeys";
import { PlatformBadge } from "@/components/PlatformBadge";
import { StatusPill } from "@/components/StatusPill";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import type { Post } from "@/types/api";
import type { PostsStackParamList } from "@/navigation/PostsStack";

type Nav = NativeStackNavigationProp<PostsStackParamList, "Review">;
type Route = RouteProp<PostsStackParamList, "Review">;

export function ReviewScreen() {
  const nav = useNavigation<Nav>();
  const { params } = useRoute<Route>();
  const qc = useQueryClient();

  const { data: post, isLoading } = useQuery<Post>({
    queryKey: qk.post(params.postId),
    queryFn: () => api.get<Post>(`/api/posts/${params.postId}`),
  });

  const [body, setBody] = useState("");
  const [scheduledDate, setScheduledDate] = useState<Date | null>(null);
  const [showPicker, setShowPicker] = useState(false);

  useEffect(() => {
    if (post) {
      setBody(post.body);
      if (post.scheduled_time) setScheduledDate(new Date(post.scheduled_time));
    }
  }, [post]);

  const approve = useMutation({
    mutationFn: () =>
      api.post(`/api/posts/${params.postId}/approve`, {
        body,
        scheduled_time: scheduledDate?.toISOString() ?? null,
      }),
    onSuccess: () => {
      invalidatePostCaches(qc);
      qc.invalidateQueries({ queryKey: qk.post(params.postId) });
      Toast.show({ type: "success", text1: "Post approved & scheduled" });
      nav.goBack();
    },
    onError: () => Toast.show({ type: "error", text1: "Failed to approve post" }),
  });

  if (isLoading || !post) return <LoadingSpinner />;

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-gray-50"
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
        {/* Status + platforms */}
        <View className="flex-row flex-wrap gap-2 mb-4">
          <StatusPill status={post.status} />
          {post.targets.map((t) => (
            <PlatformBadge key={t.id} platform={t.platform} />
          ))}
        </View>

        {/* Body editor */}
        <Text className="text-sm font-medium text-gray-700 mb-1">Post text</Text>
        <TextInput
          className="bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-800 min-h-[120px]"
          multiline
          textAlignVertical="top"
          value={body}
          onChangeText={setBody}
        />

        {/* Media thumbnails */}
        {post.media.length > 0 && (
          <View className="mt-4">
            <Text className="text-sm font-medium text-gray-700 mb-2">Media</Text>
            <View className="flex-row flex-wrap gap-2">
              {post.media.map((m) => (
                <View
                  key={m.id}
                  className="w-20 h-20 rounded-lg overflow-hidden border border-gray-100"
                >
                  {m.kind === "image" ? (
                    <Image
                      source={{ uri: m.url }}
                      className="w-full h-full"
                      resizeMode="cover"
                    />
                  ) : (
                    <View className="w-full h-full bg-gray-100 items-center justify-center">
                      <Text className="text-xs text-gray-500">Video</Text>
                    </View>
                  )}
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Schedule picker */}
        <Text className="text-sm font-medium text-gray-700 mt-4 mb-1">Schedule time</Text>
        <TouchableOpacity
          onPress={() => setShowPicker(true)}
          className="bg-white border border-gray-200 rounded-xl px-4 py-3"
        >
          <Text className="text-sm text-gray-800">
            {scheduledDate ? scheduledDate.toLocaleString() : "Pick a date & time…"}
          </Text>
        </TouchableOpacity>

        {showPicker && (
          <DateTimePicker
            value={scheduledDate ?? new Date()}
            mode="datetime"
            minimumDate={new Date()}
            onChange={(event: DateTimePickerEvent, date?: Date) => {
              setShowPicker(Platform.OS === "ios");
              if (event.type === "set" && date) setScheduledDate(date);
            }}
          />
        )}

        {/* Approve button */}
        <TouchableOpacity
          onPress={() => approve.mutate()}
          disabled={approve.isPending || !scheduledDate}
          className="mt-6 bg-blue-600 rounded-xl py-3.5 items-center"
          style={{ opacity: approve.isPending || !scheduledDate ? 0.5 : 1 }}
        >
          <Text className="text-white font-semibold">
            {approve.isPending ? "Approving…" : "Approve & schedule"}
          </Text>
        </TouchableOpacity>
        {!scheduledDate && (
          <Text className="text-xs text-gray-400 text-center mt-1">
            Pick a scheduled time to approve
          </Text>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
