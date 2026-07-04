# Contributing

Thank you for helping improve 中文音译技能.

## What To Contribute

- Better Chinese homophone readings for English technical terms.
- New AI, coding, and agent workflow terms.
- Fixes for terms that are confusing, rude, or hard to read aloud.
- Tests for glossary updates and text annotation behavior.

## Glossary Rules

Glossary entries live in `data/technical_terms.json`.

Use this shape:

```json
{
  "term": "Skill",
  "kind": "word",
  "homophone": "斯ki尔",
  "meaning": "技能"
}
```

For pure acronyms, omit `homophone`:

```json
{
  "term": "API",
  "kind": "acronym",
  "meaning": "接口"
}
```

## Correct A Term

Use the helper script:

```bash
python3 scripts/update_term.py --term "Skill" --homophone "斯ki尔" --meaning "技能" --note "User correction"
```

This updates `data/technical_terms.json` and appends a correction record to `data/corrections.jsonl`.

## Verify

```bash
python3 tests/run_tests.py
python3 -m py_compile scripts/codex_homophone_translator.py scripts/install_for_codex.py scripts/update_term.py tests/run_tests.py tests/test_codex_homophone_translator.py
```
