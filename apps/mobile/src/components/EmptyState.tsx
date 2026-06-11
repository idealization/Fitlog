import { StyleSheet, Text, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type Props = {
  icon: keyof typeof Feather.glyphMap;
  title: string;
  body: string;
};

export function EmptyState({ icon, title, body }: Props) {
  return (
    <View style={styles.container}>
      <Feather name={icon} size={24} color={colors.green} />
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.body}>{body}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.xl,
    gap: spacing.sm
  },
  title: {
    color: colors.text,
    fontSize: 16,
    fontWeight: "800"
  },
  body: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
    textAlign: "center"
  }
});

