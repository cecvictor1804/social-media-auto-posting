import React from "react";
import { Image, Text, TextInput, TouchableOpacity, View } from "react-native";
import type { DraftItem, Media } from "@/types/api";
import { PlatformBadge } from "./PlatformBadge";

interface Props {
  draft: DraftItem;
  onBodyChange: (body: string) => void;
  onRemoveMedia: (mediaId: number) => void;
}

export function DraftCard({ draft, onBodyChange, onRemoveMedia }: Props) {
  const over = draft.body.length > draft.limit;
  return (
    <View className="bg-white rounded-xl border border-gray-100 p-4 mb-3 shadow-sm">
      <View className="flex-row items-center gap-2 mb-3">
        <PlatformBadge platform={draft.platform} />
        <Text className="text-sm font-medium text-gray-700">{draft.display_name}</Text>
      </View>

      <TextInput
        className="text-sm text-gray-800 border border-gray-200 rounded-lg p-3 min-h-[80px]"
        multiline
        textAlignVertical="top"
        value={draft.body}
        onChangeText={onBodyChange}
        placeholder="Write your post…"
        placeholderTextColor="#9ca3af"
      />

      <Text className={`mt-1 text-xs text-right ${over ? "text-red-500" : "text-gray-400"}`}>
        {draft.body.length} / {draft.limit}
      </Text>

      {draft.media.length > 0 && (
        <View className="flex-row flex-wrap gap-2 mt-2">
          {draft.media.map((m) => (
            <MediaThumb key={m.id} media={m} onRemove={() => onRemoveMedia(m.id)} />
          ))}
        </View>
      )}
    </View>
  );
}

function MediaThumb({ media, onRemove }: { media: Media; onRemove: () => void }) {
  return (
    <View className="relative w-16 h-16 rounded-lg overflow-hidden border border-gray-100">
      {media.kind === "image" ? (
        <Image source={{ uri: media.url }} className="w-full h-full" resizeMode="cover" />
      ) : (
        <View className="w-full h-full bg-gray-100 items-center justify-center">
          <Text className="text-xs text-gray-500">Video</Text>
        </View>
      )}
      <TouchableOpacity
        onPress={onRemove}
        className="absolute top-0 right-0 w-5 h-5 bg-black/50 rounded-bl-lg items-center justify-center"
      >
        <Text className="text-white text-xs">✕</Text>
      </TouchableOpacity>
    </View>
  );
}
