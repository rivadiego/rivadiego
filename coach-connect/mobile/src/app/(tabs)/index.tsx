import * as Haptics from 'expo-haptics';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, RefreshControl, SectionList, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

import { ActivityCard } from '@/components/activity-card';
import { NoticeBanner, type Notice } from '@/components/notice-banner';
import { StateView } from '@/components/state-view';
import { SyncButton } from '@/components/sync-button';
import { colors, maxContentWidth, radius, spacing } from '@/constants/theme';
import { useNow } from '@/hooks/use-now';
import { api, describeError, type Activity, type ActivityPage } from '@/lib/api';
import { formatMonth, formatRelative, monthKey } from '@/lib/format';

const PAGE_SIZE = 50;

type SyncTrigger = 'button' | 'pull';

function ItemSeparator() {
  return <View style={styles.separator} />;
}

export default function ActivitiesScreen() {
  const insets = useSafeAreaInsets();
  const now = useNow(30_000);
  const [page, setPage] = useState<Omit<ActivityPage, 'items' | 'limit' | 'offset'> | null>(null);
  const [items, setItems] = useState<Activity[]>([]);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [syncing, setSyncing] = useState<SyncTrigger | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);

  const applyFirstPage = useCallback((result: ActivityPage) => {
    setItems(result.items);
    setPage({ total: result.total, mode: result.mode, last_sync_at: result.last_sync_at });
    setLoadError(null);
  }, []);

  const loadFirstPage = useCallback(
    async () => applyFirstPage(await api.activities(0, PAGE_SIZE)),
    [applyFirstPage],
  );

  const retryLoad = useCallback(() => {
    setLoadError(null);
    setPage(null);
    loadFirstPage().catch(setLoadError);
  }, [loadFirstPage]);

  useEffect(() => {
    let active = true;
    api
      .activities(0, PAGE_SIZE)
      .then((result) => active && applyFirstPage(result))
      .catch((error: unknown) => active && setLoadError(error));
    return () => {
      active = false;
    };
  }, [applyFirstPage]);

  useEffect(() => {
    if (!notice || notice.tone === 'error') {
      return;
    }
    const timer = setTimeout(() => setNotice(null), 3500);
    return () => clearTimeout(timer);
  }, [notice]);

  const sync = useCallback(
    async (trigger: SyncTrigger) => {
      if (syncing) {
        return;
      }
      setSyncing(trigger);
      setNotice(null);
      try {
        const result = await api.sync();
        await loadFirstPage();
        setNotice(
          result.new > 0
            ? { tone: 'success', title: result.new === 1 ? '1 nuova attività' : `${result.new} nuove attività` }
            : { tone: 'info', title: 'Già tutto aggiornato' },
        );
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      } catch (error) {
        setNotice({ tone: 'error', ...describeError(error) });
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
      } finally {
        setSyncing(null);
      }
    },
    [syncing, loadFirstPage],
  );

  const loadMore = useCallback(async () => {
    if (loadingMore || !page || items.length >= page.total) {
      return;
    }
    setLoadingMore(true);
    try {
      const result = await api.activities(items.length, PAGE_SIZE);
      setItems((current) => {
        const seen = new Set(current.map((activity) => activity.id));
        return [...current, ...result.items.filter((activity) => !seen.has(activity.id))];
      });
    } catch (error) {
      setNotice({ tone: 'error', ...describeError(error) });
    } finally {
      setLoadingMore(false);
    }
  }, [items.length, loadingMore, page]);

  const sections = useMemo(() => {
    const groups = new Map<string, Activity[]>();
    for (const activity of items) {
      const key = monthKey(activity.start_time_local);
      groups.set(key, [...(groups.get(key) ?? []), activity]);
    }
    return Array.from(groups, ([key, data]) => ({ key, title: formatMonth(key), data }));
  }, [items]);

  const summary = !page
    ? 'Caricamento…'
    : page.last_sync_at
      ? `${page.total} attività · aggiornato ${formatRelative(page.last_sync_at, now)}`
      : 'Mai sincronizzato con Garmin';

  let content;
  if (loadError) {
    const { title, message } = describeError(loadError);
    content = (
      <StateView
        symbol={{ ios: 'wifi.slash', android: 'wifi_off', web: 'wifi_off' }}
        tint={colors.danger}
        title={title}
        message={message}
        actionLabel="Riprova"
        onAction={retryLoad}
      />
    );
  } else if (!page) {
    content = <ActivityIndicator style={styles.loader} color={colors.textSecondary} />;
  } else if (items.length === 0) {
    content = (
      <StateView
        symbol={{ ios: 'figure.run.circle', android: 'directions_run', web: 'directions_run' }}
        title="Ancora nessuna attività"
        message="Premi Aggiorna per scaricare le tue attività da Garmin Connect."
      />
    );
  } else {
    content = (
      <SectionList
        sections={sections}
        keyExtractor={(activity) => String(activity.id)}
        renderItem={({ item }) => <ActivityCard activity={item} now={now} />}
        renderSectionHeader={({ section }) => <Text style={styles.sectionTitle}>{section.title}</Text>}
        ItemSeparatorComponent={ItemSeparator}
        stickySectionHeadersEnabled={false}
        contentContainerStyle={[styles.listContent, { paddingBottom: insets.bottom + spacing.xxl }]}
        onEndReached={loadMore}
        onEndReachedThreshold={0.6}
        ListFooterComponent={
          loadingMore ? <ActivityIndicator style={styles.footerLoader} color={colors.textSecondary} /> : undefined
        }
        refreshControl={
          <RefreshControl
            refreshing={syncing === 'pull'}
            onRefresh={() => sync('pull')}
            tintColor={colors.textSecondary}
          />
        }
      />
    );
  }

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'left', 'right']}>
      <View style={styles.column}>
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <Text style={styles.title}>Attività</Text>
            <SyncButton syncing={syncing !== null} onPress={() => sync('button')} />
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summary} numberOfLines={1}>
              {summary}
            </Text>
            {page?.mode === 'demo' && <Text style={styles.demoBadge}>DEMO</Text>}
          </View>
        </View>
        {notice && <NoticeBanner notice={notice} onDismiss={() => setNotice(null)} />}
        {content}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  column: {
    flex: 1,
    width: '100%',
    maxWidth: maxContentWidth,
    alignSelf: 'center',
  },
  header: {
    gap: spacing.xs,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.lg,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.md,
  },
  title: {
    flexShrink: 1,
    color: colors.text,
    fontSize: 32,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  summary: {
    flexShrink: 1,
    color: colors.textSecondary,
    fontSize: 13,
  },
  demoBadge: {
    flexShrink: 0,
    color: colors.warning,
    backgroundColor: `${colors.warning}22`,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.6,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.sm,
    overflow: 'hidden',
  },
  loader: {
    flex: 1,
  },
  listContent: {
    paddingHorizontal: spacing.lg,
  },
  sectionTitle: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    paddingTop: spacing.lg,
    paddingBottom: spacing.sm,
  },
  separator: {
    height: spacing.sm,
  },
  footerLoader: {
    paddingVertical: spacing.xl,
  },
});
