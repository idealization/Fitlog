import { useCallback, useEffect, useState } from "react";
import { ScrollView, StyleSheet, Switch, Text, TextInput, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { API_BASE_URL, fitlogApi } from "../api/client";
import type { NotificationSettings, RuntimeReadiness } from "../api/types";
import { ActionButton } from "../components/ActionButton";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

export function SettingsScreen() {
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [readiness, setReadiness] = useState<RuntimeReadiness | null>(null);
  const [weekdayTime, setWeekdayTime] = useState("08:00");
  const [weekendTime, setWeekendTime] = useState("09:00");
  const [timezone, setTimezone] = useState("Asia/Seoul");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [response, runtimeReadiness] = await Promise.all([
        fitlogApi.getNotificationSettings(),
        fitlogApi.runtimeReadiness()
      ]);
      setSettings(response);
      setReadiness(runtimeReadiness);
      setWeekdayTime(response.weekdayNotificationTime);
      setWeekendTime(response.weekendNotificationTime ?? "09:00");
      setTimezone(response.timezone);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Settings request failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function save() {
    setLoading(true);
    setError(null);
    try {
      setSettings(
        await fitlogApi.updateNotificationSettings({
          enabled: settings?.enabled ?? true,
          timezone,
          weekdayNotificationTime: weekdayTime,
          weekendNotificationTime: weekendTime
        })
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Settings save failed");
    } finally {
      setLoading(false);
    }
  }

  async function toggle(enabled: boolean) {
    setSettings((current) => (current ? { ...current, enabled } : current));
    try {
      setSettings(await fitlogApi.updateNotificationSettings({ enabled }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Settings save failed");
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.panel}>
        <View style={styles.titleRow}>
          <Feather name="bell" size={20} color={colors.gold} />
          <Text style={styles.title}>아침 알림</Text>
        </View>
        <View style={styles.switchRow}>
          <View>
            <Text style={styles.label}>활성화</Text>
            <Text style={styles.value}>{settings?.enabled ? "on" : "off"}</Text>
          </View>
          <Switch
            value={settings?.enabled ?? false}
            onValueChange={toggle}
            trackColor={{ false: colors.border, true: colors.green }}
            thumbColor={colors.surface}
          />
        </View>

        <Field label="평일" value={weekdayTime} onChangeText={setWeekdayTime} />
        <Field label="주말" value={weekendTime} onChangeText={setWeekendTime} />
        <Field label="시간대" value={timezone} onChangeText={setTimezone} />

        <ActionButton label="저장" icon="save" onPress={save} loading={loading} />
      </View>
      <View style={styles.panel}>
        <View style={styles.titleRow}>
          <Feather name="activity" size={20} color={colors.green} />
          <Text style={styles.title}>서비스 상태</Text>
        </View>
        <StatusRow label="API" value={readiness?.apiStatus === "ok" ? "연결됨" : "확인 중"} />
        <StatusRow label="분석 모드" value={readiness?.imageAnalysis.live ? "OpenAI 실분석" : "로컬 데모"} />
        <StatusRow label="분석 모델" value={readiness?.imageAnalysis.model ?? "-"} />
        <StatusRow label="데이터" value={readiness?.repositoryBackend ?? "-"} />
        <Text style={styles.endpoint} numberOfLines={2}>{API_BASE_URL}</Text>
        <ActionButton label="연결 다시 확인" icon="refresh-cw" onPress={load} loading={loading} tone="secondary" />
      </View>
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </ScrollView>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.statusRow}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.statusValue}>{value}</Text>
    </View>
  );
}

function Field({
  label,
  value,
  onChangeText
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput value={value} onChangeText={onChangeText} style={styles.input} />
    </View>
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
  panel: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    gap: spacing.md
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm
  },
  title: {
    color: colors.text,
    fontSize: 20,
    fontWeight: "900"
  },
  switchRow: {
    minHeight: 58,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottomColor: colors.border,
    borderBottomWidth: 1
  },
  field: {
    gap: spacing.xs
  },
  label: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "800"
  },
  value: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "800",
    marginTop: 2
  },
  statusRow: {
    minHeight: 36,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.md,
    borderBottomColor: colors.border,
    borderBottomWidth: 1
  },
  statusValue: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "800",
    textAlign: "right",
    flexShrink: 1
  },
  endpoint: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18
  },
  input: {
    minHeight: 44,
    borderRadius: 8,
    borderColor: colors.border,
    borderWidth: 1,
    color: colors.text,
    paddingHorizontal: spacing.md,
    fontWeight: "800",
    backgroundColor: colors.background
  },
  error: {
    color: colors.danger,
    fontWeight: "700"
  }
});
