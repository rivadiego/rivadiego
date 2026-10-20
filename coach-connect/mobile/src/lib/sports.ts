import type { SymbolViewProps } from 'expo-symbols';

export type Sport =
  | 'run'
  | 'bike'
  | 'swim'
  | 'walk'
  | 'hike'
  | 'strength'
  | 'cardio'
  | 'mind_body'
  | 'winter'
  | 'water'
  | 'other';

type SportMeta = {
  label: string;
  color: string;
  symbol: SymbolViewProps['name'];
};

/** Mirrors the categories produced by the backend (coach_connect/normalize.py). */
const SPORTS: Record<Sport, SportMeta> = {
  run: {
    label: 'Corsa',
    color: '#4C8DFF',
    symbol: { ios: 'figure.run', android: 'directions_run', web: 'directions_run' },
  },
  bike: {
    label: 'Bici',
    color: '#38BDF8',
    symbol: { ios: 'figure.outdoor.cycle', android: 'directions_bike', web: 'directions_bike' },
  },
  swim: {
    label: 'Nuoto',
    color: '#22D3EE',
    symbol: { ios: 'figure.pool.swim', android: 'pool', web: 'pool' },
  },
  walk: {
    label: 'Camminata',
    color: '#7DD3FC',
    symbol: { ios: 'figure.walk', android: 'directions_walk', web: 'directions_walk' },
  },
  hike: {
    label: 'Escursione',
    color: '#60A5FA',
    symbol: { ios: 'figure.hiking', android: 'hiking', web: 'hiking' },
  },
  strength: {
    label: 'Forza',
    color: '#818CF8',
    symbol: { ios: 'dumbbell.fill', android: 'fitness_center', web: 'fitness_center' },
  },
  cardio: {
    label: 'Cardio',
    color: '#A78BFA',
    symbol: {
      ios: 'figure.highintensity.intervaltraining',
      android: 'exercise',
      web: 'exercise',
    },
  },
  mind_body: {
    label: 'Yoga e mobilità',
    color: '#93C5FD',
    symbol: { ios: 'figure.mind.and.body', android: 'self_improvement', web: 'self_improvement' },
  },
  winter: {
    label: 'Sport invernali',
    color: '#93C5FD',
    symbol: { ios: 'figure.skiing.downhill', android: 'downhill_skiing', web: 'downhill_skiing' },
  },
  water: {
    label: "Sport d'acqua",
    color: '#2DD4BF',
    symbol: { ios: 'figure.rower', android: 'rowing', web: 'rowing' },
  },
  other: {
    label: 'Altro',
    color: '#94A3B8',
    symbol: { ios: 'figure.mixed.cardio', android: 'sports', web: 'sports' },
  },
};

export function sportMeta(sport: string): SportMeta {
  return SPORTS[sport as Sport] ?? SPORTS.other;
}
