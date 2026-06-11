import { StatusBar } from "expo-status-bar";
import { useMemo, useState } from "react";
import { SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { HomeScreen } from "./src/screens/HomeScreen";
import { ClosetScreen } from "./src/screens/ClosetScreen";
import { RecommendationScreen } from "./src/screens/RecommendationScreen";
import { SettingsScreen } from "./src/screens/SettingsScreen";
import { colors } from "./src/theme/colors";
import { spacing } from "./src/theme/spacing";

type TabKey = "home" | "closet" | "recommend" | "settings";

const tabs: Array<{ key: TabKey; label: string; icon: keyof typeof Feather.glyphMap }> = [
  { key: "home", label: "오늘", icon: "sun" },
  { key: "closet", label: "옷장", icon: "grid" },
  { key: "recommend", label: "추천", icon: "zap" },
  { key: "settings", label: "설정", icon: "sliders" }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("home");

  const screen = useMemo(() => {
    switch (activeTab) {
      case "closet":
        return <ClosetScreen />;
      case "recommend":
        return <RecommendationScreen />;
      case "settings":
        return <SettingsScreen />;
      case "home":
      default:
        return <HomeScreen onOpenRecommendation={() => setActiveTab("recommend")} />;
    }
  }, [activeTab]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <View style={styles.header}>
        <View>
          <Text style={styles.logo}>Fitlog</Text>
          <Text style={styles.subtitle}>AI wardrobe</Text>
        </View>
      </View>
      <View style={styles.content}>{screen}</View>
      <View style={styles.tabBar}>
        {tabs.map((tab) => {
          const selected = activeTab === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              style={[styles.tabButton, selected && styles.tabButtonActive]}
              onPress={() => setActiveTab(tab.key)}
            >
              <Feather name={tab.icon} size={20} color={selected ? colors.surface : colors.muted} />
              <Text style={[styles.tabLabel, selected && styles.tabLabelActive]}>{tab.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    paddingTop: spacing.sm,
    borderBottomColor: colors.border,
    borderBottomWidth: 1
  },
  logo: {
    color: colors.text,
    fontSize: 28,
    fontWeight: "800"
  },
  subtitle: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "600",
    marginTop: 2
  },
  content: {
    flex: 1
  },
  tabBar: {
    flexDirection: "row",
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderTopColor: colors.border,
    borderTopWidth: 1,
    backgroundColor: colors.surface
  },
  tabButton: {
    flex: 1,
    minHeight: 52,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    gap: 2
  },
  tabButtonActive: {
    backgroundColor: colors.green
  },
  tabLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: "700"
  },
  tabLabelActive: {
    color: colors.surface
  }
});

