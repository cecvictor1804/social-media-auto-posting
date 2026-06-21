import React from "react";
import { Alert } from "react-native";

interface Options {
  title: string;
  message?: string;
  confirmLabel?: string;
  onConfirm: () => void;
}

export function showConfirm({ title, message, confirmLabel = "Confirm", onConfirm }: Options) {
  Alert.alert(title, message, [
    { text: "Cancel", style: "cancel" },
    { text: confirmLabel, style: "destructive", onPress: onConfirm },
  ]);
}
