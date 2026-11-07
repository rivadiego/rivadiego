import { router, useFocusEffect } from 'expo-router';
import { SymbolView } from 'expo-symbols';
import { useCallback, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { StateView } from '@/components/state-view';
import { colors, maxContentWidth, radius, spacing } from '@/constants/theme';
import { useNow } from '@/hooks/use-now';
import { api, describeError, type Plan, type TemplateExercise, type WorkoutTemplate } from '@/lib/api';
import { formatDay, formatSet } from '@/lib/format';

const logWorkout = (key: 'A' | 'B') => router.push({ pathname: '/log', params: { template: key } });

function NextWorkoutCard({ plan, now }: { plan: Plan; now: Date }) {
  const next = plan.workouts[plan.next_workout];
  const last = plan.last_workout;
  return (
    <View style={styles.nextCard}>
      <Text style={styles.overline}>Prossimo allenamento</Text>
      <Text style={styles.nextTitle}>{next.title}</Text>
      <Text style={styles.muted}>{next.focus}</Text>
      {last && plan.done_today ? (
        <View style={styles.doneRow}>
          <SymbolView name={{ ios: 'checkmark.circle.fill', android: 'check_circle', web: 'check_circle' }} size={18} tintColor={colors.success} />
          <Text style={styles.doneLabel}>Oggi hai fatto il {last.title}</Text>
        </View>
      ) : (
        <Text style={styles.muted}>
          {last
            ? `Ultimo: ${last.title}, ${formatDay(last.date, now).toLowerCase()}`
            : 'Ancora nessun allenamento registrato: si parte dal Workout A.'}
        </Text>
      )}
      <Pressable
        accessibilityRole="button"
        onPress={() => logWorkout(plan.next_workout)}
        style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed]}>
        <Text style={styles.primaryLabel}>Registra {next.title}</Text>
      </Pressable>
    </View>
  );
}

function ExerciseRow({ exercise, now }: { exercise: TemplateExercise; now: Date }) {
  const [open, setOpen] = useState(false);
  const next = exercise.suggestion.sets.some((s) => s.weight_kg != null || s.reps != null || s.seconds != null)
    ? exercise.suggestion.sets.map((s) => formatSet(s, exercise.measure)).join(' · ')
    : null;
  return (
    <Pressable accessibilityRole="button" onPress={() => setOpen((value) => !value)} style={styles.exerciseRow}>
      <View style={styles.exerciseHeader}>
        <Text style={styles.exerciseName}>{exercise.name}</Text>
        <Text style={styles.scheme}>{exercise.scheme_label}</Text>
      </View>
      {next ? (
        <Text style={[styles.next, exercise.suggestion.progressed && styles.nextUp]}>
          {exercise.suggestion.progressed ? '↑ ' : ''}Prossima volta: {next}
        </Text>
      ) : null}
      {open ? (
        <View style={styles.details}>
          <Text style={styles.cue}>{exercise.cue}</Text>
          {exercise.last.length ? (
            <Text style={styles.muted}>
              Ultima volta{exercise.last_date ? ` (${formatDay(exercise.last_date, now).toLowerCase()})` : ''}:{' '}
              {exercise.last.map((s) => formatSet(s, exercise.measure)).join(' · ')}
            </Text>
          ) : null}
          <Text style={styles.muted}>{exercise.suggestion.message}</Text>
          {exercise.rest_s ? <Text style={styles.muted}>Recupero {exercise.rest_s / 60}&apos;</Text> : null}
        </View>
      ) : null}
    </Pressable>
  );
}

