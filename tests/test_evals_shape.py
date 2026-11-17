import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SKILLS = sorted((ROOT / "skills").iterdir())
ALLOWED = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
KNOWN = {"doctor", "workspace", "brandcheck", "packet", "verify", "beats", "hookscore", "detect", "watch", "check", "cover"}


def frontmatter(path: Path) -> dict:
    head = path.read_text().split("---")[1]
    return dict(re.findall(r"^([a-z-]+):\s*(.*)$", head, re.M))


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_skill_shape(skill):
    md = skill / "SKILL.md"
    fm = frontmatter(md)
    assert set(fm) <= ALLOWED and fm["name"] == skill.name and fm["description"]
    assert len(md.read_text().splitlines()) < 500


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_skill_starts_with_doctor(skill):
    first = next(m for m in re.findall(r"\bcs ([a-z]+)\b", (skill / "SKILL.md").read_text()) if m in KNOWN)
    assert first == "doctor"


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_skill_grants_no_write_or_edit(skill):
    assert not re.search(r"\b(Write|Edit)\b", frontmatter(skill / "SKILL.md")["allowed-tools"])


def test_six_skills():
    assert [s.name for s in SKILLS] == ["cover", "doctor", "make-video", "research", "script", "setup-brand"]


@pytest.mark.parametrize("name", ["setup-brand", "script"])
def test_trigger_shape(name):
    t = json.loads((ROOT / "evals" / name / "triggers.json").read_text())
    assert len(t) >= 20 and sum(not x["should_trigger"] for x in t) >= 8
    assert all(set(x) == {"query", "should_trigger"} for x in t)


def _rubric(p: Path) -> str:
    return re.search(r"<!-- rubric:start -->(.*?)<!-- rubric:end -->", p.read_text(), re.S).group(1).strip()


def test_rubric_text_matches_critic_agent():
    assert _rubric(ROOT / "skills/script/references/critic-rubric.md") == _rubric(ROOT / "agents/critic.md")


def test_rubric_names_every_criterion():
    from content_studio.verify import CRITERIA
    text = _rubric(ROOT / "agents/critic.md")
    assert all(f"- {c}:" in text for c in CRITERIA)


def test_agents_are_read_only():
    for a in (ROOT / "agents").glob("*.md"):
        assert frontmatter(a)["tools"] == "Read"


def test_critic_discrimination_options_build_a_packet():
    from content_studio.packet import build_packet
    opts = json.loads((ROOT / "evals/script/critic-discrimination/options.json").read_text())
    packet, labels = build_packet(opts, "evidence", 1)
    assert len(labels) == 3 and "recommend" not in packet.lower()
