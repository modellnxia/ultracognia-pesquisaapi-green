#!/usr/bin/env python3
"""
check_notebooklm_updates.py
Verifica se há atualizações disponíveis para a biblioteca notebooklm-py.

Uso:
    python scripts/check_notebooklm_updates.py
    python scripts/check_notebooklm_updates.py --github-output   # modo GitHub Actions
    python scripts/check_notebooklm_updates.py --json            # saída JSON
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests
from packaging.version import Version

# ─── Configurações ────────────────────────────────────────────────────────────

PACKAGE_NAME = os.environ.get("PYPI_NOTEBOOKLM_PACKAGE", "notebooklm-py")
PYPI_API_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
REQUIREMENTS_FILE = Path(__file__).parent.parent / "requirements.txt"
CHANGELOG_KEYWORDS = [
    "breaking",
    "breaking change",
    "removed",
    "deprecated",
    "incompatible",
    "migration",
    "upgrade guide",
]

# ─── Helpers ──────────────────────────────────────────────────────────────────


def get_current_version_from_requirements(req_file: Path) -> str | None:
    """Lê a versão fixada no requirements.txt."""
    if not req_file.exists():
        return None
    for line in req_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.lower().startswith(PACKAGE_NAME.lower()):
            # Suporta: notebooklm-py==1.2.3, notebooklm-py>=1.2.3, etc.
            match = re.search(r"[=<>!~]{1,2}([0-9]+\.[0-9]+(?:\.[0-9]+)?)", line)
            if match:
                return match.group(1)
    return None


def get_latest_version_from_pypi() -> tuple[str, str, str]:
    """
    Retorna (latest_version, release_date, release_notes_url) do PyPI.
    """
    try:
        response = requests.get(PYPI_API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        latest = data["info"]["version"]
        home_page = data["info"].get("home_page") or data["info"].get("project_url", "")
        # Obtém data do upload da versão mais recente
        releases = data.get("releases", {}).get(latest, [])
        release_date = ""
        if releases:
            release_date = releases[0].get("upload_time", "")[:10]
        return latest, release_date, home_page
    except requests.exceptions.RequestException as exc:
        print(f"[ERRO] Falha ao consultar PyPI: {exc}", file=sys.stderr)
        sys.exit(1)


def classify_update(current: str, latest: str) -> str:
    """
    Retorna o tipo de atualização: 'major', 'minor', 'patch' ou 'none'.
    """
    try:
        v_current = Version(current)
        v_latest = Version(latest)
    except Exception:
        return "unknown"

    if v_latest <= v_current:
        return "none"

    c_major, c_minor, c_patch = v_current.major, v_current.minor, v_current.micro
    l_major, l_minor, l_patch = v_latest.major, v_latest.minor, v_latest.micro

    if l_major > c_major:
        return "major"
    if l_minor > c_minor:
        return "minor"
    if l_patch > c_patch:
        return "patch"
    return "none"


def check_breaking_changes_in_changelog(version: str) -> bool:
    """
    Tenta detectar breaking changes nas release notes do GitHub.
    Retorna True se palavras-chave de breaking change forem encontradas.
    """
    # Tenta buscar release no GitHub (repositório oficial da lib)
    github_repos = [
        f"https://api.github.com/repos/jvnkr/notebooklm-py/releases/tags/v{version}",
        f"https://api.github.com/repos/jvnkr/notebooklm-py/releases/tags/{version}",
    ]
    for url in github_repos:
        try:
            resp = requests.get(url, timeout=10, headers={"Accept": "application/vnd.github+json"})
            if resp.status_code == 200:
                body = (resp.json().get("body") or "").lower()
                return any(kw in body for kw in CHANGELOG_KEYWORDS)
        except requests.exceptions.RequestException:
            continue
    return False


def get_github_release_notes(version: str) -> str:
    """Retorna as release notes do GitHub para a versão especificada."""
    github_urls = [
        f"https://api.github.com/repos/jvnkr/notebooklm-py/releases/tags/v{version}",
        f"https://api.github.com/repos/jvnkr/notebooklm-py/releases/tags/{version}",
    ]
    for url in github_urls:
        try:
            resp = requests.get(url, timeout=10, headers={"Accept": "application/vnd.github+json"})
            if resp.status_code == 200:
                return resp.json().get("body", "Sem release notes disponíveis.")
        except requests.exceptions.RequestException:
            continue
    return "Release notes não encontradas."


def write_github_output(key: str, value: str) -> None:
    """Escreve variável de saída para o GitHub Actions."""
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if not github_output:
        # GITHUB_OUTPUT não definido — ambiente fora do GitHub Actions
        return
    with open(github_output, "a", encoding="utf-8") as fh:
        # Valores multi-linha precisam de delimitador
        if "\n" in value:
            delimiter = "EOF"
            fh.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
        else:
            fh.write(f"{key}={value}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Verifica atualizações do notebooklm-py")
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="Escreve outputs no formato GitHub Actions",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Saída em formato JSON",
    )
    args = parser.parse_args()

    # 1. Versão instalada (requirements.txt)
    current_version = get_current_version_from_requirements(REQUIREMENTS_FILE)
    if not current_version:
        print(
            f"[AVISO] {PACKAGE_NAME} não encontrado em {REQUIREMENTS_FILE}. "
            "Usando '0.0.0' como base.",
            file=sys.stderr,
        )
        current_version = "0.0.0"

    # 2. Versão mais recente (PyPI)
    latest_version, release_date, home_page = get_latest_version_from_pypi()

    # 3. Classificar tipo de update
    update_type = classify_update(current_version, latest_version)
    has_update = update_type != "none"

    # 4. Verificar breaking changes (apenas para major/minor)
    has_breaking = False
    release_notes = ""
    if has_update and update_type in ("major", "minor"):
        has_breaking = check_breaking_changes_in_changelog(latest_version)
        release_notes = get_github_release_notes(latest_version)

    # ── Resultado ──
    result = {
        "package": PACKAGE_NAME,
        "current_version": current_version,
        "latest_version": latest_version,
        "update_type": update_type,
        "has_update": has_update,
        "has_breaking_changes": has_breaking,
        "release_date": release_date,
        "release_notes": release_notes[:500] if release_notes else "",
        "pypi_url": f"https://pypi.org/project/{PACKAGE_NAME}/{latest_version}/",
        "home_page": home_page,
    }

    if args.output_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.github_output:
        write_github_output("current_version", current_version)
        write_github_output("latest_version", latest_version)
        write_github_output("update_type", update_type)
        write_github_output("has_update", str(has_update).lower())
        write_github_output("release_notes", result["release_notes"])
        return

    # ── Saída humana (console) ──
    print("=" * 60)
    print(f"📦 Verificação: {PACKAGE_NAME}")
    print("=" * 60)
    print(f"  Versão atual (requirements.txt): {current_version}")
    print(f"  Versão mais recente (PyPI):       {latest_version}")
    print(f"  Data de lançamento:               {release_date or 'N/A'}")
    print(f"  Tipo de atualização:              {update_type}")
    print()

    if not has_update:
        print("✅ Versão está atualizada. Nenhuma ação necessária.")
        return

    # Determina emoji por nível de risco
    risk_map = {
        "major": ("🔴", "CRÍTICO — Breaking changes prováveis"),
        "minor": ("🟡", "ATENÇÃO — Revisar changelog antes de atualizar"),
        "patch": ("🟢", "SEGURO — Atualização de baixo risco"),
    }
    emoji, message = risk_map.get(update_type, ("⚠️", "DESCONHECIDO"))

    print(f"{emoji} Nova versão disponível: {current_version} → {latest_version}")
    print(f"   Nível de risco: {message}")

    if has_breaking:
        print()
        print("⚠️  Breaking changes detectados no changelog!")
        print("   Consulte o ALERT-RUNBOOK.md antes de atualizar.")

    if release_notes:
        print()
        print("📋 Release Notes (resumo):")
        print(f"   {release_notes[:300]}...")

    print()
    print(f"   PyPI: {result['pypi_url']}")
    print(f"   Runbook: ALERT-RUNBOOK.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