function WorkoutSection({ workout, now }: { workout: WorkoutTemplate; now: Date }) {
  return (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <View style={styles.sectionTitles}>
          <Text style={styles.sectionTitle}>{workout.title}</Text>
          <Text style={styles.muted}>{workout.focus}</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Registra ${workout.title}`}
          onPress={() => logWorkout(workout.key)}
          style={({ pressed }) => [styles.smallButton, pressed && styles.pressed]}>
          <SymbolView name={{ ios: 'plus', android: 'add', web: 'add' }} size={14} tintColor={colors.accent} />
          <Text style={styles.smallButtonLabel}>Registra</Text>
        </Pressable>
      </View>
      {workout.exercises.map((exercise) => (
        <ExerciseRow key={exercise.exercise_id} exercise={exercise} now={now} />
      ))}
      <Text style={styles.subheading}>
        Addominali · {workout.abs_rounds}
      </Text>
      <Text style={styles.muted}>{workout.abs_rest}</Text>
      {workout.abs.map((exercise) => (
        <View key={exercise.exercise_id} style={styles.absRow}>
          <Text style={styles.absName}>{exercise.name}</Text>
          <Text style={styles.scheme}>{exercise.scheme_label}</Text>
        </View>
      ))}
    </View>
  );
}

export default function PlanScreen() {
  const now = useNow(60_000);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [error, setError] = useState<unknown>(null);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      api
        .plan()
        .then((result) => {
          if (active) {
            setPlan(result);
            setError(null);
          }
        })
        .catch((e: unknown) => active && setError(e));
      return () => {
        active = false;
      };
    }, []),
  );

  let body;
  if (error && !plan) {
    const { title, message } = describeError(error);
    body = <StateView symbol={{ ios: 'wifi.slash', android: 'wifi_off', web: 'wifi_off' }} tint={colors.danger} title={title} message={message} />;
  } else if (!plan) {
    body = <ActivityIndicator style={styles.loader} color={colors.textSecondary} />;
  } else {
    body = (
      <ScrollView contentInsetAdjustmentBehavior="automatic" contentContainerStyle={styles.content}>
        <NextWorkoutCard plan={plan} now={now} />
        <WorkoutSection workout={plan.workouts.A} now={now} />
        <WorkoutSection workout={plan.workouts.B} now={now} />

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Come si lavora</Text>
          {plan.rules.map((rule) => (
            <View key={rule.title} style={styles.rule}>
              <Text style={styles.exerciseName}>{rule.title}</Text>
              <Text style={styles.muted}>{rule.text}</Text>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Alimentazione e monitoraggio</Text>
          {plan.nutrition.map((line) => (
            <Text key={line} style={styles.bullet}>
              • {line}
            </Text>
          ))}
        </View>
      </ScrollView>
    );
  }

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'left', 'right']}>
      <View style={styles.column}>
        <View style={styles.header}>
          <Text style={styles.title}>Scheda</Text>
          <Text style={styles.summary}>{plan ? plan.subtitle : 'Caricamento…'}</Text>
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
    gap: spacing.xs,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.md,
  },
  title: {
    color: colors.text,
    fontSize: 32,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  summary: {
    color: colors.textSecondary,
    fontSize: 13,
  },
  loader: {
    flex: 1,
  },
  content: {
    gap: spacing.lg,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xxl * 2,
  },
  nextCard: {
    gap: spacing.sm,
    padding: spacing.lg,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.accent,
  },
  overline: {
    color: colors.accent,
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  nextTitle: {
    color: colors.text,
    fontSize: 24,
    fontWeight: '800',
  },
  doneRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  doneLabel: {
    color: colors.success,
    fontSize: 15,
    fontWeight: '700',
  },
  primaryButton: {
    alignItems: 'center',
    paddingVertical: spacing.md,
    borderRadius: radius.pill,
    backgroundColor: colors.accent,
    marginTop: spacing.xs,
  },
  primaryLabel: {
    color: colors.onAccent,
    fontSize: 15,
    fontWeight: '700',
  },
  section: {
    gap: spacing.sm,
    padding: spacing.lg,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  sectionTitles: {
    flex: 1,
    gap: 2,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '800',
  },
  smallButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.accentSoft,
  },
  smallButtonLabel: {
    color: colors.accent,
    fontSize: 13,
    fontWeight: '700',
  },
  exerciseRow: {
    gap: 3,
    paddingVertical: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  exerciseHeader: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    gap: spacing.sm,
  },
  exerciseName: {
    flexShrink: 1,
    color: colors.text,
    fontSize: 15,
    fontWeight: '600',
  },
  scheme: {
    color: colors.textSecondary,
    fontSize: 13,
    fontWeight: '600',
    fontVariant: ['tabular-nums'],
  },
  next: {
    color: colors.textSecondary,
    fontSize: 13,
    fontVariant: ['tabular-nums'],
  },
  nextUp: {
    color: colors.accent,
    fontWeight: '600',
  },
  details: {
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  cue: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 19,
  },
  muted: {
    color: colors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
  },
  subheading: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginTop: spacing.sm,
  },
  absRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: spacing.sm,
  },
  absName: {
    color: colors.text,
    fontSize: 14,
  },
  rule: {
    gap: 2,
  },
  bullet: {
    color: colors.textSecondary,
    fontSize: 14,
    lineHeight: 20,
  },
  pressed: {
    opacity: 0.7,
  },
});
