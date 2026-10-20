import * as Haptics from 'expo-haptics';
import { router, useLocalSearchParams } from 'expo-router';
import { SymbolView } from 'expo-symbols';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ChoiceChips } from '@/components/choice-chips';
import { ExerciseEditor } from '@/components/exercise-editor';
import { ExercisePicker } from '@/components/exercise-picker';
import { StateView } from '@/components/state-view';
import { colors, maxContentWidth, radius, spacing } from '@/constants/theme';
import { api, describeError, type Exercise, type ExerciseCatalog, type Plan } from '@/lib/api';
import {
  draftFromCatalog,
  draftFromTemplate,
  draftFromTemplateExercise,
  draftSet,
  newKey,
  startDate,
  toNewWorkout,
  type DraftExercise,
  type DraftSet,
} from '@/lib/workout-draft';

type TemplateChoice = 'A' | 'B' | 'free';

const TEMPLATE_OPTIONS: { value: TemplateChoice; label: string }[] = [
  { value: 'A', label: 'A · Push' },
  { value: 'B', label: 'B · Pull' },
  { value: 'free', label: 'Libero' },
];

const DAY_OPTIONS: { value: '0' | '1' | '2'; label: string }[] = [
  { value: '0', label: 'Oggi' },
  { value: '1', label: 'Ieri' },
  { value: '2', label: '2 giorni fa' },
];

const pad = (n: number) => String(n).padStart(2, '0');

