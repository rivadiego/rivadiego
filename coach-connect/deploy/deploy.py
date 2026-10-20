#!/usr/bin/env python3
"""Pubblica Coach Connect online: servizio web gratuito su Render, dati in un dataset privato su Hugging Face.

Lo usa la GitHub Action .github/workflows/coach-connect-online.yml, in due passi:

    python coach-connect/deploy/deploy.py --web coach-connect/mobile/dist --stage DIR
        prepara in DIR quello che va nel ramo deploy/coach-connect, da cui Render costruisce il servizio
    python coach-connect/deploy/deploy.py --web coach-connect/mobile/dist --publish
        crea o aggiorna il servizio su Render, lo pubblica e controlla che funzioni

Variabili d'ambiente per --publish:
    RENDER_API_KEY      chiave API di Render (Account Settings → API Keys)
    HF_TOKEN            token Hugging Face con permesso "write", per il dataset dei dati
    COACH_ACCESS_CODE   codice di accesso dell'app (almeno 8 caratteri)
    GITHUB_REPOSITORY   repository da cui Render costruisce (lo imposta GitHub)
    LLM_BASE_URL, LLM_MODEL, LLM_API_KEY   facoltative: coach AI con un servizio compatibile OpenAI
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RENDER_API = "https://api.render.com/v1"
SERVICE_NAME = "coach-connect"
DEPLOY_BRANCH = "deploy/coach-connect"
WAIT_S = 25 * 60
FAILED = {"build_failed", "update_failed", "pre_deploy_failed", "canceled", "deactivated"}
BRANCH_README = """# Coach Connect: versione pubblicata

