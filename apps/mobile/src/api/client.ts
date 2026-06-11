import type {
  ClosetItem,
  MorningRunResponse,
  NotificationSettings,
  RecommendationRequest,
  RecommendationResponse
} from "./types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? DEFAULT_API_BASE_URL;

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json"
    },
    body: options.body ? JSON.stringify(options.body) : undefined
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const fitlogApi = {
  health: () => request<{ service: string; status: string; version: string }>("/health"),
  listClosetItems: () => request<ClosetItem[]>("/closet-items"),
  createRecommendation: (payload: RecommendationRequest) =>
    request<RecommendationResponse>("/recommendations", {
      method: "POST",
      body: payload
    }),
  getRecommendation: (recommendationId: string) =>
    request<RecommendationResponse>(`/recommendations/${recommendationId}`),
  saveRecommendation: (recommendationId: string) =>
    request<RecommendationResponse>(`/recommendations/${recommendationId}/save`, {
      method: "POST"
    }),
  markRecommendationWorn: (recommendationId: string) =>
    request<{ wearLogId: string; recommendationId: string; itemIds: string[] }>(
      `/recommendations/${recommendationId}/wear`,
      { method: "POST" }
    ),
  getNotificationSettings: () => request<NotificationSettings>("/notification-settings"),
  updateNotificationSettings: (payload: Partial<NotificationSettings>) =>
    request<NotificationSettings>("/notification-settings", {
      method: "PATCH",
      body: payload
    }),
  runMorningRecommendation: () =>
    request<MorningRunResponse>("/morning-recommendations/run-due", {
      method: "POST",
      body: {}
    })
};

