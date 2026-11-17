# Content Studio

A Claude Code plugin that helps you set up a brand, find what already works, script short vertical videos with a blind critic, build a first cut from your own footage and make a cover. It needs Claude Code and a few free tools, and nothing is paid.

## Install, the quick way

Paste this into Claude Code:

```
Install the Claude Code plugin at https://github.com/riekert7/content-studio, then run /content-studio:doctor
```

## Install in the terminal

Make a project folder first (not your home folder), start Claude Code in it, then:

```
/plugin marketplace add riekert7/content-studio
/plugin install content-studio@content-studio
/content-studio:doctor
```

The doctor lists what is missing and how to fix it. You need Claude Code, `ffmpeg`, `yt-dlp` and `uv`. Node is only needed later. See [QUICKSTART.md](QUICKSTART.md) for the first ten minutes.

## Updates

Third-party plugins do not update on their own. To switch it on: run `/plugin`, open Marketplaces, pick `content-studio` and turn on auto-update. Otherwise run `/plugin marketplace update content-studio` when you want the latest.

## Permissions

A plugin cannot grant itself permission. The skills ask only for their own commands, but Claude may still stop to ask before each web search or page fetch. To stop those prompts, run `uvx --from "git+https://github.com/riekert7/content-studio@v0.1.0" cs doctor --allow` (or let `/content-studio:doctor` do it) and put the rules it prints into `.claude/settings.json` in your project folder:

```json
{
  "permissions": {
    "allow": ["WebSearch", "WebFetch", "Bash(uvx --from \"git+https://github.com/riekert7/content-studio@v0.1.0\" cs *)"]
  }
}
```

## The loop

1. `/content-studio:setup-brand`: Claude interviews you and writes five files to `brands/<name>/` (who it is for, how you sound, how it looks, what formats you use, three imagined viewers).
2. `/content-studio:research`: finds videos that work for your viewers, watches the best ones, and writes an evidence pack and a swipe file.
3. `/content-studio:script`: three options (one out there), a blind critic whose marks are checked by code, your pick, then `script.md`, `beats.md` and a film card.
4. `/content-studio:make-video`, then `/content-studio:cover`: a first cut from your own takes, checked for 9:16, 30 fps, sound and loudness, reviewed by three imagined viewers, and a cover image.

You film, you post. Nothing is ever posted for you.

## What is in v0.1, and what is not

In: the six skills above, a brand template and a made-up example brand (`examples/lumen-coffee/`), and the `cs` tools behind them. The first cut is assembled with ffmpeg from your own takes.

Not in: music, animation, templated motion graphics and generated footage. v0.1 does not make those, and the skills say so.

## Other agents

Copy `skills/*` into your agent's skills folder (for example `.agents/skills/`) and read [AGENTS.md](AGENTS.md) for the commands. Claude Code is the tested path. Codex is untested.

## Your files stay yours

Everything you write lives in your project folder (`brands/`, `scripts/`, `out/`, `inbox/`, `research/`). The plugin never stores your data and sends nothing anywhere except the web searches and downloads you ask for.

## Going further

Tools for the things v0.1 skips. These are linked, not bundled, and each has its own licence, so check it before you use it:

- [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0): write videos as HTML.
- [OneTake](https://github.com/feitangyuan/onetake) (PolyForm Noncommercial): free for non-commercial use only. Making videos for a business needs its paid licence.
- [Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar): the licence is not clearly stated, so ask its author before reusing anything.
- [Claude Animation Base](https://github.com/JohnHeibel/ClaudeAnimationBase) (MIT): uses Anthropic's mascot artwork, so do not ship it as your own brand.

## Licence

MIT, see [LICENSE](LICENSE). The vendored scorers are MIT too: see [THIRD_PARTY.md](THIRD_PARTY.md).
