import { useMemo, useState } from "react";
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import Animated, {
  FadeIn,
  FadeOut,
  SlideInDown,
  SlideOutDown,
  useAnimatedStyle,
  useDerivedValue,
  useReducedMotion,
  withSpring,
  withTiming,
} from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Path } from "react-native-svg";

import { duration, spring, timing } from "@/design/motion";
import { tick } from "@/design/risk";
import {
  MINIMUM_TARGET,
  colour,
  elevation,
  family,
  radius,
  space,
  type,
} from "@/design/tokens";

/** A list longer than this gets a search box; shorter than this does not need one. */
const SEARCH_THRESHOLD = 12;

export type Option = {
  readonly value: string;
  readonly label: string;
  readonly detail?: string;
};

/**
 * A select.
 *
 * A dropdown rather than a long list of radios, because these questions have one right
 * answer out of many and the screen should show the answer, not the whole catalogue.
 * Opening it takes over the bottom of the screen: on a phone, a menu anchored to a small
 * trigger is unreadable and lands under the thumb that opened it.
 */
export function Dropdown({
  label,
  placeholder,
  options,
  value,
  onChange,
  searchPlaceholder = "Search",
  disabled = false,
  loading = false,
  error = null,
  onRetry,
  emptyMessage = "Nothing to choose from yet.",
}: {
  label: string;
  placeholder: string;
  options: readonly Option[];
  value: string | null;
  onChange: (value: string) => void;
  searchPlaceholder?: string;
  disabled?: boolean;
  /** The options are still arriving. Not the same as there being none. */
  loading?: boolean;
  /** The options could not be fetched. Say so, and offer a way out. */
  error?: string | null;
  onRetry?: () => void;
  emptyMessage?: string;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const insets = useSafeAreaInsets();
  const reduceMotion = useReducedMotion();

  const selected = options.find((option) => option.value === value) ?? null;
  const searchable = options.length > SEARCH_THRESHOLD;

  const matches = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return options;
    return options.filter(
      (option) =>
        option.label.toLowerCase().includes(needle) ||
        (option.detail ?? "").toLowerCase().includes(needle),
    );
  }, [options, query]);

  const pressed = useDerivedValue(() =>
    reduceMotion
      ? withTiming(open ? 1 : 0, timing(duration.instant))
      : withSpring(open ? 1 : 0, spring.press),
  );

  const triggerStyle = useAnimatedStyle(() => ({
    borderColor: pressed.value > 0.5 ? colour.accent : colour.border,
  }));

  const close = () => {
    setOpen(false);
    setQuery("");
  };

  return (
    <View>
      <Animated.View style={triggerStyle}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={selected ? `${label}: ${selected.label}` : label}
          accessibilityHint="Opens a list to choose from"
          accessibilityState={{ expanded: open, disabled }}
          disabled={disabled}
          onPress={() => {
            void tick();
            setOpen(true);
          }}
          style={[styles.trigger, disabled && styles.triggerOff]}
        >
          <View style={styles.triggerText}>
            <Text style={styles.triggerLabel}>{label}</Text>
            <Text
              style={[styles.triggerValue, selected === null && styles.placeholder]}
              numberOfLines={1}
            >
              {selected?.label ?? placeholder}
            </Text>
            {selected?.detail ? (
              <Text style={styles.triggerDetail}>{selected.detail}</Text>
            ) : null}
          </View>
          <Chevron />
        </Pressable>
      </Animated.View>

      <Modal
        visible={open}
        transparent
        animationType="none"
        onRequestClose={close}
        accessibilityViewIsModal
      >
        <Animated.View
          entering={FadeIn.duration(duration.short)}
          exiting={FadeOut.duration(duration.short)}
          style={StyleSheet.absoluteFill}
        >
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Close without choosing"
            onPress={close}
            style={styles.backdrop}
          />
        </Animated.View>

        <Animated.View
          entering={
            reduceMotion
              ? FadeIn.duration(duration.short)
              : SlideInDown.springify().damping(22)
          }
          exiting={reduceMotion ? FadeOut : SlideOutDown.duration(duration.medium)}
          style={[styles.sheet, { paddingBottom: insets.bottom + space.comfortable }]}
        >
          <View style={styles.grip} />
          <Text style={styles.sheetTitle}>{label}</Text>

          {searchable && !loading && error === null ? (
            <TextInput
              value={query}
              onChangeText={setQuery}
              placeholder={searchPlaceholder}
              placeholderTextColor={colour.inkFaint}
              accessibilityLabel={searchPlaceholder}
              style={styles.search}
              autoCorrect={false}
            />
          ) : null}

          <ScrollView
            style={styles.list}
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={styles.listContent}
          >
            {/* Four different situations that all used to render as "nothing matches",
                which told somebody their search was wrong when the truth was that the
                list had not arrived. */}
            {loading ? (
              <Text style={styles.empty}>Loading…</Text>
            ) : error !== null ? (
              <View>
                <Text style={styles.empty}>{error}</Text>
                {onRetry ? (
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel="Try loading the list again"
                    onPress={onRetry}
                    style={styles.retry}
                  >
                    <Text style={styles.retryText}>Try again</Text>
                  </Pressable>
                ) : null}
              </View>
            ) : options.length === 0 ? (
              <Text style={styles.empty}>{emptyMessage}</Text>
            ) : matches.length === 0 ? (
              <Text style={styles.empty}>
                Nothing matches &ldquo;{query.trim()}&rdquo;. Try a shorter search.
              </Text>
            ) : (
              matches.map((option) => (
                <Row
                  key={option.value}
                  option={option}
                  selected={option.value === value}
                  onSelect={() => {
                    void tick();
                    onChange(option.value);
                    close();
                  }}
                />
              ))
            )}
          </ScrollView>
        </Animated.View>
      </Modal>
    </View>
  );
}

