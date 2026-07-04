from pathlib import Path
import importlib.util
import sys


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


def test_annotates_first_occurrence_only():
    terms = translator.load_terms()
    text = "Skill can call a Plugin. Skill should stay readable."

    output = translator.annotate_text(text, terms)

    assert "Skill（谐音:斯ki尔/技能） can call a Plugin（谐音:普拉格因/插件）" in output
    assert output.endswith("Skill should stay readable.")


def test_acronym_uses_meaning_only():
    terms = translator.load_terms()

    output = translator.annotate_text("This MVP can call an API.", terms)

    assert "MVP（最小可用版本）" in output
    assert "API（接口）" in output
    assert "谐音:嗯-V-P" not in output


def test_skips_code_spans():
    terms = translator.load_terms()

    output = translator.annotate_text("Run `Plugin Skill API` before using Plugin.", terms)

    assert "`Plugin Skill API`" in output
    assert "Plugin（谐音:普拉格因/插件）" in output


def test_skips_already_annotated_terms():
    terms = translator.load_terms()

    output = translator.annotate_text("Skill（谐音:斯ki尔/技能） calls Skill.", terms)

    assert output == "Skill（谐音:斯ki尔/技能） calls Skill."


def test_cloudflare_tunnel_terms_are_curated():
    terms = translator.load_terms()

    output = translator.annotate_text("Cloudflare Tunnel is not WebUI.", terms)

    assert "Cloudflare（谐音:克劳德弗莱尔/云代理服务）" in output
    assert "Tunnel（谐音:塔呢尔/隧道）" in output
    assert "WebUI（谐音:韦布-尤艾/网页界面）" in output
    assert "널" not in output
