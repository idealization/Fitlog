import { useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { fitlogApi } from "../api/client";
import type { RecommendationResponse } from "../api/types";
import { ActionButton } from "../components/ActionButton";
import { EmptyState } from "../components/EmptyState";
import { ItemPill } from "../components/ItemPill";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

export function RecommendationScreen() {
  const [prompt, setPrompt] = useState("깔끔한 출근룩");
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [selectedCandidateIndex, setSelectedCandidateIndex] = useState(0);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function requestRecommendation() {
    setLoading(true);
    setError(null);
    try {
      const response = await fitlogApi.createRecommendation({
        weather: {
          temperatureC: 21,
          feelsLikeC: 21,
          precipitationProbability: 0.1,
          precipitationType: "none"
        },
        styleRequest: {
          occasion: prompt.includes("출근") ? "work" : "daily",
          moodTags: prompt.includes("깔끔") ? ["minimal"] : [],
          formality: prompt.includes("출근") ? "business_casual" : "casual",
          trendLevel: "balanced"
        },
        limit: 3,
        useDemoCloset: true
      });
      setRecommendation(response);
      setSelectedCandidateIndex(0);
      setFeedbackMessage(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Recommendation request failed");
    } finally {
      setLoading(false);
    }
  }

  async function saveRecommendation() {
    if (!recommendation?.recommendationId) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      setRecommendation(await fitlogApi.saveRecommendation(recommendation.recommendationId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Save failed");
    } finally {
      setActionLoading(false);
    }
  }

  async function markWorn() {
    if (!recommendation?.recommendationId) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      await fitlogApi.markRecommendationWorn(recommendation.recommendationId);
      setRecommendation(await fitlogApi.getRecommendation(recommendation.recommendationId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Wear log failed");
    } finally {
      setActionLoading(false);
    }
  }

  async function sendFeedback(feedbackType: "liked" | "disliked" | "too_hot" | "too_cold" | "too_flashy") {
    if (!recommendation?.recommendationId) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      await fitlogApi.addRecommendationFeedback(recommendation.recommendationId, { feedbackType });
      setFeedbackMessage("피드백이 저장되었습니다");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Feedback failed");
    } finally {
      setActionLoading(false);
    }
  }

  const selectedCandidate = recommendation?.candidates[selectedCandidateIndex] ?? recommendation?.candidates[0];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.requestPanel}>
        <View style={styles.panelTitleRow}>
          <Feather name="edit-3" size={20} color={colors.coral} />
          <Text style={styles.title}>스타일 요청</Text>
        </View>
        <TextInput
          value={prompt}
          onChangeText={setPrompt}
          style={styles.input}
          placeholder="원하는 느낌"
          placeholderTextColor={colors.muted}
        />
        <ActionButton label="추천 받기" icon="zap" onPress={requestRecommendation} loading={loading} />
      </View>

      {recommendation?.candidates.length ? (
        <View style={styles.resultPanel}>
          <View style={styles.resultHeader}>
            <View>
              <Text style={styles.resultTitle}>추천 코디</Text>
              <Text style={styles.status}>{recommendation?.status ?? "candidate"}</Text>
            </View>
            <Text style={styles.score}>{Math.round((selectedCandidate?.score ?? 0) * 100)}%</Text>
          </View>

          <View style={styles.candidateTabs}>
            {recommendation.candidates.map((candidate, index) => (
              <TouchableOpacity
                key={candidate.itemIds.join("-")}
                accessibilityRole="button"
                accessibilityState={{ selected: selectedCandidateIndex === index }}
                onPress={() => setSelectedCandidateIndex(index)}
                style={[styles.candidateTab, selectedCandidateIndex === index && styles.candidateTabActive]}
              >
                <Text style={[styles.candidateTabText, selectedCandidateIndex === index && styles.candidateTabTextActive]}>
                  {index + 1}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.itemStack}>
            {selectedCandidate?.items.map((item) => (
              <View key={item.id} style={styles.outfitItem}>
                <Text style={styles.outfitName}>{item.name}</Text>
                <View style={styles.pills}>
                  <ItemPill label={item.category} tone="ink" />
                  {item.styleTags.slice(0, 1).map((tag) => (
                    <ItemPill key={tag} label={tag} />
                  ))}
                </View>
              </View>
            ))}
          </View>

          <View style={styles.reasonBox}>
            {selectedCandidate?.reasons.map((reason) => (
              <Text key={reason} style={styles.reason}>
                {reason}
              </Text>
            ))}
          </View>

          <View style={styles.actions}>
            <ActionButton
              label="저장"
              icon="bookmark"
              tone="secondary"
              onPress={saveRecommendation}
              loading={actionLoading}
            />
            <ActionButton label="오늘 입음" icon="check-circle" onPress={markWorn} loading={actionLoading} />
          </View>

          <View style={styles.feedbackPanel}>
            <Text style={styles.feedbackTitle}>피드백</Text>
            <View style={styles.feedbackButtons}>
              <FeedbackChip label="좋아요" onPress={() => sendFeedback("liked")} />
              <FeedbackChip label="별로" onPress={() => sendFeedback("disliked")} />
              <FeedbackChip label="더움" onPress={() => sendFeedback("too_hot")} />
              <FeedbackChip label="추움" onPress={() => sendFeedback("too_cold")} />
              <FeedbackChip label="튀어요" onPress={() => sendFeedback("too_flashy")} />
            </View>
            {feedbackMessage ? <Text style={styles.feedbackMessage}>{feedbackMessage}</Text> : null}
          </View>
        </View>
      ) : (
        <EmptyState icon="zap" title="추천 결과 없음" body="원하는 느낌을 입력하면 코디가 생성됩니다." />
      )}

      {error ? <Text style={styles.error}>{error}</Text> : null}
    </ScrollView>
  );
}

function FeedbackChip({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <TouchableOpacity accessibilityRole="button" onPress={onPress} style={styles.feedbackChip}>
      <Text style={styles.feedbackChipText}>{label}</Text>
    </TouchableOpacity>
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
  requestPanel: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    borderColor: colors.border,
    borderWidth: 1,
    padding: spacing.lg,
    gap: spacing.md
  },
  panelTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm
  },
  title: {
    color: colors.text,
    fontSize: 20,
    fontWeight: "900"
  },
  input: {
    minHeight: 48,
    borderRadius: 8,
    borderColor: colors.border,
    borderWidth: 1,
    paddingHorizontal: spacing.md,
    color: colors.text,
    backgroundColor: colors.background,
    fontSize: 15,
    fontWeight: "700"
  },
  resultPanel: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    borderColor: colors.border,
    borderWidth: 1,
    padding: spacing.lg,
    gap: spacing.md
  },
  resultHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  resultTitle: {
    color: colors.text,
    fontSize: 19,
    fontWeight: "900"
  },
  status: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
    marginTop: 2
  },
  score: {
    color: colors.green,
    fontSize: 24,
    fontWeight: "900"
  },
  candidateTabs: {
    flexDirection: "row",
    gap: spacing.sm
  },
  candidateTab: {
    width: 36,
    height: 36,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center"
  },
  candidateTabActive: {
    backgroundColor: colors.green,
    borderColor: colors.green
  },
  candidateTabText: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "900"
  },
  candidateTabTextActive: {
    color: colors.surface
  },
  itemStack: {
    gap: spacing.sm
  },
  outfitItem: {
    minHeight: 58,
    paddingVertical: spacing.sm,
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    gap: spacing.xs
  },
  outfitName: {
    color: colors.text,
    fontSize: 15,
    fontWeight: "800"
  },
  pills: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs
  },
  reasonBox: {
    backgroundColor: colors.surfaceAlt,
    borderRadius: 8,
    padding: spacing.md,
    gap: spacing.xs
  },
  reason: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 18,
    fontWeight: "600"
  },
  actions: {
    gap: spacing.sm
  },
  feedbackPanel: {
    gap: spacing.sm
  },
  feedbackTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "900"
  },
  feedbackButtons: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  feedbackChip: {
    minHeight: 34,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    backgroundColor: colors.background
  },
  feedbackChipText: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "900"
  },
  feedbackMessage: {
    color: colors.green,
    fontSize: 12,
    fontWeight: "800"
  },
  error: {
    color: colors.danger,
    fontWeight: "700"
  }
});