function Row({
  option,
  selected,
  onSelect,
}: {
  option: Option;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{ selected }}
      accessibilityLabel={
        option.detail ? `${option.label}. ${option.detail}` : option.label
      }
      onPress={onSelect}
      style={[styles.row, selected && styles.rowSelected]}
    >
      <View style={styles.rowText}>
        <Text style={[styles.rowLabel, selected && styles.rowLabelSelected]}>
          {option.label}
        </Text>
        {option.detail ? <Text style={styles.rowDetail}>{option.detail}</Text> : null}
      </View>
      {/* Selection is carried by a tick as well as by colour: red/green colour blindness
          affects roughly one man in twelve, and this decides a year of warnings. */}
      {selected ? <Tick /> : null}
    </Pressable>
  );
}

function Chevron() {
  return (
    <Svg width={18} height={18} viewBox="0 0 24 24" fill="none">
      <Path
        d="m6 9 6 6 6-6"
        stroke={colour.inkMuted}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

function Tick() {
  return (
    <Svg width={20} height={20} viewBox="0 0 24 24" fill="none">
      <Path
        d="m5 13 4 4L19 7"
        stroke={colour.accent}
        strokeWidth={2.6}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

const styles = StyleSheet.create({
  trigger: {
    minHeight: MINIMUM_TARGET + 14,
    flexDirection: "row",
    alignItems: "center",
    gap: space.base,
    backgroundColor: colour.surface,
    borderWidth: 1.5,
    borderColor: "transparent",
    borderRadius: radius.md,
    paddingHorizontal: space.comfortable,
    paddingVertical: space.base,
  },
  triggerOff: { opacity: 0.5 },
  triggerText: { flex: 1 },
  triggerLabel: {
    ...type.caption,
    fontFamily: family.bodyMedium,
    color: colour.inkFaint,
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  triggerValue: {
    ...type.body,
    fontFamily: family.bodyMedium,
    color: colour.ink,
    marginTop: 3,
  },
  placeholder: { color: colour.inkFaint, fontFamily: family.body },
  triggerDetail: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: 1,
  },
  backdrop: { flex: 1, backgroundColor: "rgba(20, 16, 10, 0.42)" },
  sheet: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    maxHeight: "78%",
    backgroundColor: colour.canvas,
    borderTopLeftRadius: radius.xl,
    borderTopRightRadius: radius.xl,
    paddingHorizontal: space.comfortable,
    paddingTop: space.base,
    ...elevation.lifted,
  },
  grip: {
    alignSelf: "center",
    width: 40,
    height: 4,
    borderRadius: radius.pill,
    backgroundColor: colour.borderStrong,
    marginBottom: space.base,
  },
  sheetTitle: {
    ...type.title,
    fontFamily: family.display,
    color: colour.ink,
    marginBottom: space.base,
  },
  search: {
    ...type.body,
    fontFamily: family.body,
    color: colour.ink,
    backgroundColor: colour.surface,
    borderWidth: 1.5,
    borderColor: colour.border,
    borderRadius: radius.md,
    paddingHorizontal: space.base,
    minHeight: MINIMUM_TARGET,
    marginBottom: space.snug,
  },
  list: { flexGrow: 0 },
  listContent: { paddingBottom: space.base },
  row: {
    minHeight: MINIMUM_TARGET + 6,
    flexDirection: "row",
    alignItems: "center",
    gap: space.base,
    paddingVertical: space.base,
    paddingHorizontal: space.base,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: "transparent",
  },
  rowSelected: {
    backgroundColor: colour.accentSubtle,
    borderColor: colour.accent,
  },
  rowText: { flex: 1 },
  rowLabel: { ...type.body, fontFamily: family.bodyMedium, color: colour.ink },
  rowLabelSelected: { color: colour.accentPressed },
  rowDetail: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: 1,
  },
  empty: {
    ...type.small,
    fontFamily: family.body,
    color: colour.inkMuted,
    paddingVertical: space.comfortable,
  },
  retry: {
    minHeight: MINIMUM_TARGET,
    alignSelf: "flex-start",
    justifyContent: "center",
    paddingHorizontal: space.comfortable,
    borderWidth: 1.5,
    borderColor: colour.accent,
    borderRadius: radius.md,
  },
  retryText: {
    ...type.body,
    fontFamily: family.bodySemibold,
    color: colour.accent,
  },
});
