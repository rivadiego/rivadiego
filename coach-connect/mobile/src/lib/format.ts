import type { FeedItem, Measure, SetValues } from '@/lib/api';
import type { Sport } from '@/lib/sports';

const WEEKDAYS = ['dom', 'lun', 'mar', 'mer', 'gio', 'ven', 'sab'];
const MONTHS_SHORT = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic'];
const MONTHS = [
  'Gennaio',
  'Febbraio',
  'Marzo',
  'Aprile',
  'Maggio',
  'Giugno',
  'Luglio',
  'Agosto',
  'Settembre',
  'Ottobre',
  'Novembre',
  'Dicembre',
];

const pad = (value: number) => String(value).padStart(2, '0');

const decimal = (value: number, digits: number) => value.toFixed(digits).replace('.', ',');

const grouped = (value: number) => Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');

/** Parses Garmin's local wall-clock time so it is shown as recorded, whatever the phone's timezone. */
export function parseLocalTime(iso: string): Date {
  const [datePart, timePart = '00:00:00'] = iso.split('T');
  const [year, month, day] = datePart.split('-').map(Number);
  const [hours, minutes, seconds] = timePart.split(':').map(Number);
  return new Date(year, month - 1, day, hours, minutes, seconds || 0);
}

const sameDay = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

export function formatActivityDate(iso: string | null, now: Date): string {
  if (!iso) {
    return '';
  }
  const date = parseLocalTime(iso);
  const time = `${pad(date.getHours())}:${pad(date.getMinutes())}`;
  const yesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  if (sameDay(date, now)) {
    return `Oggi · ${time}`;
  }
  if (sameDay(date, yesterday)) {
    return `Ieri · ${time}`;
  }
  return `${WEEKDAYS[date.getDay()]} ${date.getDate()} ${MONTHS_SHORT[date.getMonth()]} · ${time}`;
}

export function monthKey(iso: string | null): string {
  return iso ? iso.slice(0, 7) : '';
}

export function formatMonth(key: string): string {
  const [year, month] = key.split('-').map(Number);
  return year && month ? `${MONTHS[month - 1]} ${year}` : 'Senza data';
}

export function formatRelative(isoUtc: string | null, now: Date): string {
  if (!isoUtc) {
    return 'mai';
  }
  const minutes = Math.floor((now.getTime() - new Date(isoUtc).getTime()) / 60_000);
  if (minutes < 1) {
    return 'adesso';
  }
  if (minutes < 60) {
    return `${minutes} min fa`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} h fa`;
  }
  const days = Math.floor(hours / 24);
  return days === 1 ? 'ieri' : `${days} giorni fa`;
}

export function formatDuration(seconds: number | null): string | null {
  if (!seconds || seconds <= 0) {
    return null;
  }
  const total = Math.round(seconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

export function formatDistance(meters: number | null, sport: Sport): string | null {
  if (!meters || meters < 1) {
    return null;
  }
  return sport === 'swim' ? `${grouped(meters)} m` : `${decimal(meters / 1000, 2)} km`;
}

function formatPace(secondsPerUnit: number, unit: string): string {
  const total = Math.round(secondsPerUnit);
  return `${Math.floor(total / 60)}:${pad(total % 60)} ${unit}`;
}

/** Pace for foot sports and swimming, speed for the others; null when it isn't meaningful. */
export function formatPaceOrSpeed(activity: FeedItem): string | null {
  const speed = activity.avg_speed_mps;
  if (!speed || speed <= 0 || !activity.distance_m) {
    return null;
  }
  switch (activity.sport) {
    case 'run':
    case 'walk':
    case 'hike':
      return formatPace(1000 / speed, '/km');
    case 'swim':
      return formatPace(100 / speed, '/100 m');
    case 'bike':
    case 'winter':
    case 'water':
      return `${decimal(speed * 3.6, 1)} km/h`;
    default:
      return null;
  }
}

export function formatHeartRate(bpm: number | null): string | null {
  return bpm ? `${Math.round(bpm)} bpm` : null;
}

export function formatElevation(meters: number | null): string | null {
  return meters && meters >= 1 ? `+${grouped(meters)} m` : null;
}

export function formatCalories(kcal: number | null): string | null {
  return kcal ? `${grouped(kcal)} kcal` : null;
}

export function formatKg(kg: number | null | undefined): string {
  return kg == null ? '' : String(Math.round(kg * 100) / 100).replace('.', ',');
}

export function formatVolume(kg: number | null): string | null {
  return kg ? `${grouped(kg)} kg` : null;
}

export function formatSet(set: SetValues, measure: Measure): string {
  if (measure === 'seconds') {
    return `${set.seconds ?? '–'}"`;
  }
  if (set.note) {
    return `${set.note} × ${set.reps ?? '–'}`;
  }
  if (!set.weight_kg) {
    return `${set.reps ?? '–'} rip`;
  }
  return `${formatKg(set.weight_kg)} × ${set.reps ?? '–'}`;
}

export function formatSleep(seconds: number | null): string | null {
  if (!seconds) {
    return null;
  }
  const minutes = Math.round(seconds / 60);
  return `${Math.floor(minutes / 60)}h${pad(minutes % 60)}`;
}

/** "Oggi", "Ieri" or "lun 19 ott" for a "YYYY-MM-DD" date. */
export function formatDay(isoDate: string, now: Date): string {
  const date = parseLocalTime(isoDate);
  const yesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  if (sameDay(date, now)) {
    return 'Oggi';
  }
  if (sameDay(date, yesterday)) {
    return 'Ieri';
  }
  return `${WEEKDAYS[date.getDay()]} ${date.getDate()} ${MONTHS_SHORT[date.getMonth()]}`;
}

/** Accepts "61,25" as well as "61.25"; empty or invalid input is null. */
export function parseDecimal(text: string): number | null {
  const value = Number(text.trim().replace(',', '.'));
  return text.trim() && Number.isFinite(value) ? value : null;
}

/** Local time with its UTC offset, e.g. "2026-10-20T07:10:00+02:00". */
export function toLocalIso(date: Date): string {
  const offset = -date.getTimezoneOffset();
  const sign = offset >= 0 ? '+' : '-';
  const abs = Math.abs(offset);
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}:00${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`
  );
}
