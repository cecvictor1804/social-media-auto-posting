import React from "react";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { QueueScreen } from "@/screens/queue/QueueScreen";
import { ReviewScreen } from "@/screens/queue/ReviewScreen";

export type PostsStackParamList = {
  Queue: undefined;
  Review: { postId: number };
};

const Stack = createNativeStackNavigator<PostsStackParamList>();

export function PostsStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen
        name="Queue"
        component={QueueScreen}
        options={{ title: "Queue" }}
      />
      <Stack.Screen
        name="Review"
        component={ReviewScreen}
        options={{ title: "Review post" }}
      />
    </Stack.Navigator>
  );
}
