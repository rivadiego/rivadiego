#!/usr/bin/env python3
"""Avvia Coach Connect con un solo comando: prepara backend e app, collega Garmin e mostra il QR per Expo Go.

    python3 coach-connect/start.py          # con i tuoi dati Garmin (Windows: python coach-connect\\start.py)
    python3 coach-connect/start.py --demo   # con dati finti
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
MOBILE = ROOT / "mobile"
WINDOWS = os.name == "nt"
VENV_PYTHON = BACKEND / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")
STATUS_URL = "http://localhost:8000/api/status"
HAS_TOKENS = (
    "from coach_connect.config import Settings; from coach_connect.sources import TOKEN_FILE; "
    "print((Settings.from_env().token_dir / TOKEN_FILE).is_file())"
)


def say(message: str) -> None:
    print(f"\n==> {message}", flush=True)


def fail(message: str) -> None:
    print(f"\n{message}", file=sys.stderr)
    sys.exit(1)


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def node_tool(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    # npm and npx are .cmd scripts on Windows, which need the shell.
    if WINDOWS:
        return subprocess.run(" ".join(args), cwd=cwd, shell=True)
    return subprocess.run(args, cwd=cwd)


def find_python() -> list[str]:
    """An interpreter >= 3.12 (required by python-garminconnect) to create the backend environment."""
    candidates = [[sys.executable], ["python3.14"], ["python3.13"], ["python3.12"], ["python3"], ["python"]]
    if WINDOWS:
        candidates += [["py", "-3.14"], ["py", "-3.13"], ["py", "-3.12"]]
    for cmd in candidates:
        if shutil.which(cmd[0]) is None and not Path(cmd[0]).exists():
            continue
        check = subprocess.run([*cmd, "-c", "import sys; print(sys.version_info >= (3, 12))"],
                               capture_output=True, text=True)
        if check.stdout.strip() == "True":
            return cmd
    fail("Serve Python 3.12 o più recente: https://www.python.org/downloads/ (su Windows anche dal Microsoft Store, "
         "su Mac con `brew install python@3.13`).")
    return []


def check_node() -> None:
    node = shutil.which("node")
    if node is None or shutil.which("npm") is None:
        fail("Serve Node.js 22 o più recente: https://nodejs.org (versione LTS). Dopo l'installazione chiudi e riapri "
             "il terminale.")
    version = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip().lstrip("v")
    if int(version.split(".")[0]) < 22:
        fail(f"Hai Node.js {version}: serve la 22 o più recente (https://nodejs.org).")


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def up_to_date(stamp: Path, source: Path) -> bool:
    return stamp.exists() and stamp.read_text() == fingerprint(source)


def setup_backend(python: list[str]) -> None:
    if not VENV_PYTHON.exists():
        say("Creo l'ambiente Python del backend…")
        run([*python, "-m", "venv", str(BACKEND / ".venv")], BACKEND)
    requirements = BACKEND / "requirements.txt"
    stamp = BACKEND / ".venv" / ".requirements.sha256"
    if not up_to_date(stamp, requirements):
        say("Installo le dipendenze del backend…")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-q", "--upgrade", "pip"], BACKEND)
        run([str(VENV_PYTHON), "-m", "pip", "install", "-q", "-r", str(requirements)], BACKEND)
        stamp.write_text(fingerprint(requirements))


def setup_profile() -> None:
    env = BACKEND / ".env"
    if env.exists():
        return
    say("Due domande per il coach, solo la prima volta (Invio per saltare):")
    text = (BACKEND / ".env.example").read_text(encoding="utf-8")
    for key, question in (
        ("ATHLETE_NAME", "Come ti chiami?"),
        ("ATHLETE_HEIGHT_CM", "Altezza in cm?"),
        ("ATHLETE_WEIGHT_KG", "Peso in kg?"),
    ):
        answer = input(f"    {question} ").strip()
        if answer:
            text = re.sub(rf"^{key}=.*$", f"{key}={answer}", text, flags=re.MULTILINE)
    env.write_text(text, encoding="utf-8")


def setup_mobile() -> None:
    lockfile = MOBILE / "package-lock.json"
    stamp = MOBILE / "node_modules" / ".package-lock.sha256"
    if not up_to_date(stamp, lockfile):
        say("Installo le dipendenze dell'app (la prima volta ci vuole qualche minuto)…")
        if node_tool(["npm", "install", "--no-audit", "--no-fund"], MOBILE).returncode != 0:
            fail("npm install non è riuscito: guarda l'errore qui sopra.")
        stamp.write_text(fingerprint(lockfile))


def connect_garmin() -> None:
    has_tokens = subprocess.run([str(VENV_PYTHON), "-c", HAS_TOKENS], cwd=BACKEND, capture_output=True, text=True)
    if has_tokens.stdout.strip() != "True":
        say("Collego il tuo account Garmin: email, password e codice di verifica se attivo. "
            "La password non viene salvata, solo i token.")
        if subprocess.run([str(VENV_PYTHON), "-m", "coach_connect", "login"], cwd=BACKEND).returncode != 0:
            fail("Login a Garmin non riuscito: rilancia lo script per riprovare.")
    say("Scarico attività e parametri vitali da Garmin (la prima volta tutto lo storico)…")
    if subprocess.run([str(VENV_PYTHON), "-m", "coach_connect", "sync"], cwd=BACKEND).returncode != 0:
        print("Sync non riuscito: l'app parte comunque con i dati già scaricati.")


def total_ram_gb() -> float:
    try:
        if sys.platform == "darwin":
            return int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout) / 1e9
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9
    except (OSError, ValueError, AttributeError):
        return 8.0


def check_ollama() -> None:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as response:
            tags = json.load(response)
    except OSError:
        say("Coach AI: Ollama non è acceso, il coach risponderà in modalità offline. "
            "Per il coach gratuito installa https://ollama.com e rilancia lo script.")
        return
    models = [m["name"] for m in tags.get("models", []) if "embed" not in m["name"]]
    if models:
        say(f"Coach AI gratuito pronto con Ollama ({models[0]}).")
        return
    model = "qwen3:8b" if total_ram_gb() >= 15 else "qwen3:4b"
    answer = input(f"\n==> Ollama è acceso ma senza modelli. Scarico {model} per il coach (qualche GB)? [s/N] ")
    if answer.strip().lower() in {"s", "si", "sì", "y", "yes"}:
        run(["ollama", "pull", model], ROOT)


def backend_running() -> bool:
    try:
        with urllib.request.urlopen(STATUS_URL, timeout=1):
            return True
    except OSError:
        return False


def start_backend(demo: bool) -> subprocess.Popen | None:
    if backend_running():
        say("Il backend è già acceso.")
        return None
    (BACKEND / "data").mkdir(exist_ok=True)
    log = (BACKEND / "data" / "server.log").open("a")
    cmd = [str(VENV_PYTHON), "-m", "coach_connect", "serve", *(["--demo"] if demo else [])]
    process = subprocess.Popen(cmd, cwd=BACKEND, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(60):
        if backend_running():
            say("Backend acceso (log in coach-connect/backend/data/server.log).")
            return process
        if process.poll() is not None:
            break
        time.sleep(0.5)
    fail("Il backend non è partito: guarda coach-connect/backend/data/server.log.")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Avvia Coach Connect: backend, collegamento Garmin e app.")
    parser.add_argument("--demo", action="store_true", help="usa dati finti, senza account Garmin")
    args = parser.parse_args()

    python = find_python()
    check_node()
    setup_backend(python)
    setup_profile()
    setup_mobile()
    if not args.demo:
        connect_garmin()
    check_ollama()
    backend = start_backend(args.demo)
    say("Ora apro l'app. Sull'iPhone: apri la Fotocamera e inquadra il QR (serve Expo Go, stessa rete Wi-Fi "
        "del computer). Ctrl+C qui per chiudere tutto.")
    try:
        node_tool(["npx", "expo", "start"], MOBILE)
    except KeyboardInterrupt:
        pass
    finally:
        if backend is not None:
            backend.terminate()


if __name__ == "__main__":
    main()
