import { Pressable, StyleSheet, Text } from 'react-native';

import { colors, radius, spacing } from '@/constants/theme';

export type Notice = {
  tone: 'success' | 'info' | 'error';
  title: string;
  message?: string;
};

const TONE_COLORS: Record<Notice['tone'], string> = {
  success: colors.success,
  info: colors.textSecondary,
  error: colors.danger,
};

type Props = {
  notice: Notice;
  onDismiss: () => void;
};

export function NoticeBanner({ notice, onDismiss }: Props) {
  const tint = TONE_COLORS[notice.tone];
  return (
    <Pressable
      accessibilityRole="alert"
      accessibilityHint="Tocca per chiudere"
      onPress={onDismiss}
      style={[styles.banner, { borderColor: `${tint}55`, backgroundColor: `${tint}14` }]}>
      <Text style={[styles.title, { color: tint }]}>{notice.title}</Text>
      {notice.message && <Text style={styles.message}>{notice.message}</Text>}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  banner: {
    gap: spacing.xs,
    marginHorizontal: spacing.lg,
    marginBottom: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '700',
  },
  message: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 18,
  },
});
