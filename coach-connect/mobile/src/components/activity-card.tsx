import { SymbolView } from 'expo-symbols';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { colors, radius, spacing } from '@/constants/theme';
import type { FeedItem } from '@/lib/api';
import {
  formatActivityDate,
  formatCalories,
  formatDistance,
  formatDuration,
  formatElevation,
  formatHeartRate,
  formatPaceOrSpeed,
  formatVolume,
} from '@/lib/format';
import { sportMeta } from '@/lib/sports';

type Props = {
  item: FeedItem;
  now: Date;
  onPress?: () => void;
};

function details(item: FeedItem): string[] {
  const duration = formatDuration(item.duration_s);
  if (item.source === 'manual') {
    return [
      item.exercise_count ? `${item.exercise_count} esercizi` : null,
      item.set_count ? `${item.set_count} serie` : null,
      formatVolume(item.volume_kg),
      formatHeartRate(item.avg_hr),
      formatCalories(item.calories),
    ].filter((d): d is string => Boolean(d));
  }
  const distance = formatDistance(item.distance_m, item.sport);
  return [
    distance ? duration : null,
    formatPaceOrSpeed(item),
    formatHeartRate(item.avg_hr),
    formatElevation(item.elevation_gain_m),
    distance ? null : formatCalories(item.calories),
  ].filter((d): d is string => Boolean(d));
}

export function ActivityCard({ item, now, onPress }: Props) {
  const sport = sportMeta(item.sport);
  const primary =
    item.source === 'manual' ? formatDuration(item.duration_s) : (formatDistance(item.distance_m, item.sport) ?? formatDuration(item.duration_s));
  const origin = item.source === 'manual' ? (item.garmin_linked ? 'registrato + Garmin' : 'registrato') : item.location;
  const subtitle = [formatActivityDate(item.start_time_local, now), origin].filter(Boolean).join(' · ');
  const chips = details(item);

  return (
    <Pressable
      disabled={!onPress}
      onPress={onPress}
      accessibilityRole={onPress ? 'button' : undefined}
      accessibilityLabel={`${sport.label}: ${item.name}, ${subtitle}`}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}>
      <View style={[styles.icon, { backgroundColor: `${sport.color}22` }]}>
        <SymbolView name={sport.symbol} size={22} tintColor={sport.color} />
      </View>
      <View style={styles.body}>
        <View style={styles.titleRow}>
          <Text style={styles.title} numberOfLines={1}>
            {item.name}
          </Text>
          {primary && <Text style={styles.primary}>{primary}</Text>}
        </View>
        <Text style={styles.subtitle} numberOfLines={1}>
          {subtitle}
        </Text>
        {chips.length > 0 && (
          <View style={styles.details}>
            {chips.map((detail, index) => (
              <Text key={index} style={styles.detail}>
                {detail}
              </Text>
            ))}
          </View>
        )}
      </View>
      {onPress && (
        <SymbolView
          name={{ ios: 'chevron.right', android: 'chevron_right', web: 'chevron_right' }}
          size={14}
          tintColor={colors.textMuted}
          style={styles.chevron}
        />
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    gap: spacing.md,
    padding: spacing.lg,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  pressed: {
    opacity: 0.8,
  },
  icon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  body: {
    flex: 1,
    gap: spacing.xs,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: spacing.sm,
  },
  title: {
    flex: 1,
    color: colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
  primary: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 13,
  },
  details: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs + 2,
    marginTop: spacing.xs,
  },
  detail: {
    color: colors.text,
    fontSize: 12,
    fontWeight: '500',
    fontVariant: ['tabular-nums'],
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: radius.sm,
    backgroundColor: colors.surfaceRaised,
    overflow: 'hidden',
  },
  chevron: {
    alignSelf: 'center',
  },
});
