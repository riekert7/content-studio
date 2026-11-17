---
name: script
description: Turn research into three video options (one out-there), have a blind critic mark them, let the user pick and remix, then write the script, beats table and film card into scripts/<slug>/. Use when the user wants to write, plan or choose a short vertical video for a brand, or says what to film.
license: MIT
compatibility: Needs the five brand files in brands/<brand>/. Research in brands/<brand>/research/ is strongly preferred.
allowed-tools: Bash(uvx --from "${CLAUDE_SKILL_DIR}/../.." cs *) Read WebSearch WebFetch
---

# Script

`cs` below means `uvx --from "${CLAUDE_SKILL_DIR}/../.." cs`. Read `references/options-table.md`, `references/critic-rubric.md` and `references/verify-claims.md` before step 3.

0. Run `cs doctor`. If a required tool is MISSING, stop and hand over to the doctor skill.
1. Ask which brand. Run `cs brandcheck brands/<name> --filled`; if it prints anything, hand over to `setup-brand`. Read the five files, the newest file in `brands/<name>/research/` and `swipe.csv`. If there is no research, say so and offer `/content-studio:research` first; continue only if the user says to.
2. Ask what the video is about if the user has not said (a real thing that happened, a question customers keep asking, a mistake). Real incidents, tensions or numbers only: no generic checklists.
3. Draft three options following `references/options-table.md`: each has a real incident, tension or surprising number, a person and a stake in the first 1.5 seconds, and the brand as the turn rather than the pitch. One option must be out-there. Save them as `scripts/<date>-options/options.json` and the evidence as `scripts/<date>-options/evidence.md`.
4. Build the blind packet: `cs packet --options scripts/<date>-options/options.json --evidence scripts/<date>-options/evidence.md --out scripts/<date>-options/packet.md`.
5. Start the critic agent (`content-studio:critic`) with only the path of `packet.md`. Give it nothing else: not the brand files, not which option you prefer. Save its reply as `scripts/<date>-options/marks.json`.
6. Run `cs verify --packet scripts/<date>-options/packet.md --marks scripts/<date>-options/marks.json --out-there <labels of the out-there options>`. Labels come from `packet.map.json` next to the packet. Exit 0 means at least one option survives. Exit 3 means all were dropped: rewrite them from the critic's quotes and go back to step 4; never show dropped options. Exit 2 means the marks were malformed: ask the critic again.
7. Show the survivors with their scores and the quote behind each low score. An option flagged "below threshold, your call" is shown with that note. Do not recommend one. Ask which they pick and what they want to change; they may remix.
8. Verify every claim in the chosen option as `references/verify-claims.md` says. Mark each line verified (with its source) or removed.
9. Write `scripts/<slug>/script.md` (spoken lines in the brand's voice), `scripts/<slug>/beats.md` (a `| Start | End | Beat | Carries |` table) and `scripts/<slug>/film-card.md` (what to shoot, three hook takes, props, light, sound). Copy options.json, packet.md and marks.json into the folder.
10. Run `cs beats scripts/<slug>/beats.md` and fix every flag it prints. Run `cs detect scripts/<slug>/script.md` and rewrite anything it flags as AI-sounding. Run `cs hookscore --hook "<the hook>"` and use it only to drop a dealbreaker.
11. Tell the user what to film and the next step: `/content-studio:make-video` once the takes are in `inbox/`.

Never post anything. The user films, edits and posts.
