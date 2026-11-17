import shutil
from pathlib import Path

from content_studio.brand import REQUIRED, check_brand, check_workspace
from content_studio.cli import main

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "templates" / "brand"
EXAMPLE = ROOT / "examples" / "lumen-coffee"


def test_template_folder_passes_brandcheck_headings(tmp_path):
    shutil.copytree(TEMPLATE, tmp_path / "x")
    assert check_brand(tmp_path / "x") == []


def test_example_brand_passes():
    assert check_brand(EXAMPLE) == []


def test_missing_file_reported(tmp_path):
    shutil.copytree(TEMPLATE, tmp_path / "x")
    (tmp_path / "x" / "formats.md").unlink()
    assert "formats.md: missing file" in check_brand(tmp_path / "x")


def test_missing_heading_reported(tmp_path):
    shutil.copytree(TEMPLATE, tmp_path / "x")
    p = tmp_path / "x" / "viewers.md"
    p.write_text(p.read_text().replace("# Viewer 2", "# Someone"))
    assert "viewers.md: missing heading # Viewer 2" in check_brand(tmp_path / "x")


def test_empty_section_reported(tmp_path):
    shutil.copytree(EXAMPLE, tmp_path / "x")
    p = tmp_path / "x" / "voice.md"
    p.write_text("# How they sound\n\n# Phrases they use\ntext\n\n# Never write\ntext\n")
    assert "voice.md: nothing under # How they sound" in check_brand(tmp_path / "x")


def test_template_prompts_are_not_content(tmp_path):
    # a template is valid on headings but the italic prompts alone must not count as an answer in `fill` mode
    shutil.copytree(TEMPLATE, tmp_path / "x")
    assert check_brand(tmp_path / "x", filled=True) != []
    assert check_brand(EXAMPLE, filled=True) == []


def test_required_is_exactly_the_five_files():
    assert set(REQUIRED) == {"brand.md", "voice.md", "style.md", "formats.md", "viewers.md"}


def test_home_folder_rejected():
    assert check_workspace(Path("/home/u"), Path("/home/u"))
    assert check_workspace(Path("/home"), Path("/home/u"))
    assert check_workspace(Path("/"), Path("/home/u"))
    assert check_workspace(Path("/home/u/shop"), Path("/home/u")) is None


def test_workspace_cli_exit_1_for_home(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert main(["workspace", str(tmp_path)]) == 1
    assert "project folder" in capsys.readouterr().err
    (tmp_path / "shop").mkdir()
    assert main(["workspace", str(tmp_path / "shop")]) == 0


def test_brandcheck_cli(tmp_path, capsys):
    assert main(["brandcheck", str(EXAMPLE), "--filled"]) == 0
    shutil.copytree(TEMPLATE, tmp_path / "x")
    (tmp_path / "x" / "style.md").unlink()
    assert main(["brandcheck", str(tmp_path / "x")]) == 1
    assert "style.md: missing file" in capsys.readouterr().out
