export type Category = "top" | "bottom" | "outerwear" | "dress" | "shoes" | "bag" | "accessory";
export type Formality = "casual" | "business_casual" | "formal";
export type ItemStatus = "available" | "laundry" | "repair" | "storage" | "sell_or_donate";
export type Season = "spring" | "summer" | "fall" | "winter" | "all";

export type ClosetItem = {
  id: string;
  name: string;
  category: Category;
  subType: string;
  seasons: Season[];
  styleTags: string[];
  colors: string[];
  thickness: "light" | "medium" | "heavy";
  formality: Formality;
  status: ItemStatus;
  warmth: number;
  rainSafe: boolean;
  breathability: number;
  wearCount: number;
  lastWornDaysAgo: number | null;
};

export type ClosetItemCreateRequest = {
  id: string;
  name: string;
  category: Category;
  subType: string;
  seasons: Season[];
  styleTags?: string[];
  colors?: string[];
  thickness?: "light" | "medium" | "heavy";
  formality?: Formality;
  status?: ItemStatus;
  warmth?: number;
  rainSafe?: boolean;
  breathability?: number;
};

export type OutfitItem = {
  id: string;
  name: string;
  category: Category;
  subType: string;
  colors: string[];
  styleTags: string[];
};

export type OutfitCandidate = {
  itemIds: string[];
  score: number;
  reasons: string[];
  items: OutfitItem[];
};

export type RecommendationResponse = {
  recommendationId: string | null;
  status: "candidate" | "saved" | "worn" | "dismissed" | null;
  candidates: OutfitCandidate[];
  createdAt: string | null;
  updatedAt: string | null;
};

export type RecommendationFeedbackRequest = {
  feedbackType: "liked" | "disliked" | "too_hot" | "too_cold" | "too_flashy";
  note?: string;
};

export type WeatherPayload = {
  temperatureC: number;
  feelsLikeC: number;
  precipitationProbability: number;
  precipitationType: "none" | "rain" | "snow";
};

export type RecommendationRequest = {
  weather: WeatherPayload;
  styleRequest: {
    occasion?: string;
    moodTags?: string[];
    formality?: Formality;
    trendLevel?: "basic" | "balanced" | "experimental";
  };
  limit?: number;
  useDemoCloset?: boolean;
};

export type NotificationSettings = {
  id: string;
  enabled: boolean;
  timezone: string;
  weekdayNotificationTime: string;
  weekendNotificationTime: string | null;
  locationLabel: string | null;
  latitude: number | null;
  longitude: number | null;
  updatedAt: string;
};

export type MorningRunResponse = {
  created: boolean;
  reason: string;
  runId: string | null;
  runDate: string | null;
  recommendationId: string | null;
  weatherSource: "provided" | "fallback";
  pushDispatch: {
    dispatchId: string;
    recommendationId: string;
    status: "queued" | "sent" | "failed";
    title: string;
    body: string;
    provider: string;
    createdAt: string;
  } | null;
};

export type UploadUrlResponse = {
  uploadId: string;
  uploadUrl: string;
  method: "PUT";
  storageKey: string;
  expiresAt: string;
  headers: Record<string, string>;
};

export type AnalysisJobResponse = {
  jobId: string;
  type: "closet_item_analysis";
  status: "queued" | "running" | "needs_user_review" | "succeeded" | "failed" | "canceled";
  progress: number;
  uploadId: string;
  storageKey: string;
  originalFileName: string;
  contentType: string;
  requestedOperations: string[];
  result: Record<string, unknown> | null;
  error: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  workerEvent?: {
    eventType: "image.uploaded";
    jobId: string;
    uploadId: string;
    storageKey: string;
    requestedOperations: string[];
  } | null;
};
