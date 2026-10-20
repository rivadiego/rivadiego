import { TabList, type TabListProps, TabSlot, TabTrigger, type TabTriggerSlotProps, Tabs } from 'expo-router/ui';
import { SymbolView, type SymbolViewProps } from 'expo-symbols';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { colors, maxContentWidth, spacing } from '@/constants/theme';

/** Web version: a bottom bar with icons, like the app on the phone. */
export default function AppTabs() {
  return (
    <Tabs style={styles.root}>
      <TabSlot style={styles.slot} />
      <TabList asChild>
        <BottomBar>
          <TabTrigger name="index" href="/" asChild>
            <TabButton label="Attività" symbol={{ web: 'format_list_bulleted' }} />
          </TabTrigger>
          <TabTrigger name="scheda" href="/scheda" asChild>
            <TabButton label="Scheda" symbol={{ web: 'fitness_center' }} />
          </TabTrigger>
          <TabTrigger name="coach" href="/coach" asChild>
            <TabButton label="Coach" symbol={{ web: 'forum' }} />
          </TabTrigger>
        </BottomBar>
      </TabList>
    </Tabs>
  );
}

function BottomBar(props: TabListProps) {
  return (
    <View {...props} style={styles.bar}>
      <View style={styles.inner}>{props.children}</View>
    </View>
  );
}

type TabButtonProps = TabTriggerSlotProps & { label: string; symbol: SymbolViewProps['name'] };

// expo-router types the slot ref for the old View class, which RN 0.88's Pressable rejects; navigation doesn't need it.
function TabButton({ label, symbol, isFocused, ref: _ref, ...props }: TabButtonProps) {
  return (
    <Pressable {...props} style={styles.button} accessibilityRole="tab" accessibilityState={{ selected: isFocused }}>
      <SymbolView name={symbol} size={22} tintColor={isFocused ? colors.accent : colors.textMuted} />
      <Text style={[styles.label, { color: isFocused ? colors.text : colors.textMuted }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.background,
  },
  slot: {
    flex: 1,
  },
  bar: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    backgroundColor: colors.background,
  },
  inner: {
    flexDirection: 'row',
    width: '100%',
    maxWidth: maxContentWidth,
    alignSelf: 'center',
    paddingVertical: spacing.sm,
  },
  button: {
    flex: 1,
    alignItems: 'center',
    gap: 2,
  },
  label: {
    fontSize: 11,
    fontWeight: '600',
  },
});
