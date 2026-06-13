import { useCallback, useEffect, useState } from "react";
import { FlatList, Image, RefreshControl, StyleSheet, Text, TextInput, View } from "react-native";
import { Feather } from "@expo/vector-icons";
import * as ImageManipulator from "expo-image-manipulator";
import * as ImagePicker from "expo-image-picker";

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
  RuntimeReadiness,
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
  demo: boolean;
  jobId: string;
  illustrationStorageKey: string;
  qualityUsable: boolean;
  qualityScore: number;
  qualityIssues: string[];
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

type ImageSource = "library" | "camera";

const categoryOptions: Category[] = ["top", "bottom", "outerwear", "dress", "shoes", "bag", "accessory"];
const quickCategoryOptions: Category[] = ["top", "bottom", "shoes", "outerwear"];
const thicknessOptions: Thickness[] = ["light", "medium", "heavy"];
const formalityOptions: Formality[] = ["casual", "business_casual", "formal"];

export function ClosetScreen() {
  const [items, setItems] = useState<ClosetItem[]>([]);
  const [readiness, setReadiness] = useState<RuntimeReadiness | null>(null);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [normalizingImage, setNormalizingImage] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [newItemName, setNewItemName] = useState("White shirt");
  const [newItemCategory, setNewItemCategory] = useState<Category>("top");
  const [newItemColor, setNewItemColor] = useState("white");
  const [selectedImage, setSelectedImage] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [selectedImageSource, setSelectedImageSource] = useState<ImageSource | null>(null);
  const [analysisJob, setAnalysisJob] = useState<AnalysisJobResponse | null>(null);
  const [workerRun, setWorkerRun] = useState<WorkerRunResponse | null>(null);
  const [draft, setDraft] = useState<DraftFormState | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [closetItems, runtimeReadiness] = await Promise.all([
        fitlogApi.listClosetItems(),
        fitlogApi.runtimeReadiness()
      ]);
      setItems(closetItems);
      setReadiness(runtimeReadiness);
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
    if (!selectedImage) {
      setError("먼저 분석할 옷 사진을 선택해주세요.");
      return;
    }

    setAnalyzing(true);
    setError(null);
    setNotice(null);
    setDraft(null);
    setWorkerRun(null);
    try {
      const contentType = selectedImage.mimeType ?? inferImageContentType(selectedImage.fileName ?? "");
      const fileName = buildUploadFileName(newItemName, newItemCategory, newItemColor, contentType);
      const ticket = await fitlogApi.createUploadTicket({
        fileName,
        contentType,
        byteSize: selectedImage.fileSize && selectedImage.fileSize > 0 ? selectedImage.fileSize : undefined
      });
      setNotice("사진을 업로드하고 있어요.");
      await fitlogApi.uploadFile(ticket.uploadUrl, selectedImage.uri, contentType);
      setNotice("사진 분석 작업을 만들고 있어요.");
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
      setNotice(
        processed.result.provider === "fitlog_demo"
          ? "입력한 정보로 무료 데모 초안을 만들었어요. 확인 후 저장하세요."
          : processed.result.quality.usable
          ? "자동 분석 초안을 만들었어요. 확인 후 저장하세요."
          : "사진 품질을 확인해주세요. 재촬영하거나 검토 후 저장할 수 있어요."
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Image analysis job failed");
    } finally {
      setAnalyzing(false);
    }
  }

  async function pickImage() {
    setError(null);
    setNotice(null);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.85
      });

      if (result.canceled) {
        return;
      }

      await acceptImage(result.assets[0], "library");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "사진을 불러오지 못했어요.");
    }
  }

  async function captureImage() {
    setCapturing(true);
    setError(null);
    setNotice(null);
    try {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        setError(
          permission.canAskAgain
            ? "옷 사진을 촬영하려면 카메라 권한이 필요해요."
            : "카메라 권한이 꺼져 있어요. 기기 설정에서 Fitlog의 카메라 권한을 허용해주세요."
        );
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ["images"],
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.85
      });

      if (result.canceled) {
        return;
      }

      await acceptImage(result.assets[0], "camera");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "사진 촬영을 시작하지 못했어요.");
    } finally {
      setCapturing(false);
    }
  }

  async function acceptImage(asset: ImagePicker.ImagePickerAsset, source: ImageSource) {
    setNormalizingImage(true);
    setNotice("분석할 수 있는 이미지 형식으로 준비하고 있어요.");
    try {
      const normalizedAsset = await normalizeImageForAnalysis(asset);
      setSelectedImage(normalizedAsset);
      setSelectedImageSource(source);
      setAnalysisJob(null);
      setWorkerRun(null);
      setDraft(null);
      setNotice(
        source === "camera"
          ? "사진을 촬영했어요. 데모 초안을 만들어보세요."
          : "사진을 선택했어요. 데모 초안을 만들어보세요."
      );
    } finally {
      setNormalizingImage(false);
    }
  }

  async function saveAnalyzedDraft(allowLowQuality = false) {
    if (!draft) {
      return;
    }
    if (!draft.demo && !draft.qualityUsable && !allowLowQuality) {
      setError("품질이 낮은 사진이에요. 재촬영하거나 '그래도 저장'을 선택해주세요.");
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
      setSelectedImage(null);
      setSelectedImageSource(null);
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
            {!readiness?.imageAnalysis.live ? (
              <View style={styles.demoNotice}>
                <Feather name="info" size={18} color={colors.green} />
                <Text style={styles.demoNoticeText}>
                  무료 데모는 사진을 보관하고, 아래에 입력한 이름·종류·색상으로 수정 가능한 초안을 만듭니다.
                </Text>
              </View>
            ) : null}
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
            {selectedImage ? (
              <View style={styles.selectedImagePanel}>
                <Image source={{ uri: selectedImage.uri }} style={styles.selectedImage} resizeMode="cover" />
                <View style={styles.selectedImageMeta}>
                  <Text style={styles.selectedImageName} numberOfLines={1}>
                    {selectedImage.fileName ?? "selected-image.jpg"}
                  </Text>
                  <Text style={styles.helperText}>
                    {selectedImageSource === "camera" ? "촬영" : "갤러리"} / {selectedImage.width} x {selectedImage.height}
                    {selectedImage.fileSize ? ` / ${formatFileSize(selectedImage.fileSize)}` : ""}
                  </Text>
                </View>
              </View>
            ) : null}
            <View style={styles.actionRow}>
              <ActionButton
                label="갤러리"
                icon="image"
                tone="secondary"
                onPress={pickImage}
                disabled={analyzing || capturing || normalizingImage}
                style={styles.flexAction}
              />
              <ActionButton
                label="촬영"
                icon="camera"
                tone="secondary"
                onPress={captureImage}
                loading={capturing}
                disabled={analyzing || normalizingImage}
                style={styles.flexAction}
              />
            </View>
            <ActionButton
              label={readiness?.imageAnalysis.live ? "AI 자동 분석" : "무료 데모 초안"}
              icon="upload"
              onPress={startAnalysisJob}
              loading={analyzing}
              disabled={!selectedImage || capturing || normalizingImage}
            />
            <ActionButton
              label="직접 입력으로 저장"
              icon="plus"
              tone="secondary"
              onPress={createItem}
              loading={creating}
              disabled={analyzing || capturing || normalizingImage}
            />
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
                  <Text style={styles.panelTitle}>{draft.demo ? "데모 초안 검토" : "AI 분석 검토"}</Text>
                  <Text style={styles.helperText}>
                    {draft.demo
                      ? "입력값 기반 / 저장 전 자유롭게 수정 가능"
                      : `품질 ${Math.round(draft.qualityScore * 100)}% / ${draft.qualityUsable ? "사용 가능" : "재촬영 권장"}`}
                  </Text>
                </View>
                <Feather name="edit-3" size={20} color={colors.ink} />
              </View>
              {!draft.demo && !draft.qualityUsable ? (
                <View style={styles.qualityWarning}>
                  <Feather name="alert-triangle" size={20} color={colors.danger} />
                  <View style={styles.qualityWarningBody}>
                    <Text style={styles.qualityWarningTitle}>사진을 다시 찍으면 분석 정확도가 좋아져요</Text>
                    {draft.qualityIssues.map((issue) => (
                      <Text key={issue} style={styles.qualityIssueText}>
                        {qualityIssueLabel(issue)}
                      </Text>
                    ))}
                  </View>
                </View>
              ) : null}
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
              {!draft.demo && !draft.qualityUsable ? (
                <>
                  <View style={styles.actionRow}>
                    <ActionButton
                      label="재촬영"
                      icon="camera"
                      onPress={captureImage}
                      loading={capturing}
                      disabled={savingDraft || normalizingImage}
                      style={styles.flexAction}
                    />
                    <ActionButton
                      label="다른 사진"
                      icon="image"
                      tone="secondary"
                      onPress={pickImage}
                      disabled={savingDraft || capturing || normalizingImage}
                      style={styles.flexAction}
                    />
                  </View>
                  <View style={styles.actionRow}>
                    <ActionButton
                      label="그래도 저장"
                      icon="alert-triangle"
                      tone="danger"
                      onPress={() => void saveAnalyzedDraft(true)}
                      loading={savingDraft}
                      disabled={capturing}
                      style={styles.flexAction}
                    />
                    <ActionButton
                      label="초안 닫기"
                      icon="x"
                      tone="secondary"
                      onPress={() => setDraft(null)}
                      disabled={savingDraft || capturing}
                      style={styles.flexAction}
                    />
                  </View>
                </>
              ) : (
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
              )}
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
  const demo = result.provider === "fitlog_demo";
  const draft = demo
    ? fallbackDraft(fallbackName, fallbackCategory, fallbackColor)
    : result.closetItemDraft ?? fallbackDraft(fallbackName, fallbackCategory, fallbackColor);
  return {
    demo,
    jobId: result.source.jobId,
    illustrationStorageKey: result.illustration.storageKey,
    qualityUsable: result.quality.usable,
    qualityScore: result.quality.score,
    qualityIssues: result.quality.issues,
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

function qualityIssueLabel(issue: string) {
  switch (issue) {
    case "blur_detected":
      return "사진이 흔들리거나 초점이 흐려요.";
    case "low_light":
      return "조명이 어두워 옷의 색과 디테일이 잘 보이지 않아요.";
    case "low_resolution":
      return "사진 해상도가 낮아 옷의 특징을 확인하기 어려워요.";
    case "item_occluded":
      return "옷 일부가 가려져 있어 전체 형태를 확인하기 어려워요.";
    case "multiple_items":
      return "한 번에 옷 한 벌만 보이도록 촬영해주세요.";
    case "not_clothing":
      return "의류가 명확하게 보이는 사진을 선택해주세요.";
    case "poor_framing":
      return "옷 전체가 화면 안에 들어오도록 다시 촬영해주세요.";
    default:
      return "옷 전체가 잘 보이도록 밝은 곳에서 다시 촬영해주세요.";
  }
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

function buildUploadFileName(name: string, category: Category, color: string, contentType: string) {
  const base = slugify(`${color}-${category}-${name}`) || "closet-item";
  return `${base}.${extensionForContentType(contentType)}`;
}

function inferImageContentType(fileName: string) {
  const extension = fileName.split(".").pop()?.toLowerCase();
  if (extension === "png") {
    return "image/png";
  }
  if (extension === "webp") {
    return "image/webp";
  }
  if (extension === "heic" || extension === "heif") {
    return "image/heic";
  }
  return "image/jpeg";
}

async function normalizeImageForAnalysis(
  asset: ImagePicker.ImagePickerAsset
): Promise<ImagePicker.ImagePickerAsset> {
  const contentType = asset.mimeType ?? inferImageContentType(asset.fileName ?? "");
  if (isVisionSupportedContentType(contentType)) {
    return asset;
  }

  const context = ImageManipulator.ImageManipulator.manipulate(asset.uri);
  const image = await context.renderAsync();
  const normalized = await image.saveAsync({
    compress: 0.9,
    format: ImageManipulator.SaveFormat.JPEG
  });

  return {
    ...asset,
    uri: normalized.uri,
    width: normalized.width,
    height: normalized.height,
    fileName: replaceFileExtension(asset.fileName ?? "fitlog-photo", "jpg"),
    fileSize: undefined,
    mimeType: "image/jpeg"
  };
}

function isVisionSupportedContentType(contentType: string) {
  return ["image/jpeg", "image/png", "image/webp", "image/gif"].includes(contentType.toLowerCase());
}

function replaceFileExtension(fileName: string, extension: string) {
  const base = fileName.replace(/\.[^.]+$/, "") || "fitlog-photo";
  return `${base}.${extension}`;
}

function extensionForContentType(contentType: string) {
  if (contentType === "image/png") {
    return "png";
  }
  if (contentType === "image/webp") {
    return "webp";
  }
  if (contentType === "image/heic" || contentType === "image/heif") {
    return "heic";
  }
  return "jpg";
}

function formatFileSize(byteSize: number) {
  if (byteSize < 1024 * 1024) {
    return `${Math.max(1, Math.round(byteSize / 1024))} KB`;
  }
  return `${(byteSize / (1024 * 1024)).toFixed(1)} MB`;
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
  demoNotice: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.sm,
    backgroundColor: colors.surfaceAlt,
    borderRadius: 8,
    padding: spacing.md
  },
  demoNoticeText: {
    color: colors.text,
    flex: 1,
    fontSize: 13,
    fontWeight: "700",
    lineHeight: 19
  },
  selectedImagePanel: {
    minHeight: 104,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
    padding: spacing.sm
  },
  selectedImage: {
    width: 88,
    height: 88,
    borderRadius: 8,
    backgroundColor: colors.surfaceAlt
  },
  selectedImageMeta: {
    flex: 1,
    gap: spacing.xs
  },
  selectedImageName: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "900"
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
  qualityWarning: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.sm,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.danger,
    backgroundColor: "#FFF4F3",
    padding: spacing.md
  },
  qualityWarningBody: {
    flex: 1,
    gap: spacing.xs
  },
  qualityWarningTitle: {
    color: colors.danger,
    fontSize: 13,
    fontWeight: "900"
  },
  qualityIssueText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: "700"
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
