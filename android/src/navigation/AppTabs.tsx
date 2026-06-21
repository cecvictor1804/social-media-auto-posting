import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Text } from "react-native";
import { useQueryClient } from "@tanstack/react-query";

import { PostsStack } from "./PostsStack";
import { ComposeScreen } from "@/screens/compose/ComposeScreen";
import { CalendarScreen } from "@/screens/calendar/CalendarScreen";
import { AccountsScreen } from "@/screens/accounts/AccountsScreen";
import { UsersScreen } from "@/screens/users/UsersScreen";
import { qk } from "@/constants/queryKeys";
import type { User } from "@/types/api";

export type AppTabsParamList = {
  Compose: undefined;
  QueueStack: undefined;
  Calendar: undefined;
  Accounts: { connected?: string; error?: string } | undefined;
};

export type AppModalParamList = {
  Tabs: undefined;
  Users: undefined;
};

const Tab = createBottomTabNavigator<AppTabsParamList>();
const Modal = createNativeStackNavigator<AppModalParamList>();

function icon(emoji: string, focused: boolean) {
  return <Text style={{ fontSize: 22, opacity: focused ? 1 : 0.5 }}>{emoji}</Text>;
}

function Tabs() {
  const qc = useQueryClient();
  const me = qc.getQueryData<User>(qk.me);
  return (
    <Tab.Navigator
      screenOptions={{ headerShown: true, tabBarActiveTintColor: "#2563eb" }}
    >
      <Tab.Screen
        name="Compose"
        component={ComposeScreen}
        options={{ tabBarIcon: ({ focused }) => icon("✏️", focused), title: "Compose" }}
      />
      <Tab.Screen
        name="QueueStack"
        component={PostsStack}
        options={{
          tabBarIcon: ({ focused }) => icon("📋", focused),
          tabBarLabel: "Queue",
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="Calendar"
        component={CalendarScreen}
        options={{ tabBarIcon: ({ focused }) => icon("📅", focused), title: "Calendar" }}
      />
      <Tab.Screen
        name="Accounts"
        component={AccountsScreen}
        options={{ tabBarIcon: ({ focused }) => icon("🔗", focused), title: "Accounts" }}
      />
    </Tab.Navigator>
  );
}

export function AppTabs() {
  const qc = useQueryClient();
  const me = qc.getQueryData<User>(qk.me);

  return (
    <Modal.Navigator>
      <Modal.Screen name="Tabs" component={Tabs} options={{ headerShown: false }} />
      {me?.is_admin && (
        <Modal.Screen
          name="Users"
          component={UsersScreen}
          options={{ title: "Users", presentation: "modal" }}
        />
      )}
    </Modal.Navigator>
  );
}
