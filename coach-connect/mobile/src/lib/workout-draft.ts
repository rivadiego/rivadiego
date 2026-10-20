import type { Exercise, Measure, NewWorkout, SetValues, TemplateExercise, WorkoutTemplate } from '@/lib/api';
import { formatDay, formatKg, formatSet, parseDecimal, toLocalIso } from '@/lib/format';

/** Inputs are kept as text while editing ("61,25"), and parsed on save. */
export type DraftSet = { key: string; weight: string; reps: string; seconds: string };

export type DraftExercise = {
  key: string;
  exerciseId: string;
  name: string;
  measure: Measure;
  equipment: string;
  scheme?: string;
  last?: string;
  hint?: string;
  progressed?: boolean;
  warmup?: string;
  sets: DraftSet[];
};

let counter = 0;
export function newKey(): string {
  counter += 1;
  return `k${counter}`;
}

export function draftSet(values?: SetValues): DraftSet {
  return {
    key: newKey(),
    weight: values?.weight_kg ? formatKg(values.weight_kg) : '',
    reps: values?.reps != null ? String(values.reps) : '',
    seconds: values?.seconds != null ? String(values.seconds) : '',
  };
}

export function draftFromTemplateExercise(exercise: TemplateExercise, now: Date): DraftExercise {
  const lastDay = exercise.last_date ? ` (${formatDay(exercise.last_date, now).toLowerCase()})` : '';
  const rest = exercise.rest_s >= 60 ? `recupero ${exercise.rest_s / 60}'` : null;
  return {
    key: newKey(),
    exerciseId: exercise.exercise_id,
    name: exercise.name,
    measure: exercise.measure,
    equipment: exercise.equipment,
    scheme: [exercise.scheme_label, rest].filter(Boolean).join(' · '),
    last: exercise.last.length
      ? `Ultima volta${lastDay}: ${exercise.last.map((s) => formatSet(s, exercise.measure)).join(' · ')}`
      : undefined,
    hint: exercise.suggestion.message,
    progressed: exercise.suggestion.progressed,
    warmup: exercise.suggestion.warmup.length
      ? `Riscaldamento: ${exercise.suggestion.warmup.map((s) => formatSet(s, 'reps')).join(' · ')}`
      : undefined,
    sets: exercise.suggestion.sets.map(draftSet),
  };
}

export function draftFromTemplate(template: WorkoutTemplate, now: Date): DraftExercise[] {
  return [...template.exercises, ...template.abs].map((exercise) => draftFromTemplateExercise(exercise, now));
}

export function draftFromCatalog(exercise: Exercise): DraftExercise {
  return {
    key: newKey(),
    exerciseId: exercise.id,
    name: exercise.name,
    measure: exercise.measure,
    equipment: exercise.equipment,
    sets: [draftSet()],
  };
}

const toInt = (text: string) => {
  const value = parseDecimal(text);
  return value == null ? null : Math.round(value);
};

export function toNewWorkout(
  planWorkout: 'A' | 'B' | null,
  start: Date,
  notes: string,
  exercises: DraftExercise[],
): NewWorkout {
  return {
    plan_workout: planWorkout,
    started_at: toLocalIso(start),
    notes: notes.trim() || null,
    exercises: exercises
      .map((exercise) => ({
        exercise_id: exercise.exerciseId,
        sets: exercise.sets
          .map((s) => ({
            weight_kg: exercise.measure === 'seconds' ? null : parseDecimal(s.weight),
            reps: exercise.measure === 'seconds' ? null : toInt(s.reps),
            seconds: exercise.measure === 'seconds' ? toInt(s.seconds) : null,
          }))
          .filter((s) => s.reps != null || s.seconds != null),
      }))
      .filter((exercise) => exercise.sets.length > 0),
  };
}

/** Start time from "Oggi/Ieri/…" and an "HH:MM" text; null if the time isn't valid. */
export function startDate(daysAgo: number, time: string, now: Date): Date | null {
  const match = /^(\d{1,2})[:.](\d{2})$/.exec(time.trim());
  if (!match || Number(match[1]) > 23 || Number(match[2]) > 59) {
    return null;
  }
  return new Date(now.getFullYear(), now.getMonth(), now.getDate() - daysAgo, Number(match[1]), Number(match[2]));
}

export const EQUIPMENT_LABELS: Record<string, string> = {
  barbell: 'Bilanciere',
  dumbbell: 'Manubri',
  cable: 'Cavi',
  machine: 'Macchina',
  bodyweight: 'Corpo libero',
  weighted_bodyweight: 'Corpo libero + zavorra',
};
