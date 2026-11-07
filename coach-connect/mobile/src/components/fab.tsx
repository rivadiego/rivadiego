import { SymbolView } from 'expo-symbols';
import { Pressable, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { colors, spacing } from '@/constants/theme';

type Props = {
  onPress: () => void;
  accessibilityLabel: string;
};

/** Round "+" button floating above the list (and above the native tab bar). */
export function Fab({ onPress, accessibilityLabel }: Props) {
  const insets = useSafeAreaInsets();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      style={({ pressed }) => [styles.fab, { bottom: insets.bottom + spacing.lg }, pressed && styles.pressed]}>
      <SymbolView name={{ ios: 'plus', android: 'add', web: 'add' }} size={26} weight="bold" tintColor={colors.onAccent} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    right: spacing.lg,
    width: 58,
    height: 58,
    borderRadius: 29,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.accent,
  },
  pressed: {
    opacity: 0.85,
    transform: [{ scale: 0.96 }],
  },
});
