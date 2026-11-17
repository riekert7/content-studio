---
name: setup-brand
description: Interview the user and write the five brand files (brand, voice, style, formats, viewers) into brands/<brand>/ in their project folder. Use when they want to start, add a brand or person to make videos for, or when brands/<brand>/ is missing or empty.
license: MIT
compatibility: Needs the project folder Claude Code was started in to be a folder the user chose for this work, not their home folder.
allowed-tools: Bash(uvx --from "${CLAUDE_SKILL_DIR}/../.." cs *) Read
---

# Set up a brand

`cs` below means `uvx --from "${CLAUDE_SKILL_DIR}/../.." cs`. The interview lives in `references/interview.md`: read it before the first question.

0. Run `cs doctor`. If a required tool is MISSING, stop and hand over to the doctor skill.
1. Run `cs workspace .`. If it refuses, the user started Claude Code in their home folder. Tell them to make a project folder (for example `mkdir ~/content`), start Claude Code inside it, and run this skill again. Do not write anything until it passes.
2. Ask the brand's short name (letters, digits, hyphens). It becomes `brands/<name>/`. If that folder already has files, ask whether to add to it or leave it; never overwrite without a yes.
3. Run the interview in `references/interview.md`: one question at a time, in the user's words, with a real example from them wherever a file needs one. Never invent a fact about their business; leave a gap and say it is a gap.
4. Copy `${CLAUDE_SKILL_DIR}/../../templates/brand/` to `brands/<name>/`, then fill each of the five files with the user's answers. Replace the italic prompts with real content.
5. Run `cs brandcheck brands/<name> --filled`. Fix every line it prints, then run it again until it prints nothing.
6. Show the user the five files in short, ask what is wrong, and fix it. Remind them nothing leaves their computer.
7. Tell them the next steps: `/content-studio:research`, then `/content-studio:script`.
