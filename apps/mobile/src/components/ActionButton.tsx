import { ReactNode } from "react";
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, ViewStyle } from "react-native";
import { Feather } from "@expo/vector-icons";

import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type Props = {
  label: string;
  icon: keyof typeof Feather.glyphMap;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  tone?: "primary" | "secondary" | "danger";
  style?: ViewStyle;
  children?: ReactNode;
};

export function ActionButton({
  label,
  icon,
  onPress,
  loading = false,
  disabled = false,
  tone = "primary",
  style
}: Props) {
  const palette = tone === "danger" ? colors.danger : tone === "secondary" ? colors.ink : colors.green;
  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={label}
      disabled={disabled || loading}
      onPress={onPress}
      style={[styles.button, { backgroundColor: palette }, (disabled || loading) && styles.disabled, style]}
    >
      {loading ? <ActivityIndicator color={colors.surface} /> : <Feather name={icon} size={18} color={colors.surface} />}
      <Text style={styles.label}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 44,
    borderRadius: 8,
    paddingHorizontal: spacing.md,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: spacing.sm
  },
  disabled: {
    opacity: 0.55
  },
  label: {
    color: colors.surface,
    fontSize: 14,
    fontWeight: "800"
  }
});

