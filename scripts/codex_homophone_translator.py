#!/usr/bin/env python3
"""Annotate English technical terms with Chinese homophone notes.

This MVP intentionally prefers a curated glossary over broad automatic
transliteration. Unknown words are skipped by default so normal prose stays
readable and low-confidence pronunciations do not leak into user replies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GLOSSARY = ROOT / "data" / "technical_terms.json"
MASK_RE = re.compile(r"(```[\s\S]*?```|`[^`\n]*`)")
FORBIDDEN_HOMOPHONE_SCRIPT_RE = re.compile(
    r"[\u1100-\u11ff\u3040-\u30ff\u3130-\u318f\u31f0-\u31ff\uac00-\ud7af]"
)


def validate_homophone(value: str, *, path: Path, index: int) -> None:
    match = FORBIDDEN_HOMOPHONE_SCRIPT_RE.search(value)
    if match:
        char = match.group(0)
        raise ValueError(
            f"{path} item {index} homophone contains forbidden phonetic script: {char!r}"
        )


@dataclass(frozen=True)
class Term:
    term: str
    kind: str
    meaning: str
    homophone: str = ""

    @property
    def key(self) -> str:
        return self.term.casefold()

    @property
    def is_acronym(self) -> bool:
        return self.kind == "acronym"

    def annotation_for(self, display: str) -> str:
        if self.is_acronym:
            return f"{display}（{self.meaning}）"
        return f"{display}（谐音:{self.homophone}/{self.meaning}）"


def load_terms(path: Path = DEFAULT_GLOSSARY) -> list[Term]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array")

    terms: list[Term] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path} item {index} must be an object")
        term = str(item.get("term", "")).strip()
        kind = str(item.get("kind", "word")).strip()
        meaning = str(item.get("meaning", "")).strip()
        homophone = str(item.get("homophone", "")).strip()
        if not term or not meaning:
            raise ValueError(f"{path} item {index} must include term and meaning")
        if kind not in {"word", "phrase", "acronym"}:
            raise ValueError(f"{path} item {index} has unsupported kind: {kind}")
        if kind != "acronym" and not homophone:
            raise ValueError(f"{path} item {index} must include homophone")
        if kind != "acronym":
            validate_homophone(homophone, path=path, index=index)
        terms.append(Term(term=term, kind=kind, meaning=meaning, homophone=homophone))

    return sorted(terms, key=lambda item: (-len(item.term), item.term.casefold()))


def build_pattern(term: str) -> re.Pattern[str]:
    pieces = [re.escape(piece) for piece in re.split(r"\s+", term.strip()) if piece]
    body = r"[\s-]+".join(pieces)
    return re.compile(rf"(?<![A-Za-z0-9_])({body})(?![A-Za-z0-9_])", re.IGNORECASE)


def should_skip_match(text: str, start: int, end: int) -> bool:
    tail = text[end : end + 12]
    if tail.startswith(("（", "(")):
        return True
    head = text[max(0, start - 8) : start]
    if head.endswith(("http://", "https://")):
        return True
    return False


def is_already_annotated(text: str, start: int, end: int) -> bool:
    tail = text[end : end + 12]
    return tail.startswith(("（", "("))


def annotate_plain_text(
    text: str,
    terms: Iterable[Term],
    *,
    annotate_all: bool = False,
    seen: set[str] | None = None,
) -> str:
    used = seen if seen is not None else set()
    result = text

    for term in terms:
        pattern = build_pattern(term.term)

        def replace(match: re.Match[str]) -> str:
            key = term.key
            if is_already_annotated(result, match.start(), match.end()):
                used.add(key)
                return match.group(0)
            if not annotate_all and key in used:
                return match.group(0)
            if should_skip_match(result, match.start(), match.end()):
                return match.group(0)
            used.add(key)
            return term.annotation_for(match.group(1))

        result = pattern.sub(replace, result)

    return result


def annotate_text(text: str, terms: Iterable[Term], *, annotate_all: bool = False) -> str:
    parts = MASK_RE.split(text)
    seen: set[str] = set()
    output: list[str] = []
    for part in parts:
        if not part:
            continue
        if MASK_RE.fullmatch(part):
            output.append(part)
            continue
        output.append(annotate_plain_text(part, terms, annotate_all=annotate_all, seen=seen))
    return "".join(output)


def read_input(args: argparse.Namespace) -> str:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if args.text:
        return " ".join(args.text)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("Please pass text, --file, or pipe text through stdin.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add Chinese homophone annotations to English technical terms."
    )
    parser.add_argument("text", nargs="*", help="Text to annotate")
    parser.add_argument("--file", help="Read text from a UTF-8 file")
    parser.add_argument(
        "--glossary",
        default=str(DEFAULT_GLOSSARY),
        help="Path to a glossary JSON file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Annotate every occurrence instead of only the first occurrence",
    )
    parser.add_argument(
        "--list-terms",
        action="store_true",
        help="Print loaded glossary terms as JSON and exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    terms = load_terms(Path(args.glossary).expanduser().resolve())
    if args.list_terms:
        print(
            json.dumps(
                [
                    {
                        "term": term.term,
                        "kind": term.kind,
                        "homophone": term.homophone,
                        "meaning": term.meaning,
                    }
                    for term in terms
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    text = read_input(args)
    print(annotate_text(text, terms, annotate_all=args.all), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
