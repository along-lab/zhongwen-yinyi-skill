---
name: homophone-annotator
description: 中文音译技能。Use when the user wants Codex replies to explain English technical terms with Chinese homophone pronunciation notes and Chinese meanings.
---

# 中文音译技能

Use this skill when a Chinese user wants English words in Codex replies to be annotated with Chinese pronunciation hints. The user-facing Chinese name is `中文音译技能`; keep the machine skill name `homophone-annotator` for Codex plugin compatibility.

## Output Rule

For the first visible occurrence of an English technical word in each assistant reply, use:

```text
English（谐音:中文近似读音/中文解释）
```

For pure acronyms, only add the Chinese meaning:

```text
API（接口）
```

## MVP Tool

This plugin includes a local script:

```bash
python3 scripts/codex_homophone_translator.py "Skill can call a Plugin through an API."
```

The script:

- uses `data/technical_terms.json` as the curated glossary;
- annotates only the first occurrence by default;
- skips inline code and fenced code blocks;
- avoids re-annotating terms that already have parentheses immediately after them.

## User Correction Flow

When the user explicitly corrects a pronunciation, update the glossary in the active plugin source before continuing. Examples of explicit correction:

- "Skill 应该读成 斯ki尔"
- "这个词不要读 A，改成 B"
- "X 的谐音更像 Y"

Use:

```bash
python3 scripts/update_term.py --term "Skill" --homophone "斯ki尔" --meaning "技能" --note "User correction"
```

This command updates `data/technical_terms.json` and appends a record to `data/corrections.jsonl`.

If the current thread is using an installed cached plugin, also tell the user that the source can be corrected immediately, but Codex needs the plugin to be reinstalled and a new thread opened before the cached plugin version loads the new glossary.

## Style Rules

- Prefer the curated glossary over guessing.
- Keep the pronunciation readable for non-English users.
- Do not use crude or negative Chinese characters as default pronunciation hints.
- Skip low-confidence unknown words until they are added to the glossary.
- When the user explicitly corrects a pronunciation, treat the correction as accepted data and write it into the glossary.
