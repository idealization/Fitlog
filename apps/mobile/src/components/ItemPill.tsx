import { StyleSheet, Text, View } from "react-native";

import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type Props = {
  label: string;
  tone?: "green" | "coral" | "ink" | "gold";
};

export function ItemPill({ label, tone = "green" }: Props) {
  const color = colors[tone];
  return (
    <View style={[styles.pill, { borderColor: color }]}>
      <Text style={[styles.label, { color }]} numberOfLines={1}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    minHeight: 28,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: spacing.sm,
    alignItems: "center",
    justifyContent: "center"
  },
  label: {
    fontSize: 12,
    fontWeight: "800"
  }
});

