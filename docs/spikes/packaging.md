# Packaging spike (2026-11-13)

Claude Code 2.1.317, codex-cli 0.160.0, uv from mise, Linux. Local repo with a minimal `pyproject.toml` (`cs = "content_studio.cli:main"`), throwaway `.claude-plugin/{plugin.json,marketplace.json}` and `skills/probe/SKILL.md`. All throwaway files were deleted afterwards.

Deps are pinned to what `uv` resolves today: `faster-whisper==1.2.1`, `numpy==2.5.4`. numpy 2.5.4 needs Python 3.12, so `pyproject.toml` pins `numpy==2.4.6` for `python_version < '3.12'` to keep `requires-python = ">=3.11"`.

## 1. `uvx --from`

- `uvx --from . cs --version` from the repo root: prints `content-studio 0.1.0`. Works.
- `uvx --from "git+file://$PWD" cs --version`: works, and so does `...@v0.1.0` with a tag, **but it builds the last commit, not the working tree**. My first attempt failed (`does not appear to be a Python project`) because `pyproject.toml` was not committed yet. I tested on a scratch git repo with the skeleton committed and tagged.
- Output (both): `Installed 24 packages in ~150ms` then `content-studio 0.1.0`. uv caches the build, so later runs are quick.
- Decision: inside Claude Code, point `--from` at the plugin root; for every other agent, use `git+https://github.com/riekert7/content-studio@v0.1.0` (the form needs the tag to exist, so the release script must tag before anyone uses it).

## 2. Root-level plugin plus marketplace entry with `"source": "./"`

Commands (`CLAUDE_CONFIG_DIR=<tmp>` worked for these; see item 3 for why I left it later):
```
claude plugin marketplace add <path-to-repo>
  -> Successfully added marketplace: content-studio-spike
claude plugin install content-studio@content-studio-spike
  -> Successfully installed plugin: content-studio@content-studio-spike (scope: user)
claude plugin list  -> Version 0.1.0, Read from: <repo path>, Status: enabled
```
`marketplace.json`: `{"name":"content-studio-spike","owner":{"name":"riekert7"},"plugins":[{"name":"content-studio","source":"./","description":"spike"}]}`. `plugin.json`: `name`, `version`, `description`. Works with a root-level plugin; no further fields needed.

