import { useMutation } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import Animated, { FadeIn, FadeInDown } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { DawuroMark } from "@/components/dawuro-mark";
import { duration } from "@/design/motion";
import { confirm } from "@/design/risk";
import { MINIMUM_TARGET, colour, family, radius, space, type } from "@/design/tokens";
import { api } from "@/lib/api/client";
import {
  MINIMUM_PASSWORD_LENGTH,
  asLocalNumber,
  isCompleteNumber,
} from "@/lib/identity/phone-number";
import { useSession } from "@/lib/identity/session";

/**
 * Signing back in.
 *
 * The number and the password, and nothing else. Somebody arrives here because they
 * changed phone or signed out, and both of those are already a bad day; asking them to
 * remember a username on top of a password would be a third thing to get wrong.
 */
export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { join: keepSession } = useSession();

  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");

  const signIn = useMutation({
    mutationFn: () =>
      api.signInCitizen({
        phone_number: asLocalNumber(phoneNumber),
        password,
      }),
    onSuccess: async (session) => {
      await keepSession(session);
      await confirm();
      router.replace("/");
    },
  });

  const ready =
    isCompleteNumber(phoneNumber) && password.length >= MINIMUM_PASSWORD_LENGTH;

  const submit = () => {
    if (!ready || signIn.isPending) return;
    signIn.mutate();
  };

  return (
    <KeyboardAvoidingView
      style={styles.host}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={[styles.header, { paddingTop: insets.top + space.comfortable }]}>
        <DawuroMark colour={colour.accent} size={34} />
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <Animated.View entering={FadeIn.duration(duration.medium)}>
          <Text style={styles.question}>Welcome back</Text>
          <Text style={styles.aside}>
            Sign in with the number and password you joined with.
          </Text>

          <TextInput
            value={phoneNumber}
            onChangeText={setPhoneNumber}
            placeholder="024 123 4567"
            placeholderTextColor={colour.inkFaint}
            autoFocus
            keyboardType="phone-pad"
            textContentType="telephoneNumber"
            accessibilityLabel="Your phone number"
            style={styles.input}
          />
          <TextInput
            value={password}
            onChangeText={setPassword}
            placeholder="Your password"
            placeholderTextColor={colour.inkFaint}
            secureTextEntry
            autoCapitalize="none"
            textContentType="password"
            accessibilityLabel="Your password"
            style={[styles.input, { marginTop: space.base }]}
            returnKeyType="go"
            onSubmitEditing={submit}
          />

          {signIn.isError ? (
            <Text style={styles.error} accessibilityRole="alert">
              {signIn.error.message}
            </Text>
          ) : null}

          <Pressable
            onPress={() => router.replace("/join")}
            accessibilityRole="button"
            accessibilityLabel="Create a new account instead"
            style={styles.secondary}
          >
            <Text style={styles.secondaryText}>New here? Become a Guardian</Text>
          </Pressable>
        </Animated.View>
      </ScrollView>

      <Animated.View
        entering={FadeInDown.duration(duration.medium)}
        style={[styles.footer, { paddingBottom: insets.bottom + space.comfortable }]}
      >
        <Pressable
          onPress={submit}
          disabled={!ready || signIn.isPending}
          accessibilityRole="button"
          accessibilityLabel="Sign in"
          accessibilityState={{ disabled: !ready || signIn.isPending }}
          style={[styles.primary, (!ready || signIn.isPending) && styles.primaryOff]}
        >
          <Text style={styles.primaryText}>
            {signIn.isPending ? "Signing in…" : "Sign in"}
          </Text>
        </Pressable>
      </Animated.View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  host: { flex: 1, backgroundColor: colour.canvas },
  header: { paddingHorizontal: space.comfortable, paddingBottom: space.base },
  scroll: { flex: 1 },
  content: { paddingHorizontal: space.comfortable, paddingBottom: space.section },
  question: {
    ...type.display,
    fontFamily: family.display,
    color: colour.ink,
    marginTop: space.base,
  },
  aside: {
    ...type.body,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: space.snug,
    marginBottom: space.roomy,
  },
  input: {
    ...type.body,
    fontFamily: family.body,
    color: colour.ink,
    minHeight: MINIMUM_TARGET + 6,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: colour.border,
    backgroundColor: colour.surface,
    paddingHorizontal: space.comfortable,
  },
  error: {
    ...type.caption,
    color: colour.riskSevere,
    marginTop: space.base,
  },
  secondary: {
    marginTop: space.roomy,
    minHeight: MINIMUM_TARGET,
    justifyContent: "center",
  },
  secondaryText: {
    ...type.body,
    fontFamily: family.bodySemibold,
    color: colour.accent,
    textAlign: "center",
  },
  footer: {
    paddingHorizontal: space.comfortable,
    paddingTop: space.base,
    borderTopWidth: 1,
    borderTopColor: colour.border,
  },
  primary: {
    minHeight: MINIMUM_TARGET + 6,
    borderRadius: radius.pill,
    backgroundColor: colour.accent,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryOff: { backgroundColor: colour.borderStrong },
  primaryText: {
    ...type.body,
    fontFamily: family.bodySemibold,
    color: colour.onAccent,
  },
});
