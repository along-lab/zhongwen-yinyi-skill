#!/usr/bin/env python3
"""Add or update a glossary term from an explicit user correction."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GLOSSARY = ROOT / "data" / "technical_terms.json"
DEFAULT_LOG = ROOT / "data" / "corrections.jsonl"


def load_glossary(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError(f"{path} must contain only JSON objects")
    return payload


def write_glossary(path: Path, entries: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_key(value: str) -> str:
    return value.strip().casefold()


def sort_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        entries,
        key=lambda item: (
            0 if item.get("kind") == "phrase" else 1 if item.get("kind") == "word" else 2,
            str(item.get("term", "")).casefold(),
        ),
    )


def update_entry(
    entries: list[dict[str, Any]],
    *,
    term: str,
    homophone: str,
    meaning: str | None,
    kind: str,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None, dict[str, Any]]:
    target_key = normalize_key(term)
    old_entry: dict[str, Any] | None = None
    next_entries: list[dict[str, Any]] = []
    next_entry: dict[str, Any] | None = None

    for entry in entries:
        if normalize_key(str(entry.get("term", ""))) != target_key:
            next_entries.append(entry)
            continue
        old_entry = dict(entry)
        next_entry = dict(entry)
        next_entry["term"] = term
        next_entry["kind"] = kind
        next_entry["homophone"] = homophone
        if meaning is not None:
            next_entry["meaning"] = meaning
        if not str(next_entry.get("meaning", "")).strip():
            raise ValueError("Existing entry has no meaning; pass --meaning.")
        next_entries.append(next_entry)

    if next_entry is None:
        if meaning is None:
            raise ValueError("New terms must include --meaning.")
        next_entry = {
            "term": term,
            "kind": kind,
            "homophone": homophone,
            "meaning": meaning,
        }
        next_entries.append(next_entry)

    return sort_entries(next_entries), old_entry, next_entry


def append_correction_log(
    path: Path,
    *,
    term: str,
    old_entry: dict[str, Any] | None,
    new_entry: dict[str, Any],
    source: str,
    note: str,
) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "term": term,
        "old_homophone": "" if old_entry is None else str(old_entry.get("homophone", "")),
        "new_homophone": str(new_entry.get("homophone", "")),
        "meaning": str(new_entry.get("meaning", "")),
        "source": source,
        "note": note,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update a homophone glossary entry.")
    parser.add_argument("--term", required=True, help="English term to add or update")
    parser.add_argument("--homophone", required=True, help="Corrected Chinese homophone")
    parser.add_argument("--meaning", help="Chinese meaning; required for new terms")
    parser.add_argument(
        "--kind",
        default="word",
        choices=["word", "phrase"],
        help="Term kind. Acronyms do not use homophone corrections.",
    )
    parser.add_argument("--note", default="", help="Correction note")
    parser.add_argument("--source", default="user_correction", help="Correction source label")
    parser.add_argument("--glossary", default=str(DEFAULT_GLOSSARY), help="Glossary JSON path")
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="Correction JSONL path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    glossary_path = Path(args.glossary).expanduser().resolve()
    log_path = Path(args.log).expanduser().resolve()

    entries = load_glossary(glossary_path)
    next_entries, old_entry, new_entry = update_entry(
        entries,
        term=args.term.strip(),
        homophone=args.homophone.strip(),
        meaning=args.meaning.strip() if args.meaning else None,
        kind=args.kind,
    )
    write_glossary(glossary_path, next_entries)
    append_correction_log(
        log_path,
        term=args.term.strip(),
        old_entry=old_entry,
        new_entry=new_entry,
        source=args.source,
        note=args.note,
    )

    action = "Updated" if old_entry is not None else "Added"
    print(
        f"{action} {new_entry['term']}: "
        f"{old_entry.get('homophone', '') if old_entry else ''} -> {new_entry['homophone']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
