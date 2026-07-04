# 中文音译技能

中文音译技能 is a local Codex skill and glossary tool for Chinese users who read AI, coding, and agent workflow replies that contain English technical terms.

It annotates English terms with Chinese homophone pronunciation hints and Chinese meanings:

```text
Skill（谐音:斯ki尔/技能） can call a Plugin（谐音:普拉格因/插件） through an API（接口）.
```

## Why

Many Chinese users can use AI coding agents well, but English technical terms can still be a reading barrier. This project aims to make those terms easier to read aloud and understand without turning every reply into a full English lesson.

## One-Command Install For Codex

Clone this repository and run:

```bash
python3 scripts/install_for_codex.py
```

The installer will:

- copy this plugin to `~/plugins/zhongwen-yinyi-skill`;
- create or update `~/.agents/plugins/marketplace.json`;
- run `codex plugin add zhongwen-yinyi-skill@personal` when the Codex CLI is available;
- append a global `~/.codex/AGENTS.md` rule so new Codex threads use 中文音译技能 by default.

Then open a new Codex thread.

If you only want to install the plugin and do not want to write the global Agent rule:

```bash
python3 scripts/install_for_codex.py --skip-global-rule
```

## Try It

```bash
python3 scripts/codex_homophone_translator.py "Skill can call a Plugin through an API."
```

Expected output:

```text
Skill（谐音:斯ki尔/技能） can call a Plugin（谐音:普拉格因/插件） through an API（接口）.
```

## Files

- `data/technical_terms.json`: curated technical glossary.
- `data/corrections.jsonl`: correction history for user-approved pronunciation changes.
- `scripts/codex_homophone_translator.py`: local annotation command.
- `scripts/install_for_codex.py`: one-command local installer for Codex.
- `scripts/update_term.py`: correction command for user-approved pronunciation changes.
- `skills/homophone-annotator/SKILL.md`: 中文音译技能 instructions.
- `tests/test_codex_homophone_translator.py`: MVP behavior tests.

## How It Works

The current architecture is intentionally simple:

```text
Codex global rule or user prompt
  -> homophone-annotator skill instructions
  -> curated glossary in data/technical_terms.json
  -> local annotation script for batch processing
  -> update_term.py for explicit user corrections
```

The skill should:

- annotate the first visible occurrence of an English technical word in a reply;
- skip inline code, fenced code blocks, raw logs, URLs, file paths, command literals, package names, and config keys;
- explain pure acronyms with Chinese meanings only, for example `API（接口）`;
- treat explicit user pronunciation corrections as accepted glossary data.

## Current Boundary

This version uses a curated glossary first. It does not automatically guess every unknown English word, because low-confidence guesses can make replies harder to read.

It is not a speech recognition system and does not yet verify pronunciations against audio.

## Correct A Pronunciation

```bash
python3 scripts/update_term.py --term "Skill" --homophone "斯ki尔" --meaning "技能" --note "User correction"
```

The command updates `data/technical_terms.json` and records the change in `data/corrections.jsonl`.

## Verify

```bash
python3 tests/run_tests.py
python3 -m py_compile scripts/codex_homophone_translator.py scripts/install_for_codex.py scripts/update_term.py tests/run_tests.py tests/test_codex_homophone_translator.py
```

## License

MIT
