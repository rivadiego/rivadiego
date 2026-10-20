/** Black and dark blue. */
export const colors = {
  background: '#000000',
  surface: '#08111F',
  surfaceRaised: '#0F1D33',
  border: '#172A47',
  text: '#F3F6FC',
  textSecondary: '#93A4C3',
  textMuted: '#5D6F91',
  accent: '#2F6BFF',
  accentSoft: '#2F6BFF26',
  onAccent: '#FFFFFF',
  success: '#34D399',
  warning: '#FBBF24',
  danger: '#FF6B6B',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = {
  sm: 6,
  md: 14,
  lg: 20,
  pill: 999,
} as const;

export const maxContentWidth = 720;
