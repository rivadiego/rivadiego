import Constants from 'expo-constants';
import { Platform } from 'react-native';

import type { Sport } from '@/lib/sports';

export type Activity = {
  id: number;
  name: string;
  sport: Sport;
  type_key: string;
  /** Wall-clock time where the activity happened, e.g. "2026-10-18T07:35:27". */
  start_time_local: string | null;
  start_time_utc: string | null;
  duration_s: number | null;
  moving_duration_s: number | null;
  distance_m: number | null;
  elevation_gain_m: number | null;
  avg_speed_mps: number | null;
  avg_hr: number | null;
  max_hr: number | null;
  calories: number | null;
  training_load: number | null;
  aerobic_te: number | null;
  location: string | null;
};

export type ActivityPage = {
  items: Activity[];
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
};

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

export function apiBaseUrl(): string {
  const configured = process.env.EXPO_PUBLIC_API_URL;
  if (configured) {
    return configured.replace(/\/+$/, '');
  }
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  // In development the iPhone already reaches the computer running Expo: reuse its address.
  const host = Constants.expoConfig?.hostUri?.split(':')[0];
  return `http://${host ?? 'localhost'}:8000`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = 30_000): Promise<T> {
  const token = process.env.EXPO_PUBLIC_API_TOKEN;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
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
  if (!response.ok) {
    const detail = isRecord(body) && typeof body.detail === 'string' ? body.detail : `HTTP ${response.status}`;
    const code = isRecord(body) && typeof body.code === 'string' ? body.code : null;
    throw new ApiError(detail, response.status, code);
  }
  return body as T;
}

export const api = {
  activities: (offset = 0, limit = 50) =>
    request<ActivityPage>(`/api/activities?limit=${limit}&offset=${offset}`),
  // The first sync may import a long history, so it gets a generous timeout.
  sync: () => request<SyncResult>('/api/sync', { method: 'POST' }, 120_000),
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
      return {
        title: 'Server non raggiungibile',
        message:
          `Non riesco a contattare ${apiBaseUrl()}. Sul computer avvia ` +
          '"python -m garmin_hub serve" e tieni iPhone e computer sulla stessa rete Wi-Fi.',
      };
    case 'timeout':
      return { title: 'Il server non risponde', message: 'La richiesta ci sta mettendo troppo: riprova tra poco.' };
    case 'garmin_not_authenticated':
      return { title: 'Garmin non collegato', message: error.message };
    case 'garmin_rate_limited':
      return { title: 'Garmin chiede una pausa', message: error.message };
    case 'sync_in_progress':
      return { title: 'Sincronizzazione già in corso', message: 'Aspetta qualche secondo e riprova.' };
  }
  if (error.status === 401) {
    return {
      title: 'Accesso negato',
      message: "Il token dell'app non corrisponde ad API_TOKEN del backend: controlla EXPO_PUBLIC_API_TOKEN.",
    };
  }
  return { title: 'Errore del server', message: error.message };
}