Findings:
- A **local-path (directory) marketplace is used in place**: `Read from:` is the repo and `${CLAUDE_SKILL_DIR}` resolves into the repo, not the cache (see item 4).
- The cache copy (`plugins/cache/<marketplace>/<plugin>/<version>/`) is a raw copy of the **working directory, including untracked and ignored files** (`.venv`, `.superpowers`, `docs/superpowers/`). A GitHub-sourced marketplace would not do that (tracked files only); the release gate must not rely on a local-path install to judge what ships.
- `claude plugin marketplace add` does **not** accept a `file://` or `git+file://` URL ("Invalid marketplace source format"); only `owner/repo`, https URLs or a path. I could not test the GitHub-sourced `"./"` layout without pushing (needs the owner's yes). Task 10 should test it after the push.
- The `"source": "./"` entry was only proven for a directory marketplace. The cached-copy behaviour below was proven with a marketplace entry `{"source":"url","url":"file://<git repo>"}`, which is the same thing mechanically (a git checkout copied into the cache).

## 3. A skill that runs `uvx --from ${CLAUDE_SKILL_DIR}/../.. cs --version`

`claude -p` needs a login. The isolated config dir was not logged in (`Not logged in · Please run /login`), and I did not copy credentials in. So I used the real config with `--scope local` from a throwaway project directory, then removed everything (see Cleanup).

Probe skill (frontmatter: `name`, `description`, `allowed-tools`). Body told Claude to run the command and report the literal `${CLAUDE_SKILL_DIR}`. Each case ran `claude -p ... --output-format json < /dev/null` in the temp project (`< /dev/null` is needed or claude waits 3 s for stdin).

| Case | `allowed-tools` | How invoked | Result |
|---|---|---|---|
| A | none | `/content-studio:probe` | Bash **denied** ("This command requires approval") |
| B | `Bash(uvx --from ${CLAUDE_SKILL_DIR}/../.. cs *)` | `/content-studio:probe` | runs, `content-studio 0.1.0`, 0 denials |
| C | `Bash(uvx *)` | `/content-studio:probe` | runs, 0 denials |
| D | `Bash(uvx --from "${CLAUDE_SKILL_DIR}/../.." cs *)` (quoted in command and pattern) | `/content-studio:probe` | runs, 0 denials |
| E | D | `claude -p "run the cs probe" --allowedTools "Skill(content-studio:probe)"` (model picks the skill) | runs, 0 denials |
| F | B | same as E | runs, 0 denials |

- `claude -p "run the cs probe"` with no `--allowedTools` is denied at the **Skill** tool call itself (non-interactive mode cannot approve it). That is a `-p` limit, not a pattern problem; slash invocation and `--allowedTools Skill(...)` both work.
- Decision: use the quoted form (D). It matches the pattern literally and survives a home folder with spaces (not tested with a real path containing spaces).
- The tool is called through `uvx`, so `cs` need not be on PATH. uv builds in its own cache; nothing was written into the plugin folder (checked: only Claude's own `.in_use` marker is new).

## 4. Does `${CLAUDE_SKILL_DIR}` resolve to the cached copy, and is `../..` the plugin root?

- Directory-source marketplace: `${CLAUDE_SKILL_DIR}` = `<path-to-repo>/skills/probe` (the repo itself).
- Git-sourced plugin (copied to cache): `${CLAUDE_SKILL_DIR}` = `<home>/.claude/plugins/cache/cs-spike-git/content-studio/0.1.0/skills/probe`. `../..` is the plugin root (it holds `pyproject.toml`), and `uvx --from <that>/../.. cs --version` built from the cache copy and printed `content-studio 0.1.0`.
- Yes to both. `${CLAUDE_SKILL_DIR}` is substituted into the skill text (the model saw the absolute path); it is not an env var.

## 5. Codex

`which codex` -> installed (codex-cli 0.160.0), but `codex login status` says "Not logged in". I did not work around it. **Codex untested**: whether it loads `skills/probe` from `.agents/skills/` is unknown. What is proven is that the command a Codex agent would run, `uvx --from "git+<url>@<tag>" cs --version`, works (item 1).

## Cleanup

Used `--scope local` in a temp project (`<scratchpad>/proj`), so no user-level settings file was edited. Afterwards: `claude plugin uninstall --scope local ...`, `claude plugin marketplace remove ...` (both marketplaces), deleted `~/.claude/plugins/cache/{content-studio-spike,cs-spike-git}` and the probe project's session folder. `claude plugin list` and `claude plugin marketplace list` are identical to their pre-spike output (diffed), and the md5 of `~/.claude/settings.json` and of `plugins/*.json` is unchanged. `~/.claude.json` changes on every `claude` run (per-project state), so it differs.

## Decisions for Tasks 5 to 9

1. Skills call the package through `uvx`, never `cs` on PATH, never a `tools/*.py` path.
2. Quote the plugin root and put the same string in `allowed-tools`.
3. Other agents use the git URL at the release tag. `AGENTS.md` and README must say Codex is untested.
4. A local-path install proves the manifest layout and `${CLAUDE_SKILL_DIR}`, but it copies untracked files; the leak scan and release script work from git, not from the cache.
5. Test non-interactive skills with `/content-studio:<skill>` or `--allowedTools "Skill(content-studio:<skill>)"`, and `< /dev/null`.
6. The GitHub-sourced `"source": "./"` layout still needs one real test after the push is approved.

CS_INVOKE: uvx --from "${CLAUDE_SKILL_DIR}/../.." cs
allowed-tools: Bash(uvx --from "${CLAUDE_SKILL_DIR}/../.." cs *)
