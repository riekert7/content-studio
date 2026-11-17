"""Leak scan tests. Only dummy deny-list terms are used, written to a temp file via CS_DENYLIST."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCAN = ROOT / "scripts" / "leakscan.sh"
HOOKS = ROOT / "scripts" / "hooks"
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    (tmp_path / "deny.txt").write_text("# dummy list\n\nacmecorp\n")
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    return r


def env_for(repo, **extra):
    env = {**os.environ, "HOME": str(repo.parent), "CS_DENYLIST": str(repo.parent / "deny.txt")}
    env.update(extra)
    return env


def scan(repo, *args, env=None):
    return subprocess.run(
        [str(SCAN), *args], cwd=repo, env=env or env_for(repo), capture_output=True, text=True
    )


def commit_all(repo, msg="c"):
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run([*GIT, "commit", "-qm", msg], cwd=repo, check=True)


def test_clean_repo_passes(repo):
    (repo / "a.md").write_text("hello world\n")
    assert scan(repo).returncode == 0


def test_term_in_text_file_fails(repo):
    (repo / "a.md").write_text("fine\nmade for acmecorp today\n")
    r = scan(repo)
    assert r.returncode == 1
    assert "a.md:2" in r.stdout and "acmecorp" in r.stdout


def test_term_case_insensitive(repo):
    (repo / "a.md").write_text("AcmeCorp\n")
    assert scan(repo).returncode == 1


def test_term_in_file_name_fails(repo):
    (repo / "acmecorp-notes.md").write_text("harmless\n")
    assert scan(repo).returncode == 1


def test_secret_pattern_fails(repo):
    (repo / "k.txt").write_text("token = ghp_" + "a1B2c3D4e5" * 3 + "\n")  # pragma: allowlist secret (synthetic test token)
    r = scan(repo)
    assert r.returncode == 1 and "k.txt:1" in r.stdout
    assert "ghp_" not in r.stdout  # never echo the secret


def test_env_file_name_fails(repo):
    (repo / ".env").write_text("X=1\n")
    assert scan(repo).returncode == 1


def test_term_in_history_only_fails_with_history_flag(repo):
    (repo / "a.md").write_text("acmecorp\n")
    commit_all(repo, "add")
    (repo / "a.md").write_text("clean now\n")
    commit_all(repo, "remove")
    assert scan(repo).returncode == 0
    r = scan(repo, "--history")
    assert r.returncode == 1 and "a.md" in r.stdout


def test_term_inside_binary_fails(repo):
    (repo / "blob.bin").write_bytes(os.urandom(512) + b"\x00acmecorp\x00" + os.urandom(512))
    assert scan(repo).returncode == 1


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg missing")
def test_term_in_video_metadata_fails(repo):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1",
         "-metadata", "title=acmecorp", str(repo / "clip.mp4")],
        check=True,
    )
    assert scan(repo).returncode == 1


def test_explicit_path_only_scans_that_path(repo):
    (repo / "bad.md").write_text("acmecorp\n")
    (repo / "ok.md").write_text("fine\n")
    assert scan(repo, "ok.md").returncode == 0
    assert scan(repo, "bad.md").returncode == 1


def test_missing_denylist_fails_closed(repo):
    env = env_for(repo)
    del env["CS_DENYLIST"]  # HOME is a temp dir, so the default path does not exist
    (repo / "a.md").write_text("x\n")
    assert scan(repo, env=env).returncode == 2


def test_empty_denylist_fails_closed(repo):
    (repo.parent / "deny.txt").write_text("# only comments\n\n   \n")
    (repo / "a.md").write_text("x\n")
    assert scan(repo).returncode == 2


def hook(repo):
    subprocess.run(["git", "config", "core.hooksPath", str(HOOKS)], cwd=repo, check=True)
    return subprocess.run(
        [*GIT, "commit", "-qm", "x"], cwd=repo, env=env_for(repo), capture_output=True, text=True
    )


def test_pre_commit_blocks_staged_term_only(repo):
    (repo / "ok.md").write_text("fine\n")
    commit_all(repo, "base")
    (repo / "ok.md").write_text("fine again\n")
    (repo / "dirty.md").write_text("acmecorp\n")  # not staged: must not block
    subprocess.run(["git", "add", "ok.md"], cwd=repo, check=True)
    assert hook(repo).returncode == 0
    subprocess.run(["git", "add", "dirty.md"], cwd=repo, check=True)
    (repo / "ok.md").write_text("more\n")
    subprocess.run(["git", "add", "ok.md"], cwd=repo, check=True)
    assert hook(repo).returncode == 1


def test_pre_push_scans_history(repo):
    (repo / "a.md").write_text("acmecorp\n")
    commit_all(repo)
    (repo / "a.md").write_text("clean\n")
    commit_all(repo)
    r = subprocess.run(
        [str(HOOKS / "pre-push")], cwd=repo, env=env_for(repo), capture_output=True, text=True
    )
    assert r.returncode == 1


def test_scanner_does_not_flag_its_own_files(repo):
    (repo.parent / "deny.txt").write_text("unused" + "-dummy\n")  # only the secret patterns apply
    r = subprocess.run(
        [str(SCAN), "scripts/leakscan.sh", "scripts/hooks/pre-commit", "scripts/hooks/pre-push", "tests/test_leakscan.py"],
        cwd=ROOT, env=env_for(repo), capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout


def test_directory_argument_scanned_recursively(repo):
    (repo / "sub" / "deep").mkdir(parents=True)
    (repo / "sub" / "deep" / "a.md").write_text("acmecorp\n")
    assert scan(repo, "sub").returncode == 1


def test_nonexistent_path_exits_2(repo):
    assert scan(repo, "nope.md").returncode == 2


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read anything")
def test_unreadable_file_is_a_finding(repo):
    f = repo / "locked.md"
    f.write_text("fine\n")
    f.chmod(0)
    r = scan(repo, "locked.md")
    f.chmod(0o600)
    assert r.returncode == 1 and "locked.md:0: unreadable" in r.stdout


def test_dash_filename_scanned(repo):
    (repo / "-evil.md").write_text("acmecorp\n")
    (repo / "-bin.dat").write_bytes(os.urandom(256) + b"\x00acmecorp\x00")
    r = scan(repo)
    assert r.returncode == 1 and "-evil.md:1" in r.stdout and "-bin.dat:0" in r.stdout
    assert scan(repo, "-evil.md").returncode == 1


def test_pipe_in_filename_reported_intact(repo):
    (repo / "a|b-acmecorp.md").write_text("tok ghp_" + "a1B2c3D4e5" * 3 + "\n")  # pragma: allowlist secret (synthetic test token)
    r = scan(repo)
    assert r.returncode == 1
    assert "a|b-acmecorp.md:0: path contains acmecorp" in r.stdout
    assert "a|b-acmecorp.md:1: secret pattern" in r.stdout


def test_staged_content_scanned_not_working_tree(repo):
    (repo / "ok.md").write_text("fine\n")
    commit_all(repo, "base")
    (repo / "ok.md").write_text("acmecorp\n")
    subprocess.run(["git", "add", "ok.md"], cwd=repo, check=True)
    (repo / "ok.md").write_text("fine\n")  # edited out, unstaged
    assert hook(repo).returncode == 1


def test_commit_message_hit_not_attributed_to_previous_file(repo):
    (repo / "a.md").write_text("one\n")
    commit_all(repo, "message mentions acmecorp")
    (repo / "b.md").write_text("two\n")
    commit_all(repo, "second")
    r = scan(repo, "--history")
    assert r.returncode == 1 and "b.md" not in r.stdout


def test_pre_commit_scans_renamed_and_edited_file(repo):
    body = "".join(f"line {i} of plain text\n" for i in range(20))
    (repo / "a.md").write_text(body)
    commit_all(repo, "base")
    subprocess.run(["git", "mv", "a.md", "b.md"], cwd=repo, check=True)
    (repo / "b.md").write_text(body + "acmecorp\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    assert hook(repo).returncode == 1


def test_pre_commit_fails_closed_when_git_diff_fails(repo, tmp_path):
    (repo / "a.md").write_text("fine\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    real = shutil.which("git")
    shim = tmp_path / "bin"
    shim.mkdir()
    (shim / "git").write_text(f'#!/bin/sh\n[ "$1" = diff ] && exit 128\nexec {real} "$@"\n')
    (shim / "git").chmod(0o755)
    subprocess.run(["git", "config", "core.hooksPath", str(HOOKS)], cwd=repo, check=True)
    r = subprocess.run(
        [str(HOOKS / "pre-commit")], cwd=repo,
        env=env_for(repo, PATH=f"{shim}:{os.environ['PATH']}"), capture_output=True, text=True,
    )
    assert r.returncode == 2


def test_default_mode_skips_deleted_and_dangling(repo):
    (repo / "gone.md").write_text("fine\n")
    commit_all(repo, "base")
    (repo / "gone.md").unlink()  # tracked, deleted in the working tree
    (repo / "dangling").symlink_to("missing-target")
    assert scan(repo).returncode == 0
    assert scan(repo, "gone.md").returncode == 2  # explicit paths still fail closed


def test_pre_commit_handles_several_staged_files(repo):
    (repo / "x.md").write_text("fine\n")
    (repo / "y.md").write_text("acmecorp\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    r = hook(repo)
    assert r.returncode == 1 and "y.md:1" in r.stdout + r.stderr
