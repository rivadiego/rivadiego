"""Command line entry point: python -m garmin_hub <login|sync|status|serve>."""

from __future__ import annotations

import argparse
import getpass
import os
import sys

from .config import Settings
from .db import Database
from .sources import TOKEN_FILE, SourceError, build_source
from .sync import HISTORY_COMPLETE, LAST_SYNC_AT, Syncer


def cmd_login(settings: Settings) -> int:
    from garminconnect import (
        Garmin,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    )

    token_file = settings.token_dir / TOKEN_FILE
    print("Collegamento a Garmin Connect")
    print("La password serve solo adesso: vengono salvati unicamente i token di accesso.\n")
    email = input("Email Garmin: ").strip()
    password = getpass.getpass("Password Garmin: ")
    settings.token_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    if token_file.exists():
        # Otherwise login() would silently reuse the old session instead of the new credentials.
        token_file.unlink()
    client = Garmin(email, password, prompt_mfa=lambda: input("Codice di verifica (MFA): ").strip())
    try:
        client.login(str(settings.token_dir))
    except GarminConnectAuthenticationError as exc:
        print(f"\nLogin non riuscito: {exc}", file=sys.stderr)
        return 1
    except GarminConnectTooManyRequestsError:
        print("\nGarmin sta limitando i tentativi di login: aspetta qualche minuto e riprova.", file=sys.stderr)
        return 1
    except GarminConnectConnectionError as exc:
        print(f"\nGarmin Connect non raggiungibile: {exc}", file=sys.stderr)
        return 1
    if not token_file.exists():
        client.client.dump(str(settings.token_dir))
    print(f"\nCollegato come {client.get_full_name()}.")
    print(f"Token salvati in {token_file}: trattali come una password e non metterli mai su git.")
    return 0


def cmd_sync(settings: Settings, *, full: bool) -> int:
    source = build_source(settings)
    syncer = Syncer(
        source,
        Database(settings.db_path),
        page_size=settings.sync_page_size,
        pause_s=0.5 if source.mode == "live" else 0.0,
    )

    def progress(scanned: int, new: int) -> None:
        print(f"\r  {scanned} attività lette, {new} nuove", end="", flush=True)

    print(f"Sincronizzazione {'completa' if full else 'incrementale'} ({source.mode})...")
    try:
        result = syncer.run(full=full, progress=progress)
    except SourceError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1
    print(f"\nFatto: {result.new} nuove, {result.updated} aggiornate, {result.total} attività nel database.")
    return 0


def cmd_status(settings: Settings) -> int:
    source = build_source(settings)
    db = Database(settings.db_path)
    print(f"Modalità:         {'demo (dati finti)' if settings.demo else 'Garmin reale'}")
    if not settings.demo:
        tokens = "presenti" if source.is_ready() else "mancanti, esegui: python -m garmin_hub login"
        print(f"Token Garmin:     {tokens} ({settings.token_dir})")
    print(f"Database:         {settings.db_path}")
    print(f"Attività:         {db.count_activities()}")
    print(f"Ultimo sync:      {db.get_meta(LAST_SYNC_AT) or 'mai'}")
    print(f"Storico completo: {'sì' if db.get_meta(HISTORY_COMPLETE) == '1' else 'no'}")
    return 0


def cmd_serve(host: str, port: int, reload: bool) -> int:
    import uvicorn

    uvicorn.run("garmin_hub.api:create_app", factory=True, host=host, port=port, reload=reload)
    return 0


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--demo", action="store_true", help="usa dati finti, senza account Garmin")

    parser = argparse.ArgumentParser(
        prog="python -m garmin_hub",
        description="Garmin Hub: sincronizza le tue attività Garmin e le serve all'app.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("login", help="collega il tuo account Garmin (supporta MFA)")
    sync = sub.add_parser("sync", parents=[common], help="scarica le attività nel database locale")
    sync.add_argument("--full", action="store_true", help="rilegge tutto lo storico, non solo le novità")
    sub.add_parser("status", parents=[common], help="mostra lo stato del collegamento e del database")
    serve = sub.add_parser("serve", parents=[common], help="avvia l'API usata dall'app")
    serve.add_argument("--host", default="0.0.0.0", help="0.0.0.0 = raggiungibile dall'iPhone sulla stessa Wi-Fi")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true", help="riavvia da solo quando modifichi il codice")
    args = parser.parse_args(argv)

    if getattr(args, "demo", False):
        # Via the environment so that uvicorn's reload worker process sees it too.
        os.environ["GARMIN_DEMO"] = "1"
    if args.command == "serve":
        return cmd_serve(args.host, args.port, args.reload)
    settings = Settings.from_env()
    if args.command == "login":
        return cmd_login(settings)
    if args.command == "sync":
        return cmd_sync(settings, full=args.full)
    return cmd_status(settings)
