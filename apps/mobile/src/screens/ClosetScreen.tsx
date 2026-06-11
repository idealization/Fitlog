import { useCallback, useEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { fitlogApi } from "../api/client";
import type { ClosetItem } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { ItemPill } from "../components/ItemPill";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

export function ClosetScreen() {
  const [items, setItems] = useState<ClosetItem[]>([]);
  const [loading, setLoading] = useState(false);
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
      }
      ListEmptyComponent={
        <EmptyState icon="archive" title="등록된 의류가 없습니다" body="새 아이템을 추가하면 옷장이 채워집니다." />
      }
      renderItem={({ item }) => <ClosetItemRow item={item} />}
      ListFooterComponent={error ? <Text style={styles.error}>{error}</Text> : null}
    />
  );
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
