import { Fraunces_600SemiBold } from "@expo-google-fonts/fraunces";
import {
  Inter_400Regular,
  Inter_500Medium,
  Inter_600SemiBold,
} from "@expo-google-fonts/inter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { StatusBar } from "expo-status-bar";
import { useCallback, useEffect, useState } from "react";
import { View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { Opening } from "@/components/opening";
import { colour } from "@/design/tokens";
import { SessionProvider } from "@/lib/identity/session";

const STALE_AFTER_MS = 5 * 60 * 1000;

/**
 * Hold the native splash until the fonts are ready, so nobody sees the verdict render in
 * a fallback face and then jump. The native splash and the animated opening share the
 * same field colour, which is what makes the handover invisible.
 */
void SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: STALE_AFTER_MS, retry: 1, refetchOnWindowFocus: false },
        },
      }),
  );

  const [fontsLoaded, fontError] = useFonts({
    Fraunces_600SemiBold,
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
  });

  const [openingDone, setOpeningDone] = useState(false);
  const ready = fontsLoaded || fontError !== null;

  useEffect(() => {
    // The app renders underneath the opening, so the fetch is already in flight by the
    // time the rings finish. The opening costs the reader nothing.
    if (ready) void SplashScreen.hideAsync();
  }, [ready]);

  const finish = useCallback(() => setOpeningDone(true), []);

  if (!ready) return <View style={{ flex: 1, backgroundColor: colour.field }} />;

  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: colour.canvas }}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <SessionProvider>
            <StatusBar style={openingDone ? "dark" : "light"} />
            <Stack
              screenOptions={{
                headerShown: false,
                contentStyle: { backgroundColor: colour.canvas },
                animation: "fade",
                animationDuration: 170,
              }}
            />
            {openingDone ? null : <Opening onFinished={finish} />}
          </SessionProvider>
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
