import React from "react";
import { Alert, Text, TouchableOpacity, View } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/errors";
import type { Media } from "@/types/api";

interface Props {
  onUploaded: (media: Media) => void;
}

export function MediaUploader({ onUploaded }: Props) {
  const upload = useMutation({
    mutationFn: async () => {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.All,
        allowsMultipleSelection: false,
        quality: 0.85,
      });
      if (result.canceled || result.assets.length === 0) return null;
      const asset = result.assets[0];
      return api.upload<Media>("/api/media", {
        uri: asset.uri,
        name: asset.fileName ?? `upload_${Date.now()}.jpg`,
        type: asset.mimeType ?? "image/jpeg",
      });
    },
    onSuccess: (media) => {
      if (media) onUploaded(media);
    },
    onError: (err) => {
      Alert.alert("Upload failed", getErrorMessage(err, "Could not upload file"));
    },
  });

  return (
    <TouchableOpacity
      onPress={() => upload.mutate()}
      disabled={upload.isPending}
      className="border border-dashed border-gray-300 rounded-lg py-2 px-4 items-center"
    >
      <Text className="text-sm text-gray-500">
        {upload.isPending ? "Uploading…" : "+ Add media"}
      </Text>
    </TouchableOpacity>
  );
}
