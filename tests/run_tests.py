#!/usr/bin/env python3
"""Small dependency-free test runner for the MVP."""

from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "codex_homophone_translator.py"
)
SPEC = importlib.util.spec_from_file_location("translator", SCRIPT)
translator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = translator
SPEC.loader.exec_module(translator)


def assert_contains(haystack: str, needle: str) -> None:
    assert needle in haystack, f"Expected to find {needle!r} in {haystack!r}"


def test_annotates_first_occurrence_only() -> None:
    terms = translator.load_terms()
    text = "Skill can call a Plugin. Skill should stay readable."

    output = translator.annotate_text(text, terms)

    assert_contains(
        output,
        "Skill（谐音:斯ki尔/技能） can call a Plugin（谐音:普拉格因/插件）",
    )
    assert output.endswith("Skill should stay readable.")


def test_acronym_uses_meaning_only() -> None:
    terms = translator.load_terms()

    output = translator.annotate_text("This MVP can call an API.", terms)

    assert_contains(output, "MVP（最小可用版本）")
    assert_contains(output, "API（接口）")
    assert "谐音:嗯-V-P" not in output


def test_skips_code_spans() -> None:
    terms = translator.load_terms()

    output = translator.annotate_text("Run `Plugin Skill API` before using Plugin.", terms)

    assert_contains(output, "`Plugin Skill API`")
    assert_contains(output, "Plugin（谐音:普拉格因/插件）")


def test_skips_already_annotated_terms() -> None:
    terms = translator.load_terms()

    output = translator.annotate_text("Skill（谐音:斯ki尔/技能） calls Skill.", terms)

    assert output == "Skill（谐音:斯ki尔/技能） calls Skill."


def test_cloudflare_tunnel_terms_are_curated() -> None:
    terms = translator.load_terms()

    output = translator.annotate_text("Cloudflare Tunnel is not WebUI.", terms)

    assert_contains(output, "Cloudflare（谐音:克劳德弗莱尔/云代理服务）")
    assert_contains(output, "Tunnel（谐音:塔呢尔/隧道）")
    assert_contains(output, "WebUI（谐音:韦布-尤艾/网页界面）")
    assert "널" not in output


def test_load_terms_rejects_foreign_phonetic_scripts() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        glossary = Path(tmpdir) / "terms.json"
        glossary.write_text(
            json.dumps(
                [
                    {
                        "term": "Tunnel",
                        "kind": "word",
                        "homophone": "塔널",
                        "meaning": "隧道",
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        try:
            translator.load_terms(glossary)
        except ValueError as exc:
            assert "forbidden phonetic script" in str(exc)
        else:
            raise AssertionError("Expected foreign phonetic script to be rejected")


def test_update_term_writes_glossary_and_log() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        glossary = tmp / "terms.json"
        log = tmp / "corrections.jsonl"
        glossary.write_text(
            json.dumps(
                [
                    {
                        "term": "Skill",
                        "kind": "word",
                        "homophone": "斯克一勒",
                        "meaning": "技能",
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        update_script = SCRIPT.with_name("update_term.py")
        subprocess.run(
            [
                sys.executable,
                str(update_script),
                "--term",
                "Skill",
                "--homophone",
                "斯ki尔",
                "--meaning",
                "技能",
                "--glossary",
                str(glossary),
                "--log",
                str(log),
            ],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )

        entries = json.loads(glossary.read_text(encoding="utf-8"))
        assert entries[0]["homophone"] == "斯ki尔"
        record = json.loads(log.read_text(encoding="utf-8").strip())
        assert record["old_homophone"] == "斯克一勒"
        assert record["new_homophone"] == "斯ki尔"


def test_update_term_rejects_foreign_phonetic_scripts() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        glossary = tmp / "terms.json"
        log = tmp / "corrections.jsonl"
        glossary.write_text(
            json.dumps(
                [
                    {
                        "term": "Tunnel",
                        "kind": "word",
                        "homophone": "塔呢尔",
                        "meaning": "隧道",
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        update_script = SCRIPT.with_name("update_term.py")
        result = subprocess.run(
            [
                sys.executable,
                str(update_script),
                "--term",
                "Tunnel",
                "--homophone",
                "塔널",
                "--meaning",
                "隧道",
                "--glossary",
                str(glossary),
                "--log",
                str(log),
            ],
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode != 0
        assert "forbidden phonetic script" in result.stderr
        assert json.loads(glossary.read_text(encoding="utf-8"))[0]["homophone"] == "塔呢尔"
        assert not log.exists()


def main() -> int:
    tests = [
        test_annotates_first_occurrence_only,
        test_acronym_uses_meaning_only,
        test_skips_code_spans,
        test_skips_already_annotated_terms,
        test_cloudflare_tunnel_terms_are_curated,
        test_load_terms_rejects_foreign_phonetic_scripts,
        test_update_term_writes_glossary_and_log,
        test_update_term_rejects_foreign_phonetic_scripts,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
