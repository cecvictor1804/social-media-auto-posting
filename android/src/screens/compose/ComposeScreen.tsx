import React, { useState } from "react";
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigation } from "@react-navigation/native";
import type { BottomTabNavigationProp } from "@react-navigation/bottom-tabs";
import DateTimePicker, { DateTimePickerEvent } from "@react-native-community/datetimepicker";
import Toast from "react-native-toast-message";

import { api } from "@/lib/api";
import { qk, invalidatePostCaches } from "@/constants/queryKeys";
import { DraftCard } from "@/components/DraftCard";
import { MediaUploader } from "@/components/MediaUploader";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { getErrorMessage } from "@/lib/errors";
import type { Account, AccountsResponse, DraftItem, Media, Meta, PlatformValue } from "@/types/api";
import type { AppTabsParamList } from "@/navigation/AppTabs";

type Nav = BottomTabNavigationProp<AppTabsParamList>;

function makeBlankDraft(acc: Account): DraftItem {
  return { account_id: acc.id, platform: acc.platform, display_name: acc.display_name, body: "", limit: 63206, media: [] };
}

export function ComposeScreen() {
  const nav = useNavigation<Nav>();
  const qc = useQueryClient();

  const { data: meta, isLoading: metaLoading } = useQuery<Meta>({
    queryKey: qk.meta,
    queryFn: () => api.get<Meta>("/api/meta"),
  });
  const { data: accountsData, isLoading: accountsLoading } = useQuery<AccountsResponse>({
    queryKey: qk.accounts,
    queryFn: () => api.get<AccountsResponse>("/api/accounts"),
  });

  const [brief, setBrief] = useState("");
  const [tone, setTone] = useState("");
  const [model, setModel] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [drafts, setDrafts] = useState<Map<number, DraftItem>>(new Map());
  const [scheduledDate, setScheduledDate] = useState<Date | null>(null);
  const [scheduleNow, setScheduleNow] = useState(false);
  const [showPicker, setShowPicker] = useState(false);

  const accounts = (accountsData?.accounts ?? []).filter((a) => a.is_active);

  // Sync model/tone from meta
  React.useEffect(() => {
    if (meta && !model) setModel(meta.default_model);
    if (meta && !tone && meta.tones.length) setTone(meta.tones[0]);
  }, [meta]);

  function toggleAccount(acc: Account) {
    const next = new Set(selectedIds);
    if (next.has(acc.id)) {
      next.delete(acc.id);
    } else {
      next.add(acc.id);
      if (!drafts.has(acc.id)) {
        setDrafts((d) => new Map(d).set(acc.id, makeBlankDraft(acc)));
      }
    }
    setSelectedIds(next);
  }

  const aiDraft = useMutation({
    mutationFn: () =>
      api.post<DraftItem[]>("/api/drafts/ai", {
        brief,
        tone,
        model,
        account_ids: Array.from(selectedIds),
      }),
    onSuccess: (items) => {
      setDrafts((prev) => {
        const next = new Map(prev);
        items.forEach((d) => next.set(d.account_id, { ...d, media: prev.get(d.account_id)?.media ?? [] }));
        return next;
      });
    },
    onError: (err) =>
      Alert.alert("AI draft failed", getErrorMessage(err, "Could not generate drafts")),
  });

  const publish = useMutation({
    mutationFn: (action: "review" | "schedule") =>
      api.post("/api/posts", {
        action,
        used_ai: aiDraft.isSuccess,
        ai_model: model,
        scheduled_time: scheduledDate?.toISOString() ?? null,
        items: Array.from(selectedIds).map((id) => {
          const d = drafts.get(id)!;
          return {
            account_id: id,
            body: d.body,
            media_ids: d.media.map((m) => m.id),
          };
        }),
      }),
    onSuccess: () => {
      invalidatePostCaches(qc);
      Toast.show({ type: "success", text1: "Post saved" });
      // Reset form
      setBrief("");
      setSelectedIds(new Set());
      setDrafts(new Map());
      setScheduledDate(null);
      nav.navigate("QueueStack");
    },
    onError: (err) =>
      Alert.alert("Failed to save", getErrorMessage(err, "Could not save posts")),
  });

  if (metaLoading || accountsLoading) return <LoadingSpinner />;
  if (accounts.length === 0) {
    return (
      <EmptyState
        message="No connected accounts"
        sub="Connect a social account from the Accounts tab first."
      />
    );
  }

  const selectedDrafts = Array.from(selectedIds)
    .map((id) => drafts.get(id))
    .filter(Boolean) as DraftItem[];

  const canPublish = selectedIds.size > 0 && selectedDrafts.every((d) => d.body.trim().length > 0);
  const canSchedule = canPublish && !!scheduledDate;

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-gray-50"
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 48 }}>
        {/* Account selector */}
        <Text className="text-sm font-semibold text-gray-700 mb-2">Select accounts</Text>
        <View className="flex-row flex-wrap gap-2 mb-4">
          {accounts.map((acc) => {
            const sel = selectedIds.has(acc.id);
            return (
              <TouchableOpacity
                key={acc.id}
                onPress={() => toggleAccount(acc)}
                className={`rounded-full border px-3 py-1.5 ${sel ? "bg-blue-600 border-blue-600" : "bg-white border-gray-200"}`}
              >
                <Text className={`text-xs font-medium ${sel ? "text-white" : "text-gray-700"}`}>
                  {acc.display_name}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Brief + AI section */}
        <Text className="text-sm font-semibold text-gray-700 mb-2">AI draft</Text>
        <TextInput
          className="bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-800 min-h-[60px] mb-2"
          multiline
          textAlignVertical="top"
          value={brief}
          onChangeText={setBrief}
          placeholder="Describe what you want to post…"
          placeholderTextColor="#9ca3af"
        />

        {/* Tone & model pickers */}
        {meta && (
          <View className="flex-row gap-3 mb-3">
            <View className="flex-1">
              <Text className="text-xs text-gray-500 mb-1">Tone</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                {meta.tones.map((t) => (
                  <TouchableOpacity
                    key={t}
                    onPress={() => setTone(t)}
                    className={`mr-2 rounded-lg border px-3 py-1.5 ${tone === t ? "bg-blue-50 border-blue-300" : "bg-white border-gray-200"}`}
                  >
                    <Text className={`text-xs ${tone === t ? "text-blue-600" : "text-gray-600"}`}>
                      {t}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          </View>
        )}

        <TouchableOpacity
          onPress={() => aiDraft.mutate()}
          disabled={aiDraft.isPending || !brief.trim() || selectedIds.size === 0}
          className="bg-indigo-600 rounded-xl py-3 items-center mb-4"
          style={{ opacity: aiDraft.isPending || !brief.trim() || selectedIds.size === 0 ? 0.5 : 1 }}
        >
          <Text className="text-white font-medium text-sm">
            {aiDraft.isPending ? "Generating…" : "Generate AI drafts"}
          </Text>
        </TouchableOpacity>

        {/* Draft cards */}
        {selectedDrafts.length > 0 && (
          <>
            <Text className="text-sm font-semibold text-gray-700 mb-2">Edit drafts</Text>
            {selectedDrafts.map((d) => (
              <View key={d.account_id}>
                <DraftCard
                  draft={d}
                  onBodyChange={(body) =>
                    setDrafts((prev) => new Map(prev).set(d.account_id, { ...d, body }))
                  }
                  onRemoveMedia={(mediaId) =>
                    setDrafts((prev) =>
                      new Map(prev).set(d.account_id, {
                        ...d,
                        media: d.media.filter((m) => m.id !== mediaId),
                      })
                    )
                  }
                />
                <View className="mb-3 -mt-2">
                  <MediaUploader
                    onUploaded={(media: Media) =>
                      setDrafts((prev) =>
                        new Map(prev).set(d.account_id, {
                          ...d,
                          media: [...d.media, media],
                        })
                      )
                    }
                  />
                </View>
              </View>
            ))}
          </>
        )}

        {/* Schedule */}
        {selectedDrafts.length > 0 && (
          <>
            <View className="flex-row items-center justify-between mb-3">
              <Text className="text-sm font-semibold text-gray-700">Schedule</Text>
              <View className="flex-row items-center gap-2">
                <Text className="text-xs text-gray-500">Set time</Text>
                <Switch value={scheduleNow} onValueChange={setScheduleNow} />
              </View>
            </View>

            {scheduleNow && (
              <>
                <TouchableOpacity
                  onPress={() => setShowPicker(true)}
                  className="bg-white border border-gray-200 rounded-xl px-4 py-3 mb-3"
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
              </>
            )}

            {/* Action buttons */}
            <View className="flex-row gap-3 mt-2">
              <TouchableOpacity
                onPress={() => publish.mutate("review")}
                disabled={publish.isPending || !canPublish}
                className="flex-1 border border-blue-600 rounded-xl py-3 items-center"
                style={{ opacity: publish.isPending || !canPublish ? 0.5 : 1 }}
              >
                <Text className="text-blue-600 font-medium text-sm">Save for review</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => publish.mutate("schedule")}
                disabled={publish.isPending || !canSchedule}
                className="flex-1 bg-blue-600 rounded-xl py-3 items-center"
                style={{ opacity: publish.isPending || !canSchedule ? 0.5 : 1 }}
              >
                <Text className="text-white font-medium text-sm">Schedule now</Text>
              </TouchableOpacity>
            </View>
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
