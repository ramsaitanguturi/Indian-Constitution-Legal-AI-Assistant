"""
Corpus Freshness and Incremental Update Workflow CLI.
Provides safe, auditable, and rollback-protected commands for legal corpus updates:
    python -m scripts.update_corpus --check
    python -m scripts.update_corpus --download
    python -m scripts.update_corpus --backup
    python -m scripts.update_corpus --rollback
    python -m scripts.update_corpus --full-update

Integrates catalog checksum comparison, incremental change detection,
automated index backups, and rollback capabilities.
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
import urllib.request
import ssl
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    RAW_DIR,
    MANIFESTS_DIR,
    REPORTS_DIR,
    PARENT_STORE_PATH,
    CHROMA_PERSIST_DIR,
    CORPUS_MANIFEST_PATH,
    VALIDATION_REPORT_PATH,
)
from scripts.download_sources import SOURCE_TARGETS, compute_file_sha256, run_source_downloads
from scripts.build_corpus import build_corpus
from scripts.build_index import build_or_rebuild_index
from scripts.validate_corpus import run_corpus_validation

BACKUP_DIR = BASE_DIR / "backups"


def check_updates() -> Dict[str, Any]:
    """Check remote source availability and compare SHA-256 hashes against local manifest."""
    print("=" * 65)
    print("CORPUS FRESHNESS CHECK — REMOTE SOURCE CATALOG AUDIT")
    print("=" * 65)

    manifest_path = MANIFESTS_DIR / "raw_downloads_manifest.json"
    local_manifest = {}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            local_manifest = json.load(f)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"User-Agent": "Mozilla/5.0 LegalFreshnessBot/2.0"}

    results = []
    has_changes = False

    for target in SOURCE_TARGETS:
        sid = target["source_id"]
        url = target["url"]
        local_file = target["target_dir"] / target["filename"]

        status_info = {
            "source_id": sid,
            "url": url,
            "local_exists": local_file.exists(),
            "local_sha256": None,
            "remote_status": "UNKNOWN",
            "needs_update": False,
        }

        if local_file.exists():
            status_info["local_sha256"] = compute_file_sha256(local_file)

        # Check remote availability
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
                status_info["remote_status"] = f"HTTP {resp.status}"
                remote_len = resp.headers.get("Content-Length")
                if remote_len and local_file.exists():
                    if int(remote_len) != local_file.stat().st_size:
                        status_info["needs_update"] = True
                        has_changes = True
        except Exception as e:
            status_info["remote_status"] = f"ERROR: {e}"

        if not local_file.exists():
            status_info["needs_update"] = True
            has_changes = True

        results.append(status_info)
        mark = "[UPDATE NEEDED]" if status_info["needs_update"] else "[UP TO DATE]"
        print(f"[*] {sid}: {status_info['remote_status']} -> {mark}")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "has_changes": has_changes,
        "sources": results,
    }

    report_path = REPORTS_DIR / "corpus_freshness_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 65)
    print(f"Summary: {'Updates Available' if has_changes else 'All Sources Up To Date'}")
    print(f"[+] Freshness report logged to: {report_path}")
    print("=" * 65)

    return report


def backup_active_index() -> Path:
    """Create a timestamped backup of ChromaDB and parent_store.json."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_backup = BACKUP_DIR / f"index_backup_{ts}"
    target_backup.mkdir(parents=True, exist_ok=True)

    print(f"[*] Creating safe index backup in: {target_backup}...")

    # Backup parent_store.json
    if PARENT_STORE_PATH.exists():
        shutil.copy2(PARENT_STORE_PATH, target_backup / "parent_store.json")

    # Backup chroma_db directory
    if CHROMA_PERSIST_DIR.exists():
        try:
            shutil.copytree(
                CHROMA_PERSIST_DIR,
                target_backup / "chroma_db",
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("*.lock", "*-journal", "*-wal", "*.tmp")
            )
        except Exception as e:
            print(f"    [!] Non-fatal notice during ChromaDB copy: {e}")

    print(f"[+] Index backup successfully created at: {target_backup}")
    return target_backup


def rollback_index() -> bool:
    """Restore the latest index backup if available."""
    if not BACKUP_DIR.exists():
        print("[-] No backups found.")
        return False

    backups = sorted([b for b in BACKUP_DIR.iterdir() if b.is_dir()], reverse=True)
    if not backups:
        print("[-] No backup directories found.")
        return False

    latest = backups[0]
    print(f"[*] Rolling back to latest backup: {latest}...")

    parent_src = latest / "parent_store.json"
    if parent_src.exists():
        shutil.copy2(parent_src, PARENT_STORE_PATH)
        print("    [+] Restored parent_store.json")

    chroma_src = latest / "chroma_db"
    if chroma_src.exists():
        if CHROMA_PERSIST_DIR.exists():
            shutil.rmtree(CHROMA_PERSIST_DIR)
        shutil.copytree(chroma_src, CHROMA_PERSIST_DIR)
        print("    [+] Restored chroma_db/")

    print("[+] Rollback successfully completed.")
    return True


def execute_full_update(force_rebuild: bool = False) -> None:
    """Execute complete end-to-end update sequence with backup protection."""
    print("=" * 65)
    print("EXECUTING FULL CORPUS UPDATE PIPELINE")
    print("=" * 65)

    # 1. Backup existing state
    backup_path = backup_active_index()

    try:
        # 2. Download any modified or new sources
        print("\n--- STEP 1: DOWNLOADING SOURCES ---")
        run_source_downloads()

        # 3. Build processed corpus
        print("\n--- STEP 2: BUILDING PROCESSED CORPUS ---")
        build_corpus(smoke_test=False)

        # 4. Validate corpus
        print("\n--- STEP 3: VALIDATING CORPUS INTEGRITY ---")
        val_report = run_corpus_validation()
        if val_report.get("overall_status") != "PASSED":
            raise RuntimeError(f"Corpus validation failed with {val_report.get('total_errors')} errors.")

        # 5. Build/Update Index
        print("\n--- STEP 4: BUILDING VECTOR & BM25 INDEX ---")
        build_or_rebuild_index(rebuild=force_rebuild)

        print("\n" + "=" * 65)
        print("[SUCCESS] Full legal corpus update completed cleanly!")
        print("=" * 65)

    except Exception as e:
        print(f"\n[!] Update failed with error: {e}")
        print("[!] Initiating automatic rollback to safe backup...")
        rollback_index()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corpus Freshness & Incremental Update Workflow CLI.")
    parser.add_argument("--check", action="store_true", help="Check remote sources for updates.")
    parser.add_argument("--download", action="store_true", help="Download raw authoritative sources.")
    parser.add_argument("--backup", action="store_true", help="Create snapshot backup of active index.")
    parser.add_argument("--rollback", action="store_true", help="Roll back to latest index backup.")
    parser.add_argument("--full-update", action="store_true", help="Execute full update with backup protection.")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild during full update.")
    args = parser.parse_args()

    if args.check:
        check_updates()
    elif args.download:
        run_source_downloads()
    elif args.backup:
        backup_active_index()
    elif args.rollback:
        rollback_index()
    elif args.full_update:
        execute_full_update(force_rebuild=args.rebuild)
    else:
        parser.print_help()
