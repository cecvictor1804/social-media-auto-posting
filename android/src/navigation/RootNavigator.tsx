import React, { useEffect, useState } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import * as Linking from "expo-linking";
import { useQueryClient } from "@tanstack/react-query";

import { getToken } from "@/lib/auth";
import { api } from "@/lib/api";
import { qk } from "@/constants/queryKeys";
import type { User } from "@/types/api";

import { LoginScreen } from "@/screens/auth/LoginScreen";
import { AppTabs } from "./AppTabs";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export type RootStackParamList = {
  Login: undefined;
  App: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

// Deep-link config for socialposter:// scheme.
// The App screen passes deep links into the nested tab navigator's Accounts tab.
const linking = {
  prefixes: [Linking.createURL("/"), "socialposter://"],
  config: {
    screens: {
      App: "app",
      Login: "login",
    },
  },
};

function AuthGate() {
  const qc = useQueryClient();
  const [ready, setReady] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  // On mount, check whether we have a stored token
  useEffect(() => {
    getToken().then((t) => {
      setHasToken(!!t);
      setReady(true);
    });
  }, []);

  // Probe /api/auth/me — if this succeeds the token is valid; if 401 the api
  // client clears the token and we'll land back on LoginScreen next render.
  const me = useQuery<User>({
    queryKey: qk.me,
    queryFn: () => api.get<User>("/api/auth/me"),
    enabled: hasToken,
    retry: false,
  });

  if (!ready || (hasToken && me.isLoading)) {
    return <LoadingSpinner />;
  }

  const isAuthenticated = hasToken && !!me.data;

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <Stack.Screen name="App" component={AppTabs} />
      ) : (
        <Stack.Screen name="Login" component={LoginScreen} />
      )}
    </Stack.Navigator>
  );
}

export function RootNavigator() {
  return (
    <QueryClientProvider client={queryClient}>
      <NavigationContainer linking={linking}>
        <AuthGate />
      </NavigationContainer>
    </QueryClientProvider>
  );
}
