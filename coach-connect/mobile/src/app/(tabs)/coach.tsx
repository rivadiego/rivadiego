import * as Haptics from 'expo-haptics';
import { useFocusEffect } from 'expo-router';
import { SymbolView, type SymbolViewProps } from 'expo-symbols';
import { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  type ScrollViewInstance,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { RichText } from '@/components/rich-text';
import { colors, maxContentWidth, radius, spacing } from '@/constants/theme';
import { api, describeError, type ChatMessage, type Wellness } from '@/lib/api';
import { formatSleep } from '@/lib/format';

const SUGGESTIONS = [
  'Che carichi faccio oggi?',
  'Ho dormito male, cosa faccio?',
  "Com'è andata la settimana?",
  'Sono stanco, cosa taglio?',
];

type Vital = { label: string; value: string; symbol: SymbolViewProps['name'] };

function vitals(day: Wellness | undefined): Vital[] {
  if (!day) {
    return [];
  }
  const items: (Vital | null)[] = [
    day.sleep_seconds
      ? { label: 'Sonno', value: formatSleep(day.sleep_seconds) ?? '–', symbol: { ios: 'moon.zzz.fill', android: 'bedtime', web: 'bedtime' } }
      : null,
    day.hrv_last_night_ms
      ? { label: 'HRV', value: `${Math.round(day.hrv_last_night_ms)} ms`, symbol: { ios: 'waveform.path.ecg', android: 'monitor_heart', web: 'monitor_heart' } }
      : null,
    (day.body_battery_wake ?? day.body_battery_high) != null
      ? {
          label: 'Body Battery',
          value: String(Math.round((day.body_battery_wake ?? day.body_battery_high) as number)),
          symbol: { ios: 'bolt.heart.fill', android: 'battery_charging_full', web: 'battery_charging_full' },
        }
      : null,
    day.readiness_score != null
      ? { label: 'Readiness', value: String(Math.round(day.readiness_score)), symbol: { ios: 'sparkles', android: 'auto_awesome', web: 'auto_awesome' } }
      : null,
    day.resting_hr
      ? { label: 'FC riposo', value: String(Math.round(day.resting_hr)), symbol: { ios: 'heart.fill', android: 'favorite', web: 'favorite' } }
      : null,
  ];
  return items.filter((item): item is Vital => item !== null);
}

export default function CoachScreen() {
  const scrollRef = useRef<ScrollViewInstance>(null);
  const pendingId = useRef(-1);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [coachAi, setCoachAi] = useState(true);
  const [today, setToday] = useState<Wellness | undefined>();
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      Promise.all([api.chat(), api.wellness(1)])
        .then(([chat, wellness]) => {
          if (!active) {
            return;
          }
          setMessages(chat.messages);
          setCoachAi(chat.coach_ai);
          setToday(wellness.days[0]);
          setError(null);
        })
        .catch((e: unknown) => active && setError(describeError(e).title));
      return () => {
        active = false;
      };
    }, []),
  );

  const send = async (text: string) => {
    const content = text.trim();
    if (!content || sending) {
      return;
    }
    setInput('');
    setError(null);
    setSending(true);
    // Shown right away; replaced by the stored message (with its real id) when the reply arrives.
    const pending: ChatMessage = { id: pendingId.current, role: 'user', content, created_at: '' };
    pendingId.current -= 1;
    setMessages((list) => [...list, pending]);
    try {
      const result = await api.sendChat(content);
      setMessages((list) => [...list.filter((m) => m.id !== pending.id), ...result.messages]);
      setCoachAi(result.coach_ai);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    } catch (e) {
      const { title, message } = describeError(e);
      setError(`${title}: ${message}`);
      setMessages((list) => list.filter((m) => m.id !== pending.id));
      setInput(content);
    } finally {
      setSending(false);
    }
  };

  const reset = async () => {
    try {
      await api.clearChat();
      setMessages([]);
    } catch (e) {
      setError(describeError(e).title);
    }
  };

  const strip = vitals(today);

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'left', 'right']}>
      <KeyboardAvoidingView style={styles.column} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <Text style={styles.title}>Coach</Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Nuova chat"
              onPress={reset}
              hitSlop={10}
              style={({ pressed }) => [styles.iconButton, pressed && styles.pressed]}>
              <SymbolView name={{ ios: 'square.and.pencil', android: 'edit', web: 'edit' }} size={20} tintColor={colors.accent} />
            </Pressable>
          </View>
          <Text style={styles.summary}>Il tuo personal trainer: vede scheda, allenamenti e parametri vitali degli ultimi 14 giorni.</Text>
          {strip.length > 0 && (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.vitals}>
              {strip.map((vital) => (
                <View key={vital.label} style={styles.vital}>
                  <SymbolView name={vital.symbol} size={14} tintColor={colors.accent} />
                  <Text style={styles.vitalValue}>{vital.value}</Text>
                  <Text style={styles.vitalLabel}>{vital.label}</Text>
                </View>
              ))}
            </ScrollView>
          )}
          {!coachAi && (
            <Text style={styles.offline}>
              Coach offline: risposte automatiche dai tuoi dati finché non colleghi un modello AI nel backend.
            </Text>
          )}
        </View>

        <ScrollView
          ref={scrollRef}
          style={styles.messages}
          contentContainerStyle={styles.messagesContent}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="interactive"
          onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: true })}>
          {messages.length === 0 && !sending ? (
            <View style={styles.empty}>
              <Text style={styles.emptyTitle}>Di cosa parliamo oggi?</Text>
              {SUGGESTIONS.map((suggestion) => (
                <Pressable
                  key={suggestion}
                  accessibilityRole="button"
                  onPress={() => send(suggestion)}
                  style={({ pressed }) => [styles.suggestion, pressed && styles.pressed]}>
                  <Text style={styles.suggestionLabel}>{suggestion}</Text>
                </Pressable>
              ))}
            </View>
          ) : null}
          {messages.map((message) => (
            <View key={message.id} style={[styles.bubble, message.role === 'user' ? styles.userBubble : styles.coachBubble]}>
              <RichText text={message.content} style={message.role === 'user' ? styles.userText : styles.coachText} />
            </View>
          ))}
          {sending ? (
            <View style={[styles.bubble, styles.coachBubble, styles.typing]}>
              <ActivityIndicator size="small" color={colors.textSecondary} />
              <Text style={styles.typingLabel}>Il coach sta scrivendo…</Text>
            </View>
          ) : null}
        </ScrollView>

        {error ? <Text style={styles.error}>{error}</Text> : null}
        <View style={styles.inputBar}>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="Scrivi al coach…"
            placeholderTextColor={colors.textMuted}
            multiline
            style={styles.input}
            accessibilityLabel="Messaggio per il coach"
          />
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Invia"
            disabled={!input.trim() || sending}
            onPress={() => send(input)}
            style={({ pressed }) => [styles.send, (!input.trim() || sending) && styles.sendDisabled, pressed && styles.pressed]}>
            <SymbolView name={{ ios: 'arrow.up', android: 'arrow_upward', web: 'arrow_upward' }} size={18} weight="bold" tintColor={colors.onAccent} />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
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
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: {
    color: colors.text,
    fontSize: 32,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.accentSoft,
  },
  summary: {
    color: colors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
  },
  vitals: {
    gap: spacing.sm,
  },
  vital: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  vitalValue: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
  vitalLabel: {
    color: colors.textSecondary,
    fontSize: 12,
  },
  offline: {
    color: colors.warning,
    fontSize: 12,
    lineHeight: 17,
  },
  messages: {
    flex: 1,
  },
  messagesContent: {
    gap: spacing.sm,
    padding: spacing.lg,
  },
  empty: {
    gap: spacing.sm,
    paddingVertical: spacing.lg,
  },
  emptyTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '700',
    marginBottom: spacing.xs,
  },
  suggestion: {
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  suggestionLabel: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '600',
  },
  bubble: {
    maxWidth: '88%',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: radius.lg,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: colors.accent,
    borderBottomRightRadius: radius.sm,
  },
  coachBubble: {
    alignSelf: 'flex-start',
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    borderBottomLeftRadius: radius.sm,
  },
  userText: {
    color: colors.onAccent,
    fontSize: 15,
    lineHeight: 21,
  },
  coachText: {
    color: colors.text,
    fontSize: 15,
    lineHeight: 21,
  },
  typing: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  typingLabel: {
    color: colors.textSecondary,
    fontSize: 14,
  },
  error: {
    color: colors.danger,
    fontSize: 13,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xs,
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    paddingHorizontal: spacing.lg,
    paddingTop: 12,
    paddingBottom: 12,
    borderRadius: 22,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    color: colors.text,
    fontSize: 15,
  },
  send: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.accent,
  },
  sendDisabled: {
    opacity: 0.4,
  },
  pressed: {
    opacity: 0.7,
  },
});
