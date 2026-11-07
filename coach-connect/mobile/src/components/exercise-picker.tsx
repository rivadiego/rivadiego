import { SymbolView } from 'expo-symbols';
import { useMemo, useState } from 'react';
import { Modal, Pressable, SectionList, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, maxContentWidth, radius, spacing } from '@/constants/theme';
import type { Exercise } from '@/lib/api';
import { EQUIPMENT_LABELS } from '@/lib/workout-draft';

type Props = {
  visible: boolean;
  exercises: Exercise[];
  groups: string[];
  onSelect: (exercise: Exercise) => void;
  onClose: () => void;
};

export function ExercisePicker({ visible, exercises, groups, onSelect, onClose }: Props) {
  const [query, setQuery] = useState('');
  const sections = useMemo(() => {
    const q = query.trim().toLowerCase();
    const matching = exercises.filter((e) => !q || e.name.toLowerCase().includes(q) || e.group.toLowerCase().includes(q));
    return groups
      .map((group) => ({ title: group, data: matching.filter((e) => e.group === group) }))
      .filter((section) => section.data.length > 0);
  }, [exercises, groups, query]);

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <SafeAreaView style={styles.screen} edges={['top', 'left', 'right']}>
        <View style={styles.column}>
          <View style={styles.header}>
            <Text style={styles.title}>Aggiungi esercizio</Text>
            <Pressable accessibilityRole="button" onPress={onClose} hitSlop={10}>
              <Text style={styles.close}>Chiudi</Text>
            </Pressable>
          </View>
          <View style={styles.search}>
            <SymbolView name={{ ios: 'magnifyingglass', android: 'search', web: 'search' }} size={16} tintColor={colors.textMuted} />
            <TextInput
              value={query}
              onChangeText={setQuery}
              placeholder="Cerca (es. panca, schiena)"
              placeholderTextColor={colors.textMuted}
              autoCorrect={false}
              style={styles.searchInput}
            />
          </View>
          <SectionList
            sections={sections}
            keyExtractor={(item) => item.id}
            keyboardShouldPersistTaps="handled"
            stickySectionHeadersEnabled={false}
            contentContainerStyle={styles.list}
            renderSectionHeader={({ section }) => <Text style={styles.group}>{section.title}</Text>}
            renderItem={({ item }) => (
              <Pressable
                accessibilityRole="button"
                onPress={() => {
                  setQuery('');
                  onSelect(item);
                }}
                style={({ pressed }) => [styles.row, pressed && styles.pressed]}>
                <Text style={styles.name}>{item.name}</Text>
                <Text style={styles.equipment}>{EQUIPMENT_LABELS[item.equipment] ?? item.equipment}</Text>
              </Pressable>
            )}
          />
        </View>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  column: {
    flex: 1,
    width: '100%',
    maxWidth: maxContentWidth,
    alignSelf: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  title: {
    color: colors.text,
    fontSize: 20,
    fontWeight: '800',
  },
  close: {
    color: colors.accent,
    fontSize: 16,
    fontWeight: '600',
  },
  search: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginHorizontal: spacing.lg,
    marginBottom: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.surfaceRaised,
  },
  searchInput: {
    flex: 1,
    height: 44,
    color: colors.text,
    fontSize: 16,
  },
  list: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  group: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    paddingTop: spacing.lg,
    paddingBottom: spacing.xs,
  },
  row: {
    paddingVertical: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    gap: 2,
  },
  name: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
  equipment: {
    color: colors.textSecondary,
    fontSize: 12,
  },
  pressed: {
    opacity: 0.6,
  },
});
