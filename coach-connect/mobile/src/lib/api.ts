import Constants from 'expo-constants';
import { Platform } from 'react-native';

import type { Sport } from '@/lib/sports';

export type FeedItem = {
  key: string;
  source: 'garmin' | 'manual';
  id: number;
  name: string;
  sport: Sport;
  type_key: string;
  /** Wall-clock time where the activity happened, e.g. "2026-10-18T07:35:27". */
  start_time_local: string | null;
  start_time_utc: string | null;
  duration_s: number | null;
  distance_m: number | null;
  elevation_gain_m: number | null;
  avg_speed_mps: number | null;
  avg_hr: number | null;
  max_hr: number | null;
  calories: number | null;
  location: string | null;
  plan_workout: 'A' | 'B' | null;
  exercise_count: number | null;
  set_count: number | null;
  volume_kg: number | null;
  /** A logged workout also recorded by the watch: heart rate and duration come from Garmin. */
  garmin_linked: boolean;
};

export type FeedPage = {
  items: FeedItem[];
  total: number;
  limit: number;
  offset: number;
  mode: 'live' | 'demo';
  last_sync_at: string | null;
};

export type SyncResult = {
  mode: 'live' | 'demo';
  new: number;
  updated: number;
  pages: number;
  total: number;
  last_sync_at: string;
  history_complete: boolean;
  wellness_days: number;
  warning: string | null;
};

export type Measure = 'reps' | 'seconds';

export type SetValues = {
  weight_kg: number | null;
  reps: number | null;
  seconds?: number | null;
  note?: string | null;
};

export type TemplateExercise = {
  exercise_id: string;
  name: string;
  group: string;
  equipment: string;
  measure: Measure;
  scheme: 'rpt' | 'straight' | 'circuit';
  scheme_label: string;
  rep_range: [number, number] | null;
  rest_s: number;
  main: boolean;
  cue: string;
  last: SetValues[];
  last_date: string | null;
  suggestion: { message: string; progressed: boolean; sets: SetValues[]; warmup: SetValues[] };
};

export type WorkoutTemplate = {
  key: 'A' | 'B';
  title: string;
  focus: string;
  exercises: TemplateExercise[];
  abs: TemplateExercise[];
  abs_rounds: string;
  abs_rest: string;
};

export type Plan = {
  name: string;
  subtitle: string;
  /** A and B alternate: the one after the last logged workout. */
  next_workout: 'A' | 'B';
  last_workout: { key: 'A' | 'B'; title: string; date: string } | null;
  done_today: boolean;
  workouts: Record<'A' | 'B', WorkoutTemplate>;
  rules: { title: string; text: string }[];
  nutrition: string[];
  bodyweight_kg: number | null;
};

export type Exercise = { id: string; name: string; group: string; equipment: string; measure: Measure };

export type ExerciseCatalog = { groups: string[]; exercises: Exercise[] };

export type WorkoutDetail = {
  id: number;
  name: string;
  plan_workout: 'A' | 'B' | null;
  start_time_local: string;
  start_time_utc: string;
  duration_s: number | null;
  notes: string | null;
  garmin_activity_id: number | null;
  avg_hr: number | null;
  max_hr: number | null;
  calories: number | null;
  exercises: { position: number; exercise_id: string; name: string; measure: Measure; sets: SetValues[] }[];
  set_count: number;
  volume_kg: number;
};

export type NewWorkout = {
  plan_workout: 'A' | 'B' | null;
  started_at: string;
  notes: string | null;
  exercises: {
    exercise_id: string;
    sets: { weight_kg: number | null; reps: number | null; seconds: number | null }[];
  }[];
};

export type Wellness = {
  date: string;
  sleep_seconds: number | null;
  sleep_score: number | null;
  hrv_last_night_ms: number | null;
  hrv_weekly_avg_ms: number | null;
  hrv_status: string | null;
  resting_hr: number | null;
  body_battery_high: number | null;
  body_battery_low: number | null;
  body_battery_wake: number | null;
  stress_avg: number | null;
  steps: number | null;
  readiness_score: number | null;
  readiness_level: string | null;
  weight_kg: number | null;
};

export type ChatMessage = { id: number; role: 'user' | 'assistant'; content: string; created_at: string };

/** Who answers: a local Ollama model (free), a paid API, or offline rules. */
export type CoachStatus = { mode: 'ollama' | 'api' | 'offline'; model: string | null };

export type Status = {
  mode: string;
  garmin_ready: boolean;
  activity_count: number;
  last_sync_at: string | null;
  coach: CoachStatus;
};

export type ChatState = { messages: ChatMessage[]; coach: CoachStatus };

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
    readonly code: string | null,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

const isWeb = Platform.OS === 'web' && typeof window !== 'undefined';
/** The site published online, as opposed to the Expo dev server. */
const isOnlineSite = isWeb && !__DEV__;

export function apiBaseUrl(): string {
  const configured = process.env.EXPO_PUBLIC_API_URL;
  if (configured) {
    return configured.replace(/\/+$/, '');
  }
  // On the web the API is on the same address: online the backend serves the site, in development the
  // Expo dev server forwards /api to it (metro.config.js), also through tunnels.
  if (isWeb) {
    return window.location.origin;
  }
  const hostUri = Constants.expoConfig?.hostUri;
  return __DEV__ && hostUri ? `http://${hostUri}` : 'http://localhost:8000';
}

