---
name: homophone-annotator
description: 中文音译技能。Use when the user wants Codex replies to explain English technical terms with Chinese homophone pronunciation notes and Chinese meanings.
---

# 中文音译技能

Use this skill when a Chinese user wants English words in Codex replies to be annotated with Chinese pronunciation hints. The user-facing Chinese name is `中文音译技能`; keep the machine skill name `homophone-annotator` for Codex plugin compatibility.

## Activation Contract

Global startup rules should stay short and only say to enable `中文音译技能` by default, then follow this Skill. Keep detailed behavior here to reduce cold-start context.

Installed runtime cache path:

```text
/Users/a001/.codex/plugins/cache/personal/zhongwen-yinyi-skill/0.1.0
```

Source path for edits:

```text
/Users/a001/Codex智能体工作区/05_项目工作区/Codex 翻译插件。/codex-homophone-translator
```

When editing the source glossary or scripts, reinstall the plugin so the runtime cache updates:

```bash
python3 scripts/install_for_codex.py
```

## Output Rule

For the first visible occurrence of an English technical word in each assistant reply, use:

```text
English（谐音:中文近似读音/中文解释）
```

For pure acronyms, only add the Chinese meaning:

```text
API（接口）
```

Do not carry "first occurrence" state across the whole conversation. Reset the first-occurrence check for every assistant reply.

Skip code blocks, inline code, raw logs, URLs, file paths, command literals, package names, config keys, and single letters. If one of those terms is explained in prose as a concept, annotate it in prose.

If pronunciation confidence is low and the term is not in the glossary, prefer a Chinese meaning plus `读法待确认` over inventing a low-quality homophone.

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
- Homophone text must use Chinese characters, with only small ASCII letter helpers when the user explicitly prefers them, such as `斯ki尔`.
- Never use Korean Hangul, Japanese kana, Cyrillic, or other non-Chinese phonetic scripts in homophone text.
- Do not use crude or negative Chinese characters as default pronunciation hints.
- Skip low-confidence unknown words until they are added to the glossary.
- When the user explicitly corrects a pronunciation, treat the correction as accepted data and write it into the glossary.

## Examples

- `Spec（谐音:斯佩克/规格说明）`
- `Product-Spec（谐音:普罗达克特-斯佩克/产品规格文档）`
- `Design-Brief（谐音:迪扎因-布里夫/设计简报）`
- `Phase（谐音:费兹/阶段）`
- `Review（谐音:瑞维尤/审查）`
- `Agent（谐音:诶金特/智能体）`
- `Skill（谐音:斯ki尔/技能）`
