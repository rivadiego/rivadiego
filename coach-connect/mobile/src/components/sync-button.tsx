import { SymbolView } from 'expo-symbols';
import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';

import { colors, radius, spacing } from '@/constants/theme';

type Props = {
  syncing: boolean;
  onPress: () => void;
};

export function SyncButton({ syncing, onPress }: Props) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="Aggiorna le attività da Garmin"
      accessibilityState={{ busy: syncing, disabled: syncing }}
      disabled={syncing}
      onPress={onPress}
      style={({ pressed }) => [styles.button, (pressed || syncing) && styles.dimmed]}>
      {syncing ? (
        <ActivityIndicator size="small" color={colors.onAccent} />
      ) : (
        <SymbolView
          name={{ ios: 'arrow.clockwise', android: 'refresh', web: 'refresh' }}
          size={16}
          weight="semibold"
          tintColor={colors.onAccent}
        />
      )}
      <Text style={styles.label}>{syncing ? 'Aggiorno…' : 'Aggiorna'}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    minHeight: 40,
    paddingHorizontal: spacing.lg,
    borderRadius: radius.pill,
    backgroundColor: colors.accent,
  },
  dimmed: {
    opacity: 0.75,
  },
  label: {
    color: colors.onAccent,
    fontSize: 15,
    fontWeight: '700',
  },
});