// Also written by public/index.html when the site is opened with a link ending in #codice=….
const ACCESS_CODE_KEY = 'coach-connect-access-code';

let accessCode = (isWeb ? window.localStorage.getItem(ACCESS_CODE_KEY) : null) ?? process.env.EXPO_PUBLIC_API_TOKEN ?? null;
const unauthorizedListeners = new Set<() => void>();

export function setAccessCode(code: string) {
  accessCode = code;
  if (isWeb) {
    window.localStorage.setItem(ACCESS_CODE_KEY, code);
  }
}

/** Called when the backend rejects the access code. */
export function onUnauthorized(listener: () => void): () => void {
  unauthorizedListeners.add(listener);
  return () => {
    unauthorizedListeners.delete(listener);
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = 30_000): Promise<T> {
  const token = accessCode;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  } catch (error) {
    const timedOut = controller.signal.aborted;
    throw new ApiError(
      timedOut ? 'Timeout' : `Errore di rete: ${String(error)}`,
      null,
      timedOut ? 'timeout' : 'network',
    );
  } finally {
    clearTimeout(timer);
  }

  const body: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    unauthorizedListeners.forEach((listener) => listener());
  }
  if (!response.ok) {
    const detail = isRecord(body) && typeof body.detail === 'string' ? body.detail : `HTTP ${response.status}`;
    const code = isRecord(body) && typeof body.code === 'string' ? body.code : null;
    throw new ApiError(detail, response.status, code);
  }
  return body as T;
}

const post = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) });

export const api = {
  status: () => request<Status>('/api/status'),
  feed: (offset = 0, limit = 50) => request<FeedPage>(`/api/feed?limit=${limit}&offset=${offset}`),
  // The first sync may import a long history, so it gets a generous timeout.
  sync: () => request<SyncResult>('/api/sync', { method: 'POST' }, 120_000),
  plan: () => request<Plan>('/api/plan'),
  exercises: () => request<ExerciseCatalog>('/api/exercises'),
  createWorkout: (workout: NewWorkout) => request<WorkoutDetail>('/api/workouts', post(workout)),
  workout: (id: number) => request<WorkoutDetail>(`/api/workouts/${id}`),
  deleteWorkout: (id: number) => request<null>(`/api/workouts/${id}`, { method: 'DELETE' }),
  wellness: (days = 14) => request<{ days: Wellness[] }>(`/api/wellness?days=${days}`),
  chat: () => request<ChatState>('/api/chat'),
  // A local model on a laptop can take a while to answer.
  sendChat: (content: string) => request<ChatState>('/api/chat', post({ content }), 200_000),
  clearChat: () => request<null>('/api/chat', { method: 'DELETE' }),
  // Garmin's login can be slow, especially from a server.
  garminLogin: (email: string, password: string) =>
    request<{ status: 'connected' | 'needs_code' }>('/api/garmin/login', post({ email, password }), 90_000),
  garminCode: (code: string) => request<{ status: 'connected' }>('/api/garmin/code', post({ code }), 90_000),
};

export function describeError(error: unknown): { title: string; message: string } {
  if (!(error instanceof ApiError)) {
    return {
      title: 'Qualcosa è andato storto',
      message: error instanceof Error ? error.message : String(error),
    };
  }
  switch (error.code) {
    case 'network':
      if (isOnlineSite) {
        return {
          title: 'Il sito non risponde',
          message: 'Se non lo aprivi da un paio di giorni si sta riaccendendo: riprova tra un minuto.',
        };
      }
      return {
        title: 'Server non raggiungibile',
        message:
          `Non riesco a contattare ${apiBaseUrl()}. Sul computer avvia "coach-connect/start.py" e tieni iPhone ` +
          'e computer sulla stessa rete Wi-Fi, oppure avvialo con --tunnel.',
      };
    case 'timeout':
      return { title: 'Il server non risponde', message: 'La richiesta ci sta mettendo troppo: riprova tra poco.' };
    case 'garmin_not_authenticated':
      return { title: 'Garmin non collegato', message: error.message };
    case 'garmin_rate_limited':
      return { title: 'Garmin chiede una pausa', message: error.message };
    case 'garmin_login_failed':
    case 'garmin_code_expired':
      return { title: 'Login Garmin non riuscito', message: error.message };
    case 'garmin_unavailable':
      return { title: 'Garmin non raggiungibile', message: error.message };
    case 'sync_in_progress':
      return { title: 'Sincronizzazione già in corso', message: 'Aspetta qualche secondo e riprova.' };
    case 'coach_unavailable':
      return { title: 'Coach AI non disponibile', message: error.message };
  }
  if (error.status === 401) {
    return { title: 'Codice di accesso non valido', message: 'Inserisci di nuovo il codice di accesso.' };
  }
  if (error.status === 422) {
    return { title: 'Dati non validi', message: error.message.startsWith('HTTP') ? 'Controlla i valori inseriti.' : error.message };
  }
  return { title: 'Errore del server', message: error.message };
}
