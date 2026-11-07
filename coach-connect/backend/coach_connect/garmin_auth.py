"""Connect the Garmin account from the app: email and password, then the verification code if MFA is on."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from .sources import GarminRateLimited, GarminUnavailable, SourceError, brief


class GarminLoginFailed(SourceError):
    status_code = 400
    code = "garmin_login_failed"


class GarminCodeExpired(SourceError):
    status_code = 409
    code = "garmin_code_expired"


class GarminLogin:
    def __init__(self, token_dir: Path) -> None:
        self.token_dir = token_dir
        # The library keeps the half-finished login inside the client, so the same instance must get the code.
        self._waiting: Garmin | None = None
        self._lock = threading.Lock()

    def start(self, email: str, password: str) -> str:
        """Return "connected", or "needs_code" when Garmin sent a verification code."""
        client = Garmin(email, password, return_on_mfa=True)
        with _errors("Login non riuscito: controlla email e password."):
            status, _ = client.login()
        with self._lock:
            self._waiting = client if status == "needs_mfa" else None
        if status == "needs_mfa":
            return "needs_code"
        self._save(client)
        return "connected"

    def finish(self, code: str) -> str:
        with self._lock:
            client, self._waiting = self._waiting, None
        if client is None:
            raise GarminCodeExpired("Richiesta scaduta: inserisci di nuovo email e password.")
        try:
            with _errors("Codice non valido: controlla l'ultimo codice ricevuto e riprova."):
                client.resume_login({}, code)
        except GarminLoginFailed:
            with self._lock:
                self._waiting = client
            raise
        self._save(client)
        return "connected"

    def _save(self, client: Garmin) -> None:
        self.token_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        client.client.dump(str(self.token_dir))


@contextmanager
def _errors(rejected: str) -> Iterator[None]:
    try:
        yield
    except GarminConnectAuthenticationError as exc:
        raise GarminLoginFailed(rejected) from exc
    except GarminConnectTooManyRequestsError as exc:
        raise GarminRateLimited("Garmin sta limitando i tentativi di login: aspetta qualche minuto e riprova.") from exc
    except GarminConnectConnectionError as exc:
        raise GarminUnavailable(
            f"Garmin Connect non risponde da questo server: riprova tra qualche minuto. Dettaglio: {brief(exc)}"
        ) from exc
