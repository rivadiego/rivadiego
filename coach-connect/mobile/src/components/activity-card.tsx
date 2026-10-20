import { SymbolView } from 'expo-symbols';
import { StyleSheet, Text, View } from 'react-native';

import { colors, radius, spacing } from '@/constants/theme';
import type { Activity } from '@/lib/api';
import {
  formatActivityDate,
  formatCalories,
  formatDistance,
  formatDuration,
  formatElevation,
  formatHeartRate,
  formatPaceOrSpeed,
} from '@/lib/format';
import { sportMeta } from '@/lib/sports';

type Props = {
  activity: Activity;
  now: Date;
};

export function ActivityCard({ activity, now }: Props) {
  const sport = sportMeta(activity.sport);
  const distance = formatDistance(activity.distance_m, activity.sport);
  const duration = formatDuration(activity.duration_s);
  const details = [
    distance ? duration : null,
    formatPaceOrSpeed(activity),
    formatHeartRate(activity.avg_hr),
    formatElevation(activity.elevation_gain_m),
    distance ? null : formatCalories(activity.calories),
  ].filter((detail): detail is string => Boolean(detail));
  const subtitle = [formatActivityDate(activity.start_time_local, now), activity.location]
    .filter(Boolean)
    .join(' · ');

  return (
    <View style={styles.card} accessibilityLabel={`${sport.label}: ${activity.name}, ${subtitle}`}>
      <View style={[styles.icon, { backgroundColor: `${sport.color}22` }]}>
        <SymbolView name={sport.symbol} size={22} tintColor={sport.color} />
      </View>
      <View style={styles.body}>
        <View style={styles.titleRow}>
          <Text style={styles.title} numberOfLines={1}>
            {activity.name}
          </Text>
          {(distance ?? duration) && <Text style={styles.primary}>{distance ?? duration}</Text>}
        </View>
        <Text style={styles.subtitle} numberOfLines={1}>
          {subtitle}
        </Text>
        {details.length > 0 && (
          <View style={styles.details}>
            {details.map((detail, index) => (
              <Text key={index} style={styles.detail}>
                {detail}
              </Text>
            ))}
          </View>
        )}
      </View>
    </View>
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
});
