---
name: doctor
description: Check that Content Studio can run on this computer and say what is missing and how to fix it. Use when the user has just installed the plugin, something fails with a missing tool, or they ask whether their setup is ready.
license: MIT
compatibility: Needs uv. Works with ffmpeg, ffprobe, yt-dlp and optionally Node installed.
allowed-tools: Bash(uvx --from "${CLAUDE_SKILL_DIR}/../.." cs *)
---

# Doctor

`cs` below means `uvx --from "${CLAUDE_SKILL_DIR}/../.." cs`.

0. Run `cs doctor`.
1. Read the result line by line. `ok` is fine. `MISSING` means a required tool is absent: show the user the `fix:` line for it, one tool at a time, and wait until they say it is installed. `later` means optional: tell them what it is for and move on.
2. Run `cs doctor` again after each fix until nothing required is MISSING.
3. Offer the permission rules: run `cs doctor --allow` and show the JSON. Say these go into `.claude/settings.json` in their project folder so Claude stops asking before each web search and fetch, and that you will only write the file if they say yes. If they say yes, merge the rules into the existing `permissions.allow` list (create the file if it does not exist), keep everything already there.
4. If they have a link they want to learn from, run `cs doctor --url <link>`. If it cannot be downloaded, tell them to download the video themselves and use the local file.
5. Finish by telling them the next step: run `/content-studio:setup-brand`.

Do not install anything yourself. The user runs the fix commands.
