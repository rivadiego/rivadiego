import { useEffect, useState, type ReactNode } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, radius, spacing } from '@/constants/theme';
import { api, ApiError, describeError, onUnauthorized, setAccessCode } from '@/lib/api';

/** Shows the app, or asks for the access code when the backend rejects it (the site online). */
export function AccessGate({ children }: { children: ReactNode }) {
  const [locked, setLocked] = useState(false);

  useEffect(() => onUnauthorized(() => setLocked(true)), []);

  // Unlocking mounts the screens again, so they reload their data with the new code.
  return locked ? <AccessScreen onUnlocked={() => setLocked(false)} /> : children;
}

function AccessScreen({ onUnlocked }: { onUnlocked: () => void }) {
  const [code, setCode] = useState('');
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    const value = code.trim();
    if (!value || checking) {
      return;
    }
    setChecking(true);
    setError(null);
    setAccessCode(value);
    try {
      await api.status();
      onUnlocked();
    } catch (failure) {
      setError(failure instanceof ApiError && failure.status === 401 ? 'Codice non valido.' : describeError(failure).message);
      setChecking(false);
    }
  };

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.card}>
        <Text style={styles.title}>Coach Connect</Text>
        <Text style={styles.message}>Inserisci il codice di accesso: questo dispositivo lo ricorderà.</Text>
        <TextInput
          value={code}
          onChangeText={setCode}
          onSubmitEditing={submit}
          placeholder="Codice di accesso"
          placeholderTextColor={colors.textMuted}
          accessibilityLabel="Codice di accesso"
          secureTextEntry
          autoCapitalize="none"
          autoCorrect={false}
          autoFocus
          returnKeyType="go"
          style={styles.input}
        />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Pressable
          accessibilityRole="button"
          disabled={checking}
          onPress={submit}
          style={({ pressed }) => [styles.button, (pressed || checking) && styles.pressed]}>
          {checking ? <ActivityIndicator color={colors.onAccent} /> : <Text style={styles.buttonLabel}>Entra</Text>}
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
    backgroundColor: colors.background,
  },
  card: {
    width: '100%',
    maxWidth: 400,
    gap: spacing.md,
    padding: spacing.xl,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  title: {
    color: colors.text,
    fontSize: 28,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  message: {
    color: colors.textSecondary,
    fontSize: 15,
    lineHeight: 21,
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
  error: {
    color: colors.danger,
    fontSize: 14,
  },
  button: {
    height: 48,
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
  pressed: {
    opacity: 0.7,
  },
});
