import { SymbolView } from 'expo-symbols';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { colors, radius, spacing } from '@/constants/theme';
import type { DraftExercise, DraftSet } from '@/lib/workout-draft';

type Field = keyof Omit<DraftSet, 'key'>;

type Props = {
  exercise: DraftExercise;
  onChangeSet: (setKey: string, field: Field, value: string) => void;
  onAddSet: () => void;
  onRemoveSet: (setKey: string) => void;
  onRemove: () => void;
};

export function ExerciseEditor({ exercise, onChangeSet, onAddSet, onRemoveSet, onRemove }: Props) {
  const timed = exercise.measure === 'seconds';
  const weighted = !timed && exercise.equipment !== 'bodyweight';
  const weightLabel = exercise.equipment === 'weighted_bodyweight' ? 'zavorra kg' : 'kg';

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.name}>{exercise.name}</Text>
          {exercise.scheme ? <Text style={styles.meta}>{exercise.scheme}</Text> : null}
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Rimuovi ${exercise.name}`}
          onPress={onRemove}
          hitSlop={10}
          style={({ pressed }) => pressed && styles.pressed}>
          <SymbolView name={{ ios: 'trash', android: 'delete', web: 'delete' }} size={18} tintColor={colors.textMuted} />
        </Pressable>
      </View>

      {exercise.last ? <Text style={styles.meta}>{exercise.last}</Text> : null}
      {exercise.hint ? (
        <Text style={[styles.hint, exercise.progressed && styles.hintUp]}>
          {exercise.progressed ? '↑ ' : ''}
          {exercise.hint}
        </Text>
      ) : null}
      {exercise.warmup ? <Text style={styles.meta}>{exercise.warmup}</Text> : null}

      <View style={styles.tableHeader}>
        <Text style={[styles.columnLabel, styles.setColumn]}>Serie</Text>
        {weighted && <Text style={[styles.columnLabel, styles.inputColumn]}>{weightLabel}</Text>}
        <Text style={[styles.columnLabel, styles.inputColumn]}>{timed ? 'secondi' : 'rip'}</Text>
        <View style={styles.removeColumn} />
      </View>
      {exercise.sets.map((set, index) => (
        <View key={set.key} style={styles.row}>
          <Text style={[styles.setNumber, styles.setColumn]}>{index + 1}</Text>
          {weighted && (
            <TextInput
              value={set.weight}
              onChangeText={(value) => onChangeSet(set.key, 'weight', value)}
              placeholder={exercise.equipment === 'weighted_bodyweight' ? '0' : '–'}
              placeholderTextColor={colors.textMuted}
              keyboardType="decimal-pad"
              selectTextOnFocus
              accessibilityLabel={`Serie ${index + 1}, ${weightLabel}`}
              style={[styles.input, styles.inputColumn]}
            />
          )}
          <TextInput
            value={timed ? set.seconds : set.reps}
            onChangeText={(value) => onChangeSet(set.key, timed ? 'seconds' : 'reps', value)}
            placeholder="–"
            placeholderTextColor={colors.textMuted}
            keyboardType="number-pad"
            selectTextOnFocus
            accessibilityLabel={`Serie ${index + 1}, ${timed ? 'secondi' : 'ripetizioni'}`}
            style={[styles.input, styles.inputColumn]}
          />
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`Elimina serie ${index + 1}`}
            onPress={() => onRemoveSet(set.key)}
            hitSlop={8}
            style={({ pressed }) => [styles.removeColumn, pressed && styles.pressed]}>
            <SymbolView name={{ ios: 'minus', android: 'remove', web: 'remove' }} size={16} tintColor={colors.textMuted} />
          </Pressable>
        </View>
      ))}
      <Pressable
        accessibilityRole="button"
        onPress={onAddSet}
        style={({ pressed }) => [styles.addSet, pressed && styles.pressed]}>
        <SymbolView name={{ ios: 'plus', android: 'add', web: 'add' }} size={14} tintColor={colors.accent} />
        <Text style={styles.addSetLabel}>Serie</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.sm,
    padding: spacing.lg,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
  },
  headerText: {
    flex: 1,
    gap: 2,
  },
  name: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '700',
  },
  meta: {
    color: colors.textSecondary,
    fontSize: 12,
    lineHeight: 17,
  },
  hint: {
    color: colors.textSecondary,
    fontSize: 12,
    lineHeight: 17,
    fontStyle: 'italic',
  },
  hintUp: {
    color: colors.accent,
    fontStyle: 'normal',
    fontWeight: '600',
  },
  tableHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.xs,
  },
  columnLabel: {
    color: colors.textMuted,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  setColumn: {
    width: 44,
  },
  setNumber: {
    color: colors.textSecondary,
    fontSize: 15,
    fontWeight: '600',
    fontVariant: ['tabular-nums'],
  },
  inputColumn: {
    flex: 1,
    // Lets text inputs shrink below their default intrinsic width (noticeable on web).
    minWidth: 0,
  },
  input: {
    height: 42,
    paddingHorizontal: spacing.md,
    borderRadius: radius.sm,
    backgroundColor: colors.surfaceRaised,
    color: colors.text,
    fontSize: 17,
    fontWeight: '600',
    fontVariant: ['tabular-nums'],
    textAlign: 'center',
  },
  removeColumn: {
    width: 28,
    alignItems: 'center',
  },
  addSet: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: spacing.xs,
    paddingVertical: spacing.xs,
  },
  addSetLabel: {
    color: colors.accent,
    fontSize: 14,
    fontWeight: '700',
  },
  pressed: {
    opacity: 0.6,
  },
});
