import { Tabs } from "expo-router";
import { Platform } from "react-native";

import {
  GuardianIcon,
  LearnIcon,
  PlayIcon,
  ReportIcon,
  TodayIcon,
  type TabIconProps,
} from "@/components/tab-icons";
import { colour, family, space } from "@/design/tokens";

/**
 * The five places worth going.
 *
 * They used to be a list of cards down the home screen, which meant the warning had to
 * share the first screen with a menu, and two of the destinations were reachable only by
 * scrolling past it. A tab bar keeps every one of them one tap away and gives the
 * forecast the whole screen back.
 *
 * Five and no more: a sixth would start shrinking the targets on the small, cheap phones
 * this is built for. The district page is still a push from Today, because it is
 * somewhere you go from the forecast rather than a place you switch to.
 */

const TABS = [
  { name: "index", title: "Today", icon: TodayIcon },
  { name: "learn", title: "Learn", icon: LearnIcon },
  { name: "play", title: "Play", icon: PlayIcon },
  { name: "report", title: "Report", icon: ReportIcon },
  { name: "guardian", title: "You", icon: GuardianIcon },
] as const;

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colour.accent,
        tabBarInactiveTintColor: colour.inkFaint,
        sceneStyle: { backgroundColor: colour.canvas },
        tabBarStyle: {
          backgroundColor: colour.surface,
          borderTopColor: colour.border,
          borderTopWidth: 1,
          height: Platform.OS === "ios" ? 88 : 64,
          paddingTop: space.tight,
        },
        tabBarLabelStyle: {
          fontFamily: family.bodyMedium,
          fontSize: 11,
          letterSpacing: 0.1,
        },
        tabBarItemStyle: { paddingVertical: 2 },
      }}
    >
      {TABS.map(({ name, title, icon: Icon }) => (
        <Tabs.Screen
          key={name}
          name={name}
          options={{
            title,
            tabBarIcon: ({ color, focused }: { color: string; focused: boolean }) => {
              const props: TabIconProps = { colour: color, focused };
              return <Icon {...props} />;
            },
          }}
        />
      ))}
    </Tabs>
  );
}
