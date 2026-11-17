import json
import re
import tomllib
from pathlib import Path

from content_studio.cli import main

ROOT = Path(__file__).parent.parent
PLUGIN = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
MARKET = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())


def test_versions_match():
    assert PLUGIN["version"] == tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert f'VERSION = "{PLUGIN["version"]}"' in (ROOT / "src" / "content_studio" / "cli.py").read_text()


def test_plugin_has_no_dependencies():
    assert "dependencies" not in PLUGIN


def test_marketplace_lists_plugin():
    assert [(p["name"], p["source"]) for p in MARKET["plugins"]] == [(PLUGIN["name"], "./")]


def test_licence_lines():
    assert PLUGIN["license"] == "MIT" and (ROOT / "LICENSE").read_text().startswith("MIT License")
    third = (ROOT / "THIRD_PARTY.md").read_text()
    for needle in ("MIT License", "Apache-2.0", "PolyForm Noncommercial", "NOASSERTION"):
        assert needle in third


def test_readme_has_the_install_facts():
    readme = (ROOT / "README.md").read_text()
    assert "riekert7/content-studio" in readme and "auto-update" in readme.lower()
    assert "Install the Claude Code plugin" in readme and "cs doctor --allow" in readme


def test_every_cs_command_in_skills_is_in_agents_md():
    agents = (ROOT / "AGENTS.md").read_text()
    used = set()
    for f in (ROOT / "skills").rglob("*.md"):
        used |= set(re.findall(r"\bcs ([a-z]+)\b", f.read_text()))
    known = {"doctor", "workspace", "brandcheck", "packet", "verify", "beats", "hookscore", "detect", "watch", "check", "cover"}
    used &= known | {"below"}  # "cs below" is prose in the preamble
    used.discard("below")
    assert used and all(f"`cs {c}" in agents for c in used)


def test_every_documented_command_runs_help(capsys):
    for c in ("doctor", "workspace", "brandcheck", "packet", "verify", "beats", "watch", "check", "cover"):
        try:
            main([c, "--help"])
        except SystemExit as e:
            assert e.code == 0
        assert capsys.readouterr().out
