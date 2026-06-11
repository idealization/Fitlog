import { useCallback, useEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, TextInput, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { fitlogApi } from "../api/client";
import type { AnalysisJobResponse, Category, ClosetItem } from "../api/types";
import { ActionButton } from "../components/ActionButton";
import { EmptyState } from "../components/EmptyState";
import { ItemPill } from "../components/ItemPill";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

export function ClosetScreen() {
  const [items, setItems] = useState<ClosetItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [newItemName, setNewItemName] = useState("White shirt");
  const [newItemCategory, setNewItemCategory] = useState<Category>("top");
  const [newItemColor, setNewItemColor] = useState("white");
  const [analysisJob, setAnalysisJob] = useState<AnalysisJobResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await fitlogApi.listClosetItems());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Closet request failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function createItem() {
    setCreating(true);
    setError(null);
    try {
      await fitlogApi.createClosetItem({
        id: slugify(`${newItemName}-${Date.now()}`),
        name: newItemName,
        category: newItemCategory,
        subType: defaultSubType(newItemCategory),
        seasons: ["all"],
        styleTags: ["minimal"],
        colors: [newItemColor],
        formality: "business_casual",
        warmth: 4,
        breathability: 7
      });
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Create item failed");
    } finally {
      setCreating(false);
    }
  }

  async function startAnalysisJob() {
    setAnalyzing(true);
    setError(null);
    try {
      const ticket = await fitlogApi.createUploadTicket({
        fileName: `${slugify(newItemName)}.jpg`,
        contentType: "image/jpeg"
      });
      const job = await fitlogApi.createAnalysisJob({
        uploadId: ticket.uploadId,
        requestedOperations: ["quality_check", "attribute_extraction", "illustration"]
      });
      setAnalysisJob(job);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Image analysis job failed");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(item) => item.id}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      contentContainerStyle={styles.list}
      ListHeaderComponent={
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.title}>디지털 옷장</Text>
            <Text style={styles.count}>{items.length} items</Text>
          </View>
          <Feather name="camera" size={22} color={colors.green} />
        </View>
        <View style={styles.creationPanel}>
          <Text style={styles.panelTitle}>빠른 등록</Text>
          <View style={styles.fieldRow}>
            <TextInput
              value={newItemName}
              onChangeText={setNewItemName}
              style={styles.input}
              placeholder="아이템 이름"
              placeholderTextColor={colors.muted}
            />
            <TextInput
              value={newItemColor}
              onChangeText={setNewItemColor}
              style={styles.inputCompact}
              placeholder="색상"
              placeholderTextColor={colors.muted}
            />
          </View>
          <View style={styles.categoryRow}>
            {(["top", "bottom", "shoes", "outerwear"] as Category[]).map((category) => (
              <Text
                key={category}
                onPress={() => setNewItemCategory(category)}
                style={[styles.categoryChip, newItemCategory === category && styles.categoryChipActive]}
              >
                {category}
              </Text>
            ))}
          </View>
          <View style={styles.actionRow}>
            <ActionButton label="아이템 저장" icon="plus" onPress={createItem} loading={creating} style={styles.flexAction} />
            <ActionButton
              label="분석 시작"
              icon="upload"
              tone="secondary"
              onPress={startAnalysisJob}
              loading={analyzing}
              style={styles.flexAction}
            />
          </View>
          {analysisJob ? (
            <Text style={styles.jobStatus}>
              job {analysisJob.jobId.slice(0, 8)} / {analysisJob.status}
            </Text>
          ) : null}
        </View>
      }
      ListEmptyComponent={
        <EmptyState icon="archive" title="등록된 의류가 없습니다" body="새 아이템을 추가하면 옷장이 채워집니다." />
      }
      renderItem={({ item }) => <ClosetItemRow item={item} />}
      ListFooterComponent={error ? <Text style={styles.error}>{error}</Text> : null}
    />
  );
}

function slugify(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function defaultSubType(category: Category) {
  switch (category) {
    case "bottom":
      return "slacks";
    case "shoes":
      return "loafers";
    case "outerwear":
      return "jacket";
    case "top":
    default:
      return "shirt";
  }
}

function ClosetItemRow({ item }: { item: ClosetItem }) {
  return (
    <View style={styles.itemRow}>
      <View style={styles.thumbnail}>
        <Text style={styles.thumbnailText}>{item.name.slice(0, 1).toUpperCase()}</Text>
      </View>
      <View style={styles.itemBody}>
        <Text style={styles.itemName} numberOfLines={1}>
          {item.name}
        </Text>
        <Text style={styles.itemMeta} numberOfLines={1}>
          {item.category} / {item.subType}
        </Text>
        <View style={styles.pills}>
          {item.colors.slice(0, 2).map((color) => (
            <ItemPill key={color} label={color} tone="ink" />
          ))}
          {item.styleTags.slice(0, 1).map((tag) => (
            <ItemPill key={tag} label={tag} />
          ))}
        </View>
      </View>
      <Feather name="chevron-right" size={20} color={colors.muted} />
    </View>
  );
}

const styles = StyleSheet.create({
  list: {
    padding: spacing.lg,
    gap: spacing.md
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.md
  },
  creationPanel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 8,
    padding: spacing.md,
    gap: spacing.sm,
    marginBottom: spacing.md
  },
  panelTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: "900"
  },
  fieldRow: {
    flexDirection: "row",
    gap: spacing.sm
  },
  input: {
    flex: 1,
    minHeight: 44,
    borderRadius: 8,
    borderColor: colors.border,
    borderWidth: 1,
    color: colors.text,
    paddingHorizontal: spacing.md,
    fontWeight: "800",
    backgroundColor: colors.background
  },
  inputCompact: {
    width: 88,
    minHeight: 44,
    borderRadius: 8,
    borderColor: colors.border,
    borderWidth: 1,
    color: colors.text,
    paddingHorizontal: spacing.md,
    fontWeight: "800",
    backgroundColor: colors.background
  },
  categoryRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  categoryChip: {
    minHeight: 32,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    color: colors.muted,
    fontSize: 12,
    fontWeight: "900",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  categoryChipActive: {
    color: colors.surface,
    backgroundColor: colors.green,
    borderColor: colors.green
  },
  actionRow: {
    flexDirection: "row",
    gap: spacing.sm
  },
  flexAction: {
    flex: 1
  },
  jobStatus: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "800"
  },
  title: {
    color: colors.text,
    fontSize: 22,
    fontWeight: "900"
  },
  count: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
    marginTop: 2
  },
  itemRow: {
    minHeight: 92,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface
  },
  thumbnail: {
    width: 56,
    height: 56,
    borderRadius: 8,
    backgroundColor: colors.surfaceAlt,
    alignItems: "center",
    justifyContent: "center"
  },
  thumbnailText: {
    color: colors.green,
    fontSize: 20,
    fontWeight: "900"
  },
  itemBody: {
    flex: 1,
    gap: spacing.xs
  },
  itemName: {
    color: colors.text,
    fontSize: 15,
    fontWeight: "900"
  },
  itemMeta: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700"
  },
  pills: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs
  },
  error: {
    color: colors.danger,
    fontWeight: "700",
    marginTop: spacing.md
  }
});
