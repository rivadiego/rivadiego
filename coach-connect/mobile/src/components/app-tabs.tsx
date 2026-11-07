import { NativeTabs } from 'expo-router/native-tabs';

import { colors } from '@/constants/theme';

/** Native tab bar on iPhone (Liquid Glass on iOS 26) and Android. */
export default function AppTabs() {
  return (
    <NativeTabs
      backgroundColor={colors.background}
      tintColor={colors.accent}
      iconColor={{ default: colors.textMuted, selected: colors.accent }}
      labelStyle={{ default: { color: colors.textMuted }, selected: { color: colors.text } }}
      indicatorColor={colors.surfaceRaised}>
      <NativeTabs.Trigger name="index">
        <NativeTabs.Trigger.Label>Attività</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon sf="list.bullet" md="format_list_bulleted" />
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="scheda">
        <NativeTabs.Trigger.Label>Scheda</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon sf="dumbbell.fill" md="fitness_center" />
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="coach">
        <NativeTabs.Trigger.Label>Coach</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon sf="bubble.left.and.bubble.right.fill" md="forum" />
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
