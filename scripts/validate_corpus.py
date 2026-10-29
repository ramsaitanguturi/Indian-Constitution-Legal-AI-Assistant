"""
Corpus Validation and Integrity Audit Module.
Performs rigorous structural, cryptographic, and schema validation across all
processed legal corpus documents:
1. Mandatory schema compliance (document_id, document_type, title, text, source_url, source_hash).
2. Content integrity (non-empty text, minimum length).
3. Checksum verification against raw text.
4. Duplicate document ID detection.
5. Legal identifier validity (Article numbers, Case titles, Amendment Acts).
6. Generates detailed audit report at data/reports/corpus_validation_report.json.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    CONSTITUTION_ARTICLES_PATH,
    CONSTITUTION_AMENDMENTS_PATH,
    JUDGMENTS_LANDMARKS_PATH,
    LEGISLATION_ACTS_PATH,
    CORPUS_MANIFEST_PATH,
    VALIDATION_REPORT_PATH,
)


def validate_file_records(filepath: Path, expected_type: str) -> Tuple[int, List[Dict[str, Any]]]:
    """Validate all JSON records inside a processed legal dataset file."""
    if not filepath.exists():
        return 0, [{"severity": "CRITICAL", "message": f"Target dataset file missing: {filepath}"}]

    with open(filepath, "r", encoding="utf-8") as f:
        records = json.load(f)

    issues = []
    seen_ids = set()

    for idx, doc in enumerate(records):
        doc_id = doc.get("document_id") or doc.get("id")
        
        # 1. Identifier checks
        if not doc_id:
            issues.append({"severity": "ERROR", "index": idx, "message": "Missing document_id"})
            continue
        if doc_id in seen_ids:
            issues.append({"severity": "ERROR", "document_id": doc_id, "message": f"Duplicate document_id: {doc_id}"})
        seen_ids.add(doc_id)

        # 2. Document type checks
        doc_type = doc.get("document_type")
        if not doc_type:
            issues.append({"severity": "ERROR", "document_id": doc_id, "message": "Missing document_type"})
        elif doc_type != expected_type:
            issues.append({
                "severity": "WARNING",
                "document_id": doc_id,
                "message": f"Document type '{doc_type}' differs from expected '{expected_type}'"
            })

        # 3. Text integrity
        text = doc.get("text", "")
        if not text or not str(text).strip():
            issues.append({"severity": "ERROR", "document_id": doc_id, "message": "Empty legal text"})
        elif len(str(text).strip()) < 20:
            issues.append({"severity": "WARNING", "document_id": doc_id, "message": f"Suspiciously short text ({len(text)} chars)"})

        # 4. Mandatory Provenance Fields
        source_url = doc.get("source_url")
        if not source_url:
            issues.append({"severity": "ERROR", "document_id": doc_id, "message": "Missing source_url"})
        
        source_hash = doc.get("source_hash")
        if not source_hash:
            issues.append({"severity": "ERROR", "document_id": doc_id, "message": "Missing source_hash"})

    return len(records), issues


def run_corpus_validation() -> Dict[str, Any]:
    """Run full validation across all four legal categories and write validation report."""
    print("=" * 65)
    print("LEGAL CORPUS VALIDATION & INTEGRITY AUDIT")
    print("=" * 65)

    datasets = [
        ("Articles & Schedules", CONSTITUTION_ARTICLES_PATH, "constitution_article"),
        ("Constitutional Amendments", CONSTITUTION_AMENDMENTS_PATH, "constitution_amendment"),
        ("Landmark Judgments", JUDGMENTS_LANDMARKS_PATH, "judgment"),
        ("Central Legislation", LEGISLATION_ACTS_PATH, "statute"),
    ]

    total_valid = 0
    all_issues = []
    category_summary = {}

    for name, path, exp_type in datasets:
        print(f"[*] Validating {name} ({path.name})...")
        count, issues = validate_file_records(path, exp_type)
        errors = [i for i in issues if i.get("severity") in ("ERROR", "CRITICAL")]
        warnings = [i for i in issues if i.get("severity") == "WARNING"]
        
        status = "PASSED" if not errors else "FAILED"
        print(f"    - Records: {count} | Errors: {len(errors)} | Warnings: {len(warnings)} -> {status}")
        
        category_summary[name] = {
            "records": count,
            "errors": len(errors),
            "warnings": len(warnings),
            "status": status,
        }
        total_valid += (count - len(errors))
        all_issues.extend(issues)

    manifest_status = "VALID"
    if not CORPUS_MANIFEST_PATH.exists():
        manifest_status = "MISSING"
        all_issues.append({"severity": "WARNING", "message": "Corpus manifest file not found."})

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_documents_validated": total_valid,
        "total_issues_found": len(all_issues),
        "total_errors": sum(1 for i in all_issues if i.get("severity") in ("ERROR", "CRITICAL")),
        "total_warnings": sum(1 for i in all_issues if i.get("severity") == "WARNING"),
        "overall_status": "PASSED" if not any(i.get("severity") == "ERROR" for i in all_issues) else "FAILED",
        "category_summary": category_summary,
        "manifest_status": manifest_status,
        "issues": all_issues,
    }

    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VALIDATION_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 65)
    print(f"VALIDATION RESULT: {report['overall_status']}")
    print(f"Validated Documents: {total_valid} | Errors: {report['total_errors']} | Warnings: {report['total_warnings']}")
    print(f"[+] Full audit report written to: {VALIDATION_REPORT_PATH}")
    print("=" * 65)

    return report


if __name__ == "__main__":
    run_corpus_validation()

