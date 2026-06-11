import * as FileSystem from "expo-file-system";
import { Platform } from "react-native";

import type {
  AnalysisJobResponse,
  ClosetItem,
  ClosetItemCreateRequest,
  MorningRunResponse,
  NotificationSettings,
  RecommendationFeedbackRequest,
  RecommendationRequest,
  RecommendationResponse,
  UploadCompletionResponse,
  UploadUrlResponse,
  WorkerRunResponse
} from "./types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? DEFAULT_API_BASE_URL;

const API_ORIGIN = API_BASE_URL.endsWith("/api/v1") ? API_BASE_URL.slice(0, -7) : API_BASE_URL;

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

async function uploadFile(
  uploadUrl: string,
  fileUri: string,
  contentType: string
): Promise<UploadCompletionResponse> {
  const resolvedUrl = resolveUploadUrl(uploadUrl);

  if (Platform.OS === "web") {
    const fileResponse = await fetch(fileUri);
    const body = await fileResponse.blob();
    const response = await fetch(resolvedUrl, {
      method: "PUT",
      headers: { "Content-Type": contentType },
      body
    });
    if (!response.ok) {
      throw new Error((await response.text()) || `Upload failed with ${response.status}`);
    }
    return response.json() as Promise<UploadCompletionResponse>;
  }

  const response = await FileSystem.uploadAsync(resolvedUrl, fileUri, {
    httpMethod: "PUT",
    headers: { "Content-Type": contentType },
    uploadType: FileSystem.FileSystemUploadType.BINARY_CONTENT
  });
  if (response.status < 200 || response.status >= 300) {
    throw new Error(response.body || `Upload failed with ${response.status}`);
  }
  return JSON.parse(response.body) as UploadCompletionResponse;
}

function resolveUploadUrl(uploadUrl: string) {
  if (/^https?:\/\//.test(uploadUrl)) {
    return uploadUrl;
  }
  return `${API_ORIGIN}${uploadUrl.startsWith("/") ? "" : "/"}${uploadUrl}`;
}

export const fitlogApi = {
  health: () => request<{ service: string; status: string; version: string }>("/health"),
  listClosetItems: () => request<ClosetItem[]>("/closet-items"),
  createClosetItem: (payload: ClosetItemCreateRequest) =>
    request<ClosetItem>("/closet-items", {
      method: "POST",
      body: payload
    }),
  createUploadTicket: (payload: { fileName: string; contentType: string; byteSize?: number }) =>
    request<UploadUrlResponse>("/closet-items/uploads", {
      method: "POST",
      body: payload
    }),
  uploadFile,
  createAnalysisJob: (payload: { uploadId: string; requestedOperations?: string[] }) =>
    request<AnalysisJobResponse>("/closet-items/analyze", {
      method: "POST",
      body: payload
    }),
  processNextAnalysisJob: () =>
    request<WorkerRunResponse>("/closet-items/jobs/process-next", {
      method: "POST"
    }),
  getAnalysisJob: (jobId: string) => request<AnalysisJobResponse>(`/closet-items/jobs/${jobId}`),
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
  addRecommendationFeedback: (recommendationId: string, payload: RecommendationFeedbackRequest) =>
    request<{ feedbackId: string; recommendationId: string; feedbackType: string }>(
      `/recommendations/${recommendationId}/feedback`,
      {
        method: "POST",
        body: payload
      }
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
