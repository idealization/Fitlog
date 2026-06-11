import { useCallback, useEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, TextInput, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { fitlogApi } from "../api/client";
import type {
  AnalyzedClosetItemDraft,
  AnalysisJobResponse,
  Category,
  ClosetItem,
  ClosetItemCreateRequest,
  Formality,
  ImageAnalysisResult,
  ItemStatus,
  Season,
  Thickness,
  WorkerRunResponse
} from "../api/types";
import { ActionButton } from "../components/ActionButton";
import { EmptyState } from "../components/EmptyState";
import { ItemPill } from "../components/ItemPill";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type DraftFormState = {
  jobId: string;
  illustrationStorageKey: string;
  qualityScore: number;
  name: string;
  category: Category;
  subType: string;
  colorsText: string;
  styleTagsText: string;
  seasonsText: string;
  thickness: Thickness;
  formality: Formality;
  status: ItemStatus;
  rainSafe: boolean;
  warmthText: string;
  breathabilityText: string;
};

const categoryOptions: Category[] = ["top", "bottom", "outerwear", "dress", "shoes", "bag", "accessory"];
const quickCategoryOptions: Category[] = ["top", "bottom", "shoes", "outerwear"];
const thicknessOptions: Thickness[] = ["light", "medium", "heavy"];
const formalityOptions: Formality[] = ["casual", "business_casual", "formal"];

export function ClosetScreen() {
  const [items, setItems] = useState<ClosetItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [newItemName, setNewItemName] = useState("White shirt");
  const [newItemCategory, setNewItemCategory] = useState<Category>("top");
  const [newItemColor, setNewItemColor] = useState("white");
  const [analysisJob, setAnalysisJob] = useState<AnalysisJobResponse | null>(null);
  const [workerRun, setWorkerRun] = useState<WorkerRunResponse | null>(null);
  const [draft, setDraft] = useState<DraftFormState | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
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
    setNotice(null);
    try {
      await fitlogApi.createClosetItem({
        id: uniqueItemId(newItemName),
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
      setNotice("아이템을 저장했어요.");
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
    setNotice(null);
    setDraft(null);
    setWorkerRun(null);
    try {
      const ticket = await fitlogApi.createUploadTicket({
        fileName: `${slugify(newItemName) || "closet-item"}.jpg`,
        contentType: "image/jpeg"
      });
      const createdJob = await fitlogApi.createAnalysisJob({
        uploadId: ticket.uploadId,
        requestedOperations: ["quality_check", "attribute_extraction", "illustration"]
      });
      setAnalysisJob(createdJob);

      const processed = await processAnalysisQueueForJob(createdJob.jobId);
      setWorkerRun(processed);

      if (!processed.processed || !processed.result || processed.jobId !== createdJob.jobId) {
        const currentJob = await fitlogApi.getAnalysisJob(createdJob.jobId);
        setAnalysisJob(currentJob);
        setNotice("분석 대기열이 비어 있거나 다른 작업이 먼저 처리됐어요.");
        return;
      }

      const completedJob = await fitlogApi.getAnalysisJob(createdJob.jobId);
      setAnalysisJob(completedJob);
      setDraft(toDraftFormState(processed.result, newItemName, newItemCategory, newItemColor));
      setNotice("분석 초안을 만들었어요. 확인 후 저장하세요.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Image analysis job failed");
    } finally {
      setAnalyzing(false);
    }
  }

  async function saveAnalyzedDraft() {
    if (!draft) {
      return;
    }

    setSavingDraft(true);
    setError(null);
    setNotice(null);
    try {
      await fitlogApi.createClosetItem(toCreateRequest(draft));
      setNotice("분석 초안을 옷장에 저장했어요.");
      setDraft(null);
      setAnalysisJob(null);
      setWorkerRun(null);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Save analyzed item failed");
    } finally {
      setSavingDraft(false);
    }
  }

  function updateDraft<K extends keyof DraftFormState>(field: K, value: DraftFormState[K]) {
    setDraft((current) => (current ? { ...current, [field]: value } : current));
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(item) => item.id}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      contentContainerStyle={styles.list}
      ListHeaderComponent={
        <View style={styles.headerContent}>
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
              {quickCategoryOptions.map((category) => (
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
                label="AI 분석"
                icon="upload"
                tone="secondary"
                onPress={startAnalysisJob}
                loading={analyzing}
                style={styles.flexAction}
              />
            </View>
            {analysisJob ? (
              <View style={styles.jobSummary}>
                <Text style={styles.jobStatus}>
                  job {analysisJob.jobId.slice(0, 8)} / {analysisJob.status} / {analysisJob.progress}%
                </Text>
                {workerRun ? <Text style={styles.jobStatus}>worker: {workerRun.reason}</Text> : null}
              </View>
            ) : null}
          </View>

          {draft ? (
            <View style={styles.reviewPanel}>
              <View style={styles.reviewHeader}>
                <View>
                  <Text style={styles.panelTitle}>AI 분석 검토</Text>
                  <Text style={styles.helperText}>quality {Math.round(draft.qualityScore * 100)}%</Text>
                </View>
                <Feather name="edit-3" size={20} color={colors.ink} />
              </View>
              <View style={styles.illustrationBox}>
                <Feather name="image" size={20} color={colors.green} />
                <Text style={styles.illustrationText} numberOfLines={1}>
                  {draft.illustrationStorageKey}
                </Text>
              </View>
              <TextInput
                value={draft.name}
                onChangeText={(value) => updateDraft("name", value)}
                style={styles.input}
                placeholder="이름"
                placeholderTextColor={colors.muted}
              />
              <View style={styles.fieldRow}>
                <TextInput
                  value={draft.subType}
                  onChangeText={(value) => updateDraft("subType", value)}
                  style={styles.input}
                  placeholder="세부 종류"
                  placeholderTextColor={colors.muted}
                />
                <TextInput
                  value={draft.colorsText}
                  onChangeText={(value) => updateDraft("colorsText", value)}
                  style={styles.input}
                  placeholder="색상"
                  placeholderTextColor={colors.muted}
                />
              </View>
              <View style={styles.categoryRow}>
                {categoryOptions.map((category) => (
                  <Text
                    key={category}
                    onPress={() => updateDraft("category", category)}
                    style={[styles.categoryChip, draft.category === category && styles.categoryChipActive]}
                  >
                    {category}
                  </Text>
                ))}
              </View>
              <View style={styles.fieldRow}>
                <TextInput
                  value={draft.styleTagsText}
                  onChangeText={(value) => updateDraft("styleTagsText", value)}
                  style={styles.input}
                  placeholder="태그: minimal, workwear"
                  placeholderTextColor={colors.muted}
                />
                <TextInput
                  value={draft.seasonsText}
                  onChangeText={(value) => updateDraft("seasonsText", value)}
                  style={styles.inputCompact}
                  placeholder="계절"
                  placeholderTextColor={colors.muted}
                />
              </View>
              <View style={styles.segmentGroup}>
                <Text style={styles.segmentLabel}>두께</Text>
                <View style={styles.categoryRow}>
                  {thicknessOptions.map((thickness) => (
                    <Text
                      key={thickness}
                      onPress={() => updateDraft("thickness", thickness)}
                      style={[styles.categoryChip, draft.thickness === thickness && styles.categoryChipActive]}
                    >
                      {thickness}
                    </Text>
                  ))}
                </View>
              </View>
              <View style={styles.segmentGroup}>
                <Text style={styles.segmentLabel}>분위기</Text>
                <View style={styles.categoryRow}>
                  {formalityOptions.map((formality) => (
                    <Text
                      key={formality}
                      onPress={() => updateDraft("formality", formality)}
                      style={[styles.categoryChip, draft.formality === formality && styles.categoryChipActive]}
                    >
                      {formality}
                    </Text>
                  ))}
                </View>
              </View>
              <View style={styles.fieldRow}>
                <TextInput
                  value={draft.warmthText}
                  onChangeText={(value) => updateDraft("warmthText", value)}
                  keyboardType="number-pad"
                  style={styles.input}
                  placeholder="보온"
                  placeholderTextColor={colors.muted}
                />
                <TextInput
                  value={draft.breathabilityText}
                  onChangeText={(value) => updateDraft("breathabilityText", value)}
                  keyboardType="number-pad"
                  style={styles.input}
                  placeholder="통기"
                  placeholderTextColor={colors.muted}
                />
                <Text
                  onPress={() => updateDraft("rainSafe", !draft.rainSafe)}
                  style={[styles.rainToggle, draft.rainSafe && styles.categoryChipActive]}
                >
                  rain
                </Text>
              </View>
              <View style={styles.actionRow}>
                <ActionButton
                  label="초안 저장"
                  icon="check"
                  onPress={saveAnalyzedDraft}
                  loading={savingDraft}
                  style={styles.flexAction}
                />
                <ActionButton
                  label="초안 닫기"
                  icon="x"
                  tone="secondary"
                  onPress={() => setDraft(null)}
                  disabled={savingDraft}
                  style={styles.flexAction}
                />
              </View>
            </View>
          ) : null}

          {notice ? <Text style={styles.notice}>{notice}</Text> : null}
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

async function processAnalysisQueueForJob(jobId: string) {
  let lastRun = await fitlogApi.processNextAnalysisJob();
  let attempts = 1;

  while (lastRun.processed && lastRun.jobId !== jobId && attempts < 5) {
    lastRun = await fitlogApi.processNextAnalysisJob();
    attempts += 1;
  }

  return lastRun;
}

function toDraftFormState(
  result: ImageAnalysisResult,
  fallbackName: string,
  fallbackCategory: Category,
  fallbackColor: string
): DraftFormState {
  const draft = result.closetItemDraft ?? fallbackDraft(fallbackName, fallbackCategory, fallbackColor);
  return {
    jobId: result.source.jobId,
    illustrationStorageKey: result.illustration.storageKey,
    qualityScore: result.quality.score,
    name: draft.name,
    category: draft.category,
    subType: draft.subType,
    colorsText: draft.colors.join(", "),
    styleTagsText: draft.styleTags.join(", "),
    seasonsText: draft.seasons.join(", "),
    thickness: draft.thickness,
    formality: draft.formality,
    status: draft.status,
    rainSafe: draft.rainSafe,
    warmthText: String(draft.warmth),
    breathabilityText: String(draft.breathability)
  };
}

function fallbackDraft(name: string, category: Category, color: string): AnalyzedClosetItemDraft {
  return {
    name,
    category,
    subType: defaultSubType(category),
    seasons: ["all"],
    styleTags: ["daily"],
    colors: [color],
    thickness: "medium",
    formality: "casual",
    status: "available",
    warmth: 5,
    rainSafe: false,
    breathability: 6
  };
}

function toCreateRequest(draft: DraftFormState): ClosetItemCreateRequest {
  return {
    id: uniqueItemId(draft.name || draft.jobId),
    name: draft.name.trim() || "Analyzed item",
    category: draft.category,
    subType: draft.subType.trim() || defaultSubType(draft.category),
    seasons: parseSeasons(draft.seasonsText),
    styleTags: parseRequiredList(draft.styleTagsText, ["daily"]),
    colors: parseRequiredList(draft.colorsText, ["neutral"]),
    thickness: draft.thickness,
    formality: draft.formality,
    status: draft.status,
    warmth: clampScore(draft.warmthText, 5),
    rainSafe: draft.rainSafe,
    breathability: clampScore(draft.breathabilityText, 6)
  };
}

function parseList(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseRequiredList(value: string, fallback: string[]) {
  const parsed = parseList(value);
  return parsed.length ? parsed : fallback;
}

function parseSeasons(value: string): Season[] {
  const allowed: Season[] = ["spring", "summer", "fall", "winter", "all"];
  const seasons = parseList(value).filter((item): item is Season => allowed.includes(item as Season));
  return seasons.length ? seasons : ["all"];
}

function clampScore(value: string, fallback: number) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) {
    return fallback;
  }
  return Math.min(10, Math.max(1, parsed));
}

function uniqueItemId(value: string) {
  const base = slugify(value) || "closet-item";
  return `${base}-${Date.now()}`;
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
    case "dress":
      return "dress";
    case "bag":
      return "bag";
    case "accessory":
      return "accessory";
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
  headerContent: {
    gap: spacing.md
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between"
  },
  creationPanel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 8,
    padding: spacing.md,
    gap: spacing.sm
  },
  reviewPanel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 8,
    padding: spacing.md,
    gap: spacing.sm
  },
  reviewHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between"
  },
  panelTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: "900"
  },
  helperText: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
    marginTop: 2
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
    width: 92,
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
  segmentGroup: {
    gap: spacing.xs
  },
  segmentLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "800"
  },
  actionRow: {
    flexDirection: "row",
    gap: spacing.sm
  },
  flexAction: {
    flex: 1
  },
  jobSummary: {
    gap: spacing.xs
  },
  jobStatus: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "800"
  },
  illustrationBox: {
    minHeight: 42,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surfaceAlt,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingHorizontal: spacing.md
  },
  illustrationText: {
    flex: 1,
    color: colors.ink,
    fontSize: 12,
    fontWeight: "800"
  },
  rainToggle: {
    minWidth: 72,
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    color: colors.muted,
    fontSize: 12,
    fontWeight: "900",
    textAlign: "center",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md
  },
  notice: {
    color: colors.green,
    fontSize: 13,
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