export default function LogWorkoutScreen() {
  const params = useLocalSearchParams<{ template?: string }>();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [catalog, setCatalog] = useState<ExerciseCatalog | null>(null);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [template, setTemplate] = useState<TemplateChoice>('free');
  const [exercises, setExercises] = useState<DraftExercise[]>([]);
  const [daysAgo, setDaysAgo] = useState<'0' | '1' | '2'>('0');
  const [time, setTime] = useState(() => {
    const now = new Date();
    return `${pad(now.getHours())}:${pad(now.getMinutes())}`;
  });
  const [notes, setNotes] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([api.plan(), api.exercises()])
      .then(([loadedPlan, loadedCatalog]) => {
        if (!active) {
          return;
        }
        const requested = params.template === 'A' || params.template === 'B' ? params.template : null;
        const { today } = loadedPlan;
        const todayKey = !today.done && (today.key === 'A' || today.key === 'B') ? today.key : null;
        const initial = requested ?? todayKey ?? loadedPlan.next_gym_workout;
        setPlan(loadedPlan);
        setCatalog(loadedCatalog);
        setTemplate(initial);
        setExercises(draftFromTemplate(loadedPlan.workouts[initial], new Date()));
      })
      .catch((error: unknown) => active && setLoadError(error));
    return () => {
      active = false;
    };
  }, [params.template]);

  const chooseTemplate = (choice: TemplateChoice) => {
    setTemplate(choice);
    setExercises(choice === 'free' || !plan ? [] : draftFromTemplate(plan.workouts[choice], new Date()));
  };

  const updateExercise = (key: string, change: (exercise: DraftExercise) => DraftExercise) =>
    setExercises((list) => list.map((exercise) => (exercise.key === key ? change(exercise) : exercise)));

  const changeSet = (exerciseKey: string, setKey: string, field: keyof Omit<DraftSet, 'key'>, value: string) =>
    updateExercise(exerciseKey, (exercise) => ({
      ...exercise,
      sets: exercise.sets.map((s) => (s.key === setKey ? { ...s, [field]: value } : s)),
    }));

  const addSet = (exerciseKey: string) =>
    updateExercise(exerciseKey, (exercise) => {
      const last = exercise.sets.at(-1);
      return { ...exercise, sets: [...exercise.sets, last ? { ...last, key: newKey() } : draftSet()] };
    });

  const removeSet = (exerciseKey: string, setKey: string) =>
    updateExercise(exerciseKey, (exercise) => ({ ...exercise, sets: exercise.sets.filter((s) => s.key !== setKey) }));

  const addExercise = (exercise: Exercise) => {
    const planned = plan
      ? [...plan.workouts.A.exercises, ...plan.workouts.A.abs, ...plan.workouts.B.exercises].find(
          (item) => item.exercise_id === exercise.id,
        )
      : undefined;
    setExercises((list) => [...list, planned ? draftFromTemplateExercise(planned, new Date()) : draftFromCatalog(exercise)]);
    setPickerOpen(false);
  };

  const save = async () => {
    const start = startDate(Number(daysAgo), time, new Date());
    if (!start) {
      setSaveError("Orario non valido: scrivilo come 07:30.");
      return;
    }
    const workout = toNewWorkout(template === 'free' ? null : template, start, notes, exercises);
    if (workout.exercises.length === 0) {
      setSaveError('Inserisci almeno una serie con le ripetizioni (o i secondi).');
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      await api.createWorkout(workout);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      router.back();
    } catch (error) {
      const { title, message } = describeError(error);
      setSaveError(`${title}: ${message}`);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
    } finally {
      setSaving(false);
    }
  };

  let body;
  if (loadError) {
    const { title, message } = describeError(loadError);
    body = (
      <StateView
        symbol={{ ios: 'wifi.slash', android: 'wifi_off', web: 'wifi_off' }}
        tint={colors.danger}
        title={title}
        message={message}
      />
    );
  } else if (!plan || !catalog) {
    body = <ActivityIndicator style={styles.loader} color={colors.textSecondary} />;
  } else {
    body = (
      <ScrollView
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="on-drag"
        contentContainerStyle={styles.content}>
        <Text style={styles.label}>Scheda</Text>
        <ChoiceChips options={TEMPLATE_OPTIONS} value={template} onChange={chooseTemplate} />

        <Text style={styles.label}>Quando</Text>
        <View style={styles.whenRow}>
          <ChoiceChips options={DAY_OPTIONS} value={daysAgo} onChange={setDaysAgo} />
          <TextInput
            value={time}
            onChangeText={setTime}
            keyboardType="numbers-and-punctuation"
            accessibilityLabel="Ora di inizio"
            maxLength={5}
            style={styles.timeInput}
          />
        </View>

        {exercises.map((exercise) => (
          <ExerciseEditor
            key={exercise.key}
            exercise={exercise}
            onChangeSet={(setKey, field, value) => changeSet(exercise.key, setKey, field, value)}
            onAddSet={() => addSet(exercise.key)}
            onRemoveSet={(setKey) => removeSet(exercise.key, setKey)}
            onRemove={() => setExercises((list) => list.filter((e) => e.key !== exercise.key))}
          />
        ))}

        <Pressable
          accessibilityRole="button"
          onPress={() => setPickerOpen(true)}
          style={({ pressed }) => [styles.addExercise, pressed && styles.pressed]}>
          <SymbolView name={{ ios: 'plus', android: 'add', web: 'add' }} size={16} tintColor={colors.accent} />
          <Text style={styles.addExerciseLabel}>Aggiungi esercizio</Text>
        </Pressable>

        <Text style={styles.label}>Note</Text>
        <TextInput
          value={notes}
          onChangeText={setNotes}
          placeholder="Come ti sei sentito, dolori, cose da ricordare…"
          placeholderTextColor={colors.textMuted}
          multiline
          style={styles.notes}
        />

        {saveError ? <Text style={styles.error}>{saveError}</Text> : null}
        <Pressable
          accessibilityRole="button"
          disabled={saving}
          onPress={save}
          style={({ pressed }) => [styles.saveButton, (pressed || saving) && styles.pressed]}>
          {saving ? <ActivityIndicator color={colors.onAccent} /> : <Text style={styles.saveLabel}>Salva allenamento</Text>}
        </Pressable>
      </ScrollView>
    );
  }

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'left', 'right', 'bottom']}>
      <KeyboardAvoidingView style={styles.column} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.header}>
          <Pressable accessibilityRole="button" onPress={() => router.back()} hitSlop={10}>
            <Text style={styles.headerAction}>Annulla</Text>
          </Pressable>
          <Text style={styles.title}>Registra allenamento</Text>
          <Pressable accessibilityRole="button" onPress={save} disabled={saving || !plan} hitSlop={10}>
            <Text style={[styles.headerAction, styles.headerSave]}>Salva</Text>
          </Pressable>
        </View>
        {body}
      </KeyboardAvoidingView>
      <ExercisePicker
        visible={pickerOpen}
        exercises={catalog?.exercises ?? []}
        groups={catalog?.groups ?? []}
        onSelect={addExercise}
        onClose={() => setPickerOpen(false)}
      />
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
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  title: {
    color: colors.text,
    fontSize: 17,
    fontWeight: '700',
  },
  headerAction: {
    color: colors.textSecondary,
    fontSize: 16,
  },
  headerSave: {
    color: colors.accent,
    fontWeight: '700',
  },
  loader: {
    flex: 1,
  },
  content: {
    gap: spacing.md,
    padding: spacing.lg,
    paddingBottom: spacing.xxl * 2,
  },
  label: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginTop: spacing.sm,
  },
  whenRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: spacing.sm,
  },
  timeInput: {
    width: 76,
    height: 38,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceRaised,
    borderWidth: 1,
    borderColor: colors.border,
    color: colors.text,
    fontSize: 15,
    fontWeight: '600',
    textAlign: 'center',
    fontVariant: ['tabular-nums'],
  },
  addExercise: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: colors.border,
  },
  addExerciseLabel: {
    color: colors.accent,
    fontSize: 15,
    fontWeight: '700',
  },
  notes: {
    minHeight: 80,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    color: colors.text,
    fontSize: 15,
    textAlignVertical: 'top',
  },
  error: {
    color: colors.danger,
    fontSize: 14,
  },
  saveButton: {
    alignItems: 'center',
    justifyContent: 'center',
    height: 52,
    borderRadius: radius.pill,
    backgroundColor: colors.accent,
    marginTop: spacing.sm,
  },
  saveLabel: {
    color: colors.onAccent,
    fontSize: 16,
    fontWeight: '700',
  },
  pressed: {
    opacity: 0.7,
  },
});
