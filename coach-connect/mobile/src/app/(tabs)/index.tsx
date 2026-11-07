import * as Haptics from 'expo-haptics';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, RefreshControl, SectionList, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ActivityCard } from '@/components/activity-card';
import { ConnectGarminCard } from '@/components/connect-garmin-card';
import { Fab } from '@/components/fab';
import { NoticeBanner, type Notice } from '@/components/notice-banner';
import { StateView } from '@/components/state-view';
import { SyncButton } from '@/components/sync-button';
import { colors, maxContentWidth, radius, spacing } from '@/constants/theme';
import { useNow } from '@/hooks/use-now';
import { api, ApiError, describeError, type FeedItem, type FeedPage } from '@/lib/api';
import { formatMonth, formatRelative, monthKey } from '@/lib/format';

const PAGE_SIZE = 50;

type SyncTrigger = 'button' | 'pull';

function ItemSeparator() {
  return <View style={styles.separator} />;
}

export default function ActivitiesScreen() {
  const now = useNow(30_000);
  const [page, setPage] = useState<Omit<FeedPage, 'items' | 'limit' | 'offset'> | null>(null);
  const [items, setItems] = useState<FeedItem[]>([]);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [syncing, setSyncing] = useState<SyncTrigger | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [garminReady, setGarminReady] = useState<boolean | null>(null);

  const applyFirstPage = useCallback((result: FeedPage) => {
    setItems(result.items);
    setPage({ total: result.total, mode: result.mode, last_sync_at: result.last_sync_at });
    setLoadError(null);
  }, []);

  const loadFirstPage = useCallback(async () => applyFirstPage(await api.feed(0, PAGE_SIZE)), [applyFirstPage]);

  const retryLoad = useCallback(() => {
    setLoadError(null);
    setPage(null);
    loadFirstPage().catch(setLoadError);
  }, [loadFirstPage]);

  // Reload whenever the tab comes back into view, e.g. after logging a workout or connecting Garmin.
  useFocusEffect(
    useCallback(() => {
      let active = true;
      api
        .feed(0, PAGE_SIZE)
        .then((result) => active && applyFirstPage(result))
        .catch((error: unknown) => active && setLoadError(error));
      api
        .status()
        .then((status) => active && setGarminReady(status.garmin_ready))
        .catch(() => {});
      return () => {
        active = false;
      };
    }, [applyFirstPage]),
  );

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
        if (result.warning) {
          setNotice({ tone: 'error', title: 'Aggiornamento parziale', message: result.warning });
        } else {
          setNotice(
            result.new > 0
              ? { tone: 'success', title: result.new === 1 ? '1 nuova attività' : `${result.new} nuove attività` }
              : { tone: 'info', title: 'Già tutto aggiornato' },
          );
        }
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      } catch (error) {
        if (error instanceof ApiError && error.code === 'garmin_not_authenticated') {
          setGarminReady(false);
        }
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
      const result = await api.feed(items.length, PAGE_SIZE);
      setItems((current) => {
        const seen = new Set(current.map((item) => item.key));
        return [...current, ...result.items.filter((item) => !seen.has(item.key))];
      });
    } catch (error) {
      setNotice({ tone: 'error', ...describeError(error) });
    } finally {
      setLoadingMore(false);
    }
  }, [items.length, loadingMore, page]);

  const sections = useMemo(() => {
    const groups = new Map<string, FeedItem[]>();
    for (const item of items) {
      const key = monthKey(item.start_time_local);
      groups.set(key, [...(groups.get(key) ?? []), item]);
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
        message="Premi Aggiorna per scaricare le attività da Garmin Connect, oppure + per registrare un allenamento."
      />
    );
  } else {
    content = (
      <SectionList
        sections={sections}
        keyExtractor={(item) => item.key}
        renderItem={({ item }) => (
          <ActivityCard
            item={item}
            now={now}
            onPress={
              item.source === 'manual'
                ? () => router.push({ pathname: '/workout/[id]', params: { id: String(item.id) } })
                : undefined
            }
          />
        )}
        renderSectionHeader={({ section }) => <Text style={styles.sectionTitle}>{section.title}</Text>}
        ItemSeparatorComponent={ItemSeparator}
        stickySectionHeadersEnabled={false}
        contentInsetAdjustmentBehavior="automatic"
        contentContainerStyle={styles.listContent}
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
        {page?.mode === 'live' && garminReady === false && <ConnectGarminCard onPress={() => router.push('/garmin')} />}
        {notice && <NoticeBanner notice={notice} onDismiss={() => setNotice(null)} />}
        {content}
        <Fab accessibilityLabel="Registra un allenamento" onPress={() => router.push('/log')} />
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
    paddingBottom: 96,
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
