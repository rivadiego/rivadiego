import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { StateView } from '@/components/state-view';
import { colors, maxContentWidth, radius, spacing } from '@/constants/theme';
import { useNow } from '@/hooks/use-now';
import { api, describeError, type WorkoutDetail } from '@/lib/api';
import {
  formatActivityDate,
  formatCalories,
  formatDuration,
  formatHeartRate,
  formatSet,
  formatVolume,
} from '@/lib/format';

function confirmDelete(onConfirm: () => void) {
  const message = 'Vuoi eliminare questo allenamento? Non si può annullare.';
  if (Platform.OS === 'web') {
    if (window.confirm(message)) {
      onConfirm();
    }
    return;
  }
  Alert.alert('Elimina allenamento', message, [
    { text: 'Annulla', style: 'cancel' },
    { text: 'Elimina', style: 'destructive', onPress: onConfirm },
  ]);
}

export default function WorkoutDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const now = useNow(60_000);
  const [workout, setWorkout] = useState<WorkoutDetail | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let active = true;
    api
      .workout(Number(id))
      .then((result) => active && setWorkout(result))
      .catch((e: unknown) => active && setError(e));
    return () => {
      active = false;
    };
  }, [id]);

  const remove = () =>
    confirmDelete(async () => {
      setDeleting(true);
      try {
        await api.deleteWorkout(Number(id));
        router.back();
      } catch (e) {
        setError(e);
        setDeleting(false);
      }
    });

  let body;
  if (error) {
    const { title, message } = describeError(error);
    body = <StateView symbol={{ ios: 'xmark', android: 'close', web: 'close' }} tint={colors.danger} title={title} message={message} />;
  } else if (!workout) {
    body = <ActivityIndicator style={styles.loader} color={colors.textSecondary} />;
  } else {
    const stats = [
      formatDuration(workout.duration_s),
      `${workout.set_count} serie`,
      formatVolume(workout.volume_kg),
      formatHeartRate(workout.avg_hr),
      formatCalories(workout.calories),
    ].filter((s): s is string => Boolean(s));
    body = (
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>{workout.name}</Text>
        <Text style={styles.subtitle}>
          {formatActivityDate(workout.start_time_local, now)}
          {workout.garmin_activity_id ? ' · con i dati dell’orologio' : ''}
        </Text>
        <View style={styles.stats}>
          {stats.map((stat) => (
            <Text key={stat} style={styles.stat}>
              {stat}
            </Text>
          ))}
        </View>
        {workout.exercises.map((exercise) => (
          <View key={exercise.position} style={styles.exercise}>
            <Text style={styles.exerciseName}>{exercise.name}</Text>
            {exercise.sets.map((set, index) => (
              <View key={index} style={styles.setRow}>
                <Text style={styles.setIndex}>{index + 1}</Text>
                <Text style={styles.setValue}>{formatSet(set, exercise.measure)}</Text>
              </View>
            ))}
          </View>
        ))}
        {workout.notes ? (
          <View style={styles.exercise}>
            <Text style={styles.exerciseName}>Note</Text>
            <Text style={styles.notes}>{workout.notes}</Text>
          </View>
        ) : null}
        <Pressable
          accessibilityRole="button"
          disabled={deleting}
          onPress={remove}
          style={({ pressed }) => [styles.delete, (pressed || deleting) && styles.pressed]}>
          <Text style={styles.deleteLabel}>Elimina allenamento</Text>
        </Pressable>
      </ScrollView>
    );
  }

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'left', 'right', 'bottom']}>
      <View style={styles.column}>
        <View style={styles.header}>
          <View />
          <Pressable accessibilityRole="button" onPress={() => router.back()} hitSlop={10}>
            <Text style={styles.close}>Chiudi</Text>
          </Pressable>
        </View>
        {body}
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  close: {
    color: colors.accent,
    fontSize: 16,
    fontWeight: '600',
  },
  loader: {
    flex: 1,
  },
  content: {
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  title: {
    color: colors.text,
    fontSize: 26,
    fontWeight: '800',
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 14,
    marginTop: -spacing.sm,
  },
  stats: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  stat: {
    color: colors.text,
    fontSize: 13,
    fontWeight: '600',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 1,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceRaised,
    overflow: 'hidden',
  },
  exercise: {
    gap: spacing.xs,
    padding: spacing.lg,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  exerciseName: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '700',
    marginBottom: spacing.xs,
  },
  setRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  setIndex: {
    width: 20,
    color: colors.textMuted,
    fontSize: 15,
    fontVariant: ['tabular-nums'],
  },
  setValue: {
    color: colors.text,
    fontSize: 15,
    fontVariant: ['tabular-nums'],
  },
  notes: {
    color: colors.textSecondary,
    fontSize: 15,
    lineHeight: 21,
  },
  delete: {
    alignItems: 'center',
    paddingVertical: spacing.md,
    marginTop: spacing.md,
  },
  deleteLabel: {
    color: colors.danger,
    fontSize: 15,
    fontWeight: '600',
  },
  pressed: {
    opacity: 0.6,
  },
});
