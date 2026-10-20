#!/usr/bin/env python3
"""Pubblica Coach Connect su Hugging Face Spaces: sito e backend nello Space, dati in un dataset privato.

Lo lancia la GitHub Action .github/workflows/coach-connect-online.yml a ogni modifica. Variabili d'ambiente:
    HF_TOKEN            token Hugging Face con permesso "write"
    COACH_ACCESS_CODE   codice di accesso dell'app (almeno 8 caratteri)
    LLM_BASE_URL, LLM_MODEL, LLM_API_KEY   facoltative: coach AI con un servizio compatibile OpenAI
    SPACE_NAME, DATA_NAME                  facoltative: nomi di Space e dataset

    python coach-connect/deploy/deploy_hf.py --web coach-connect/mobile/dist [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WAIT_S = 25 * 60
SPACE_README = """---
title: Coach Connect
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
short_description: Allenamento ibrido con i dati Garmin
---

Coach Connect: attività Garmin, scheda palestra e coach. Pubblicato da GitHub; i dati stanno in un dataset privato
e l'app chiede un codice di accesso.
"""


def stage(web_dir: Path, target: Path) -> None:
    skip = shutil.ignore_patterns(
        ".venv", "data", "tests", "__pycache__", "*.pyc", ".pytest_cache", ".env", "requirements-dev.txt"
    )
    shutil.copytree(ROOT / "backend", target / "backend", ignore=skip)
    shutil.copytree(web_dir, target / "web")
    shutil.copy(ROOT / "deploy" / "Dockerfile", target / "Dockerfile")
    (target / "README.md").write_text(SPACE_README, encoding="utf-8")


def fetch(url: str, token: str | None = None, *, method: str = "GET", timeout: float = 60) -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        method=method,
        data=b"" if method == "POST" else None,
        headers={"Authorization": f"Bearer {token}"} if token else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except OSError as exc:
        return 0, str(exc)


def print_logs(space_id: str, token: str, kind: str) -> None:
    """Tail of the build or run logs, which Hugging Face streams as server-sent events."""
    request = urllib.request.Request(
        f"https://huggingface.co/api/spaces/{space_id}/logs/{kind}", headers={"Authorization": f"Bearer {token}"}
    )
    lines: list[str] = []
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            for raw in response:
                line = raw.decode("utf-8", "replace").strip()
                if line.startswith("data:"):
                    try:
                        lines.append(json.loads(line[5:]).get("data", "").rstrip())
                    except json.JSONDecodeError:
                        lines.append(line[5:].strip())
    except OSError:
        pass
    print(f"--- ultimi log ({kind}) ---")
    print("\n".join(lines[-60:]) or "(nessun log)")


def wait_for_site(api, space_id: str, url: str, entry: str, token: str) -> None:
    """Until the site serves this build (its entry script), reporting the Space stage on the way."""
    deadline = time.monotonic() + WAIT_S
    last_stage = None
    while time.monotonic() < deadline:
        stage_now = api.get_space_runtime(space_id).stage
        if stage_now != last_stage:
            print(f"Space: {stage_now}", flush=True)
            last_stage = stage_now
        if stage_now in {"BUILD_ERROR", "CONFIG_ERROR", "NO_APP_FILE"}:
            print_logs(space_id, token, "build")
            sys.exit(f"Lo Space non si è costruito ({stage_now}).")
        if stage_now == "RUNTIME_ERROR":
            print_logs(space_id, token, "run")
            sys.exit("Lo Space si è costruito ma l'app non parte (RUNTIME_ERROR).")
        if stage_now == "RUNNING":
            status, html = fetch(url)
            if status == 200 and entry in html:
                return
        time.sleep(15)
    sys.exit(f"Dopo {WAIT_S // 60} minuti il sito non serve ancora la nuova versione.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pubblica Coach Connect su Hugging Face Spaces.")
    parser.add_argument("--web", type=Path, required=True, help="cartella del sito (npx expo export -p web)")
    parser.add_argument("--dry-run", action="store_true", help="prepara i file dello Space senza pubblicarli")
    args = parser.parse_args()

    entry = re.search(r"/_expo/static/js/web/entry-[\w-]+\.js", (args.web / "index.html").read_text())
    if entry is None:
        sys.exit(f"{args.web} non sembra un export web di Expo.")
    if args.dry_run:
        with tempfile.TemporaryDirectory() as tmp:
            stage(args.web, Path(tmp))
            files = sorted(str(p.relative_to(tmp)) for p in Path(tmp).rglob("*") if p.is_file())
            print(f"{len(files)} file per lo Space, per esempio:", *files[:12], sep="\n  ")
        return 0

    token = os.getenv("HF_TOKEN")
    code = os.getenv("COACH_ACCESS_CODE") or ""
    if not token:
        sys.exit("Manca HF_TOKEN.")
    if len(code) < 8:
        sys.exit("COACH_ACCESS_CODE manca o è più corto di 8 caratteri.")

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    user = api.whoami()["name"]
    space_id = f"{user}/{os.getenv('SPACE_NAME') or 'coach-connect'}"
    data_id = f"{user}/{os.getenv('DATA_NAME') or 'coach-connect-data'}"

    api.create_repo(data_id, repo_type="dataset", private=True, exist_ok=True)
    api.create_repo(space_id, repo_type="space", space_sdk="docker", exist_ok=True)
    api.add_space_secret(space_id, "API_TOKEN", code)
    api.add_space_secret(space_id, "HF_TOKEN", token)
    api.add_space_variable(space_id, "HF_DATA_REPO", data_id)
    for key in ("LLM_BASE_URL", "LLM_MODEL"):
        if os.getenv(key):
            api.add_space_variable(space_id, key, os.environ[key])
    if os.getenv("LLM_API_KEY"):
        api.add_space_secret(space_id, "LLM_API_KEY", os.environ["LLM_API_KEY"])

    with tempfile.TemporaryDirectory() as tmp:
        stage(args.web, Path(tmp))
        commit = api.upload_folder(
            repo_id=space_id,
            repo_type="space",
            folder_path=tmp,
            commit_message=f"Coach Connect {os.getenv('GITHUB_SHA', '')[:7]}".strip(),
            delete_patterns=["backend/**", "web/**"],
        )
    print(f"Caricato su {space_id}: {commit.commit_url}")

    url = api.space_info(space_id).host or f"https://{space_id.replace('/', '-').lower()}.hf.space"
    wait_for_site(api, space_id, url, entry.group(0), token)
    protected, _ = fetch(f"{url}/api/status")
    status, body = fetch(f"{url}/api/status", code)
    if protected != 401 or status != 200:
        sys.exit(f"Il sito risponde ma l'API no: senza codice {protected}, con il codice {status}.")
    saved, detail = fetch(f"{url}/api/backup", code, method="POST")
    if saved != 200:
        sys.exit(f"Il salvataggio sul dataset privato non funziona ({saved}): {detail}")
    # These logs are public on a public repository: nothing personal beyond this.
    info = json.loads(body)
    print(f"Online: {url}")
    print(f"API protetta dal codice, salvataggio sul dataset privato ok. "
          f"Garmin collegato: {'sì' if info['garmin_ready'] else 'no'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
