import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, maxContentWidth, radius, spacing } from '@/constants/theme';
import { api, ApiError, describeError } from '@/lib/api';

type Step = 'credentials' | 'code' | 'syncing';

export default function GarminScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [step, setStep] = useState<Step>('credentials');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ title: string; message: string } | null>(null);

  const firstSync = async () => {
    setStep('syncing');
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    try {
      await api.sync();
      router.back();
    } catch (failure) {
      // The account is connected anyway: Aggiorna will try again.
      setError(describeError(failure));
    }
  };

  const submit = async () => {
    if (busy) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      if (step === 'credentials') {
        const result = await api.garminLogin(email.trim(), password);
        if (result.status === 'needs_code') {
          setStep('code');
          return;
        }
      } else {
        await api.garminCode(code.trim());
      }
      await firstSync();
    } catch (failure) {
      if (failure instanceof ApiError && failure.code === 'garmin_code_expired') {
        setStep('credentials');
        setCode('');
      }
      setError(describeError(failure));
    } finally {
      setBusy(false);
    }
  };

  const canSubmit = step === 'credentials' ? email.trim().length > 3 && password.length > 0 : code.trim().length >= 4;

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'left', 'right', 'bottom']}>
      <KeyboardAvoidingView style={styles.column} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.header}>
          <Pressable accessibilityRole="button" onPress={() => router.back()} hitSlop={10}>
            <Text style={styles.headerAction}>{step === 'syncing' ? 'Chiudi' : 'Annulla'}</Text>
          </Pressable>
          <Text style={styles.title}>Collega Garmin</Text>
          <View style={styles.headerSpacer} />
        </View>
        <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}>
          {step === 'credentials' && (
            <>
              <Text style={styles.intro}>
                Usa l&apos;email e la password di Garmin Connect. La password serve solo adesso: sul server restano i
                token di accesso, come nell&apos;app Garmin.
              </Text>
              <Text style={styles.label}>Email</Text>
              <TextInput
                value={email}
                onChangeText={setEmail}
                accessibilityLabel="Email Garmin"
                keyboardType="email-address"
                autoComplete="email"
                textContentType="username"
                autoCapitalize="none"
                autoCorrect={false}
                style={styles.input}
              />
              <Text style={styles.label}>Password</Text>
              <TextInput
                value={password}
                onChangeText={setPassword}
                onSubmitEditing={submit}
                accessibilityLabel="Password Garmin"
                secureTextEntry
                autoComplete="password"
                textContentType="password"
                autoCapitalize="none"
                returnKeyType="go"
                style={styles.input}
              />
            </>
          )}
          {step === 'code' && (
            <>
              <Text style={styles.intro}>
                Garmin ti ha mandato un codice di verifica (per email o nell&apos;app): inseriscilo qui.
              </Text>
              <Text style={styles.label}>Codice di verifica</Text>
              <TextInput
                value={code}
                onChangeText={setCode}
                onSubmitEditing={submit}
                accessibilityLabel="Codice di verifica"
                keyboardType="number-pad"
                autoComplete="one-time-code"
                textContentType="oneTimeCode"
                autoFocus
                maxLength={12}
                returnKeyType="go"
                style={[styles.input, styles.codeInput]}
              />
            </>
          )}
          {step === 'syncing' && (
            <View style={styles.syncing}>
              <Text style={styles.connected}>Garmin collegato</Text>
              {!error && (
                <>
                  <ActivityIndicator color={colors.textSecondary} />
                  <Text style={styles.intro}>Scarico attività e parametri vitali: la prima volta ci vuole un po&apos;.</Text>
                </>
              )}
            </View>
          )}

          {error ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorTitle}>{error.title}</Text>
              <Text style={styles.errorMessage}>{error.message}</Text>
            </View>
          ) : null}

          {step !== 'syncing' && (
            <Pressable
              accessibilityRole="button"
              disabled={busy || !canSubmit}
              onPress={submit}
              style={({ pressed }) => [styles.button, (pressed || busy || !canSubmit) && styles.dimmed]}>
              {busy ? (
                <ActivityIndicator color={colors.onAccent} />
              ) : (
                <Text style={styles.buttonLabel}>{step === 'code' ? 'Conferma codice' : 'Collega'}</Text>
              )}
            </Pressable>
          )}
        </ScrollView>
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  title: {
    color: colors.text,
    fontSize: 17,
    fontWeight: '700',
  },
  headerAction: {
    color: colors.textSecondary,
    fontSize: 16,
  },
  headerSpacer: {
    width: 56,
  },
  content: {
    gap: spacing.md,
    padding: spacing.lg,
  },
  intro: {
    color: colors.textSecondary,
    fontSize: 15,
    lineHeight: 21,
  },
  label: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginTop: spacing.sm,
  },
  input: {
    height: 48,
    paddingHorizontal: spacing.lg,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surfaceRaised,
    color: colors.text,
    fontSize: 16,
  },
  codeInput: {
    fontSize: 22,
    letterSpacing: 6,
    fontVariant: ['tabular-nums'],
  },
  syncing: {
    alignItems: 'center',
    gap: spacing.md,
    paddingVertical: spacing.xl,
  },
  connected: {
    color: colors.success,
    fontSize: 20,
    fontWeight: '800',
  },
  errorBox: {
    gap: spacing.xs,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: `${colors.danger}55`,
    backgroundColor: `${colors.danger}14`,
  },
  errorTitle: {
    color: colors.danger,
    fontSize: 14,
    fontWeight: '700',
  },
  errorMessage: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 18,
  },
  button: {
    height: 50,
    marginTop: spacing.sm,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
    backgroundColor: colors.accent,
  },
  buttonLabel: {
    color: colors.onAccent,
    fontSize: 16,
    fontWeight: '700',
  },
  dimmed: {
    opacity: 0.6,
  },
});
