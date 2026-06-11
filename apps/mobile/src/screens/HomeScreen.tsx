import { useCallback, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { fitlogApi } from "../api/client";
import type { MorningRunResponse } from "../api/types";
import { ActionButton } from "../components/ActionButton";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type Props = {
  onOpenRecommendation: () => void;
};

export function HomeScreen({ onOpenRecommendation }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MorningRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runMorning = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setResult(await fitlogApi.runMorningRecommendation());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Morning run failed");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={runMorning} />}
    >
      <View style={styles.band}>
        <View style={styles.bandHeader}>
          <Feather name="cloud-sun" size={22} color={colors.gold} />
          <Text style={styles.bandTitle}>오늘의 추천</Text>
        </View>
        <Text style={styles.bandBody}>오늘 입기 좋은 조합을 준비합니다.</Text>
        <View style={styles.actions}>
          <ActionButton label="아침 추천 실행" icon="play" onPress={runMorning} loading={loading} />
          <ActionButton label="추천 요청" icon="zap" tone="secondary" onPress={onOpenRecommendation} />
        </View>
      </View>

      {result ? (
        <View style={styles.summary}>
          <Text style={styles.summaryLabel}>상태</Text>
          <Text style={styles.summaryValue}>{result.created ? "생성됨" : result.reason}</Text>
          <Text style={styles.summaryLabel}>추천 ID</Text>
          <Text style={styles.summaryValue}>{result.recommendationId ?? "-"}</Text>
          <Text style={styles.summaryLabel}>날씨 소스</Text>
          <Text style={styles.summaryValue}>{result.weatherSource}</Text>
        </View>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1
  },
  content: {
    padding: spacing.lg,
    gap: spacing.lg
  },
  band: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    borderColor: colors.border,
    borderWidth: 1,
    padding: spacing.lg,
    gap: spacing.md
  },
  bandHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm
  },
  bandTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: "900"
  },
  bandBody: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20
  },
  actions: {
    gap: spacing.sm
  },
  summary: {
    backgroundColor: colors.surfaceAlt,
    borderRadius: 8,
    padding: spacing.lg,
    gap: spacing.xs
  },
  summaryLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "800"
  },
  summaryValue: {
    color: colors.text,
    fontSize: 15,
    fontWeight: "700",
    marginBottom: spacing.sm
  },
  error: {
    color: colors.danger,
    fontWeight: "700"
  }
});