Ramo generato dalla GitHub Action "Coach Connect online": Render costruisce il servizio da qui.
Non modificarlo a mano: il codice è in `coach-connect/` e questo ramo viene riscritto a ogni pubblicazione.
"""


def stage(web_dir: Path, target: Path) -> None:
    skip = shutil.ignore_patterns(
        ".venv", "data", "tests", "__pycache__", "*.pyc", ".pytest_cache", ".env", "requirements-dev.txt"
    )
    shutil.copytree(ROOT / "backend", target / "backend", ignore=skip)
    shutil.copytree(web_dir, target / "web")
    shutil.copy(ROOT / "deploy" / "Dockerfile", target / "Dockerfile")
    (target / "README.md").write_text(BRANCH_README, encoding="utf-8")


def request(method: str, url: str, token: str | None = None, body: Any = None, timeout: float = 60) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif method == "POST":
        data = b""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data, headers, method=method), timeout=timeout) as r:
            status, text = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        status, text = exc.code, exc.read().decode("utf-8", "replace")
    except OSError as exc:
        return 0, str(exc)
    try:
        return status, json.loads(text)
    except json.JSONDecodeError:
        return status, text


class Render:
    def __init__(self, key: str) -> None:
        self.key = key

    def __call__(self, method: str, path: str, body: Any = None) -> Any:
        status, payload = request(method, f"{RENDER_API}{path}", self.key, body)
        if not 200 <= status < 300:
            sys.exit(f"Render ha risposto {status} a {method} {path.split('?')[0]}: {payload}")
        return payload

    def print_logs(self, owner_id: str, service_id: str) -> None:
        status, payload = request(
            "GET",
            f"{RENDER_API}/logs?ownerId={owner_id}&resource={service_id}&limit=80&direction=backward",
            self.key,
        )
        logs = payload.get("logs", []) if status == 200 and isinstance(payload, dict) else []
        print("--- ultimi log di Render ---")
        print("\n".join(entry.get("message", "") for entry in reversed(logs)) or "(log non disponibili)")


def wait_for_deploy(render: Render, owner_id: str, service_id: str, deploy_id: str) -> None:
    deadline = time.monotonic() + WAIT_S
    last = None
    while time.monotonic() < deadline:
        status = render("GET", f"/services/{service_id}/deploys/{deploy_id}")["status"]
        if status != last:
            print(f"Render: {status}", flush=True)
            last = status
        if status == "live":
            return
        if status in FAILED:
            render.print_logs(owner_id, service_id)
            sys.exit(f"La pubblicazione su Render non è riuscita ({status}).")
        time.sleep(10)
    sys.exit(f"Dopo {WAIT_S // 60} minuti la pubblicazione su Render non è ancora finita.")


def wait_for_site(url: str, entry: str) -> None:
    """Until the site serves this build: a free instance can take a minute to wake up."""
    deadline = time.monotonic() + 5 * 60
    while time.monotonic() < deadline:
        status, html = request("GET", url, timeout=90)
        if status == 200 and isinstance(html, str) and entry in html:
            return
        time.sleep(10)
    sys.exit(f"{url} non serve la nuova versione del sito.")


def publish(web_entry: str) -> None:
    key = os.getenv("RENDER_API_KEY") or ""
    hf_token = os.getenv("HF_TOKEN") or ""
    code = os.getenv("COACH_ACCESS_CODE") or ""
    repository = os.getenv("GITHUB_REPOSITORY") or ""
    if not (key and hf_token and repository):
        sys.exit("Servono RENDER_API_KEY, HF_TOKEN e GITHUB_REPOSITORY.")
    if len(code) < 8:
        sys.exit("COACH_ACCESS_CODE manca o è più corto di 8 caratteri.")

    from huggingface_hub import HfApi

    hub = HfApi(token=hf_token)
    data_repo = f"{hub.whoami()['name']}/coach-connect-data"
    hub.create_repo(data_repo, repo_type="dataset", private=True, exist_ok=True)

    env_vars = [
        {"key": "API_TOKEN", "value": code},
        {"key": "HF_TOKEN", "value": hf_token},
        {"key": "HF_DATA_REPO", "value": data_repo},
    ]
    env_vars += [{"key": k, "value": os.environ[k]} for k in ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY") if os.getenv(k)]

    render = Render(key)
    owner_id = render("GET", "/owners?limit=20")[0]["owner"]["id"]
    found = [item["service"] for item in render("GET", f"/services?name={SERVICE_NAME}&limit=20")]
    service = next((s for s in found if s["name"] == SERVICE_NAME), None)
    if service is None:
        created = render(
            "POST",
            "/services",
            {
                "type": "web_service",
                "name": SERVICE_NAME,
                "ownerId": owner_id,
                "repo": f"https://github.com/{repository}",
                "branch": DEPLOY_BRANCH,
                "autoDeploy": "no",
                "envVars": env_vars,
                "serviceDetails": {
                    "runtime": "docker",
                    "plan": "free",
                    "region": "frankfurt",
                    "envSpecificDetails": {"dockerfilePath": "./Dockerfile", "dockerContext": "."},
                },
            },
        )
        service, deploy_id = created["service"], created["deployId"]
        print(f"Creato il servizio {SERVICE_NAME} su Render (piano gratuito, Francoforte).")
    else:
        render("PUT", f"/services/{service['id']}/env-vars", env_vars)
        deploy_id = render("POST", f"/services/{service['id']}/deploys", {"clearCache": "do_not_clear"})["id"]

    wait_for_deploy(render, owner_id, service["id"], deploy_id)
    url = render("GET", f"/services/{service['id']}")["serviceDetails"]["url"]
    wait_for_site(url, web_entry)

    protected, _ = request("GET", f"{url}/api/status")
    status, info = request("GET", f"{url}/api/status", code)
    if protected != 401 or status != 200:
        sys.exit(f"Il sito risponde ma l'API no: senza codice {protected}, con il codice {status}.")
    saved, detail = request("POST", f"{url}/api/backup", code)
    if saved != 200:
        sys.exit(f"Il salvataggio sul dataset privato non funziona ({saved}): {detail}")
    # These logs are public on a public repository: nothing personal beyond this.
    print(f"Online: {url}")
    print(f"API protetta dal codice, salvataggio sul dataset privato ok. "
          f"Garmin collegato: {'sì' if info['garmin_ready'] else 'no'}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pubblica Coach Connect online (Render + dataset Hugging Face).")
    parser.add_argument("--web", type=Path, required=True, help="cartella del sito (npx expo export -p web)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", type=Path, metavar="DIR", help="prepara il contenuto del ramo di pubblicazione")
    mode.add_argument("--publish", action="store_true", help="pubblica su Render e controlla il risultato")
    args = parser.parse_args()

    entry = re.search(r"/_expo/static/js/web/entry-[\w-]+\.js", (args.web / "index.html").read_text())
    if entry is None:
        sys.exit(f"{args.web} non sembra un export web di Expo.")
    if args.stage:
        args.stage.mkdir(parents=True, exist_ok=True)
        stage(args.web, args.stage)
        print(f"Pronto in {args.stage}: {sum(1 for p in args.stage.rglob('*') if p.is_file())} file.")
    else:
        publish(entry.group(0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
