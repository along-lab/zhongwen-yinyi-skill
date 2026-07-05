#!/usr/bin/env python3
"""Install this local plugin into the user's personal Codex marketplace."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


PLUGIN_NAME = "zhongwen-yinyi-skill"
MARKETPLACE_NAME = "personal"
HOME = Path.home()
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TARGET_ROOT = HOME / "plugins" / PLUGIN_NAME
MARKETPLACE_PATH = HOME / ".agents" / "plugins" / "marketplace.json"
GLOBAL_AGENTS_PATH = HOME / ".codex" / "AGENTS.md"

GLOBAL_RULE_BLOCK = """\

## 全局中文音译技能

- 新开任何 Codex 线程时，默认启用 `zhongwen-yinyi-skill` / Skill `homophone-annotator`，用户可见名为“中文音译技能”。
- 每条回复的英文术语注释、谐音格式、跳过规则、纠错入库和词库路径，都遵守该 Skill 的 `SKILL.md`。
- 运行时缓存路径：`~/.codex/plugins/cache/personal/zhongwen-yinyi-skill/0.1.0`；源码路径：当前仓库。
"""


def copy_plugin_source() -> None:
    if TARGET_ROOT.exists():
        shutil.rmtree(TARGET_ROOT)
    ignore = shutil.ignore_patterns(
        ".git",
        "__pycache__",
        ".DS_Store",
        ".pytest_cache",
        "*.pyc",
    )
    shutil.copytree(PLUGIN_ROOT, TARGET_ROOT, ignore=ignore)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": MARKETPLACE_NAME,
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    payload.setdefault("name", MARKETPLACE_NAME)
    payload.setdefault("interface", {"displayName": "Personal"})
    payload.setdefault("plugins", [])
    return payload


def write_marketplace() -> None:
    payload = load_json(MARKETPLACE_PATH)
    plugins = payload.get("plugins")
    if not isinstance(plugins, list):
        raise ValueError(f"{MARKETPLACE_PATH} field 'plugins' must be an array")

    entry = {
        "name": PLUGIN_NAME,
        "source": {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }
    for index, existing in enumerate(plugins):
        if isinstance(existing, dict) and existing.get("name") == PLUGIN_NAME:
            plugins[index] = entry
            break
    else:
        plugins.append(entry)

    MARKETPLACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKETPLACE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def append_global_rule() -> bool:
    GLOBAL_AGENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    current = GLOBAL_AGENTS_PATH.read_text(encoding="utf-8") if GLOBAL_AGENTS_PATH.exists() else ""
    if "## 全局中文音译技能" in current or "zhongwen-yinyi-skill" in current:
        return False
    next_text = current.rstrip() + "\n" + GLOBAL_RULE_BLOCK
    GLOBAL_AGENTS_PATH.write_text(next_text, encoding="utf-8")
    return True


def install_with_codex_cli() -> None:
    codex = shutil.which("codex")
    if codex is None:
        print("Codex CLI not found. Marketplace files were prepared, but plugin add was skipped.")
        return
    subprocess.run(
        [codex, "plugin", "add", f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install 中文音译技能 into Codex.")
    parser.add_argument(
        "--skip-global-rule",
        action="store_true",
        help="Install the plugin without writing the global AGENTS.md rule.",
    )
    parser.add_argument(
        "--skip-codex-add",
        action="store_true",
        help="Prepare marketplace files without running `codex plugin add`.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    copy_plugin_source()
    write_marketplace()
    wrote_rule = False if args.skip_global_rule else append_global_rule()
    if not args.skip_codex_add:
        install_with_codex_cli()

    print(f"Installed plugin source: {TARGET_ROOT}")
    print(f"Updated marketplace: {MARKETPLACE_PATH}")
    if args.skip_global_rule:
        print("Skipped global AGENTS.md rule.")
    elif wrote_rule:
        print(f"Appended global rule: {GLOBAL_AGENTS_PATH}")
    else:
        print(f"Global rule already exists: {GLOBAL_AGENTS_PATH}")
    print("Open a new Codex thread to use 中文音译技能.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
