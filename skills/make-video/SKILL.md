---
name: make-video
description: Assemble a first cut of a short vertical video from the user's own takes in inbox/ following scripts/<slug>/beats.md, check the file, and have three imagined viewers react before showing it. Use when the takes are filmed and the user wants the video edited or checked.
license: MIT
compatibility: Needs ffmpeg and ffprobe. Uses the user's own footage and audio; it does not generate footage or download music.
allowed-tools: Bash(uvx --from "${CLAUDE_SKILL_DIR}/../.." cs *) Bash(ffmpeg *) Bash(ffprobe *) Read
---

# Make a video

`cs` below means `uvx --from "${CLAUDE_SKILL_DIR}/../.." cs`. Read `references/first-cut.md` first.

0. Run `cs doctor`. If ffmpeg or ffprobe is MISSING, stop and hand over to the doctor skill.
1. Ask which script (a folder in `scripts/`). Read its `beats.md`, `script.md` and `film-card.md`, and `brands/<name>/style.md` and `formats.md`.
2. Look in `inbox/` for the user's takes. Run `ffprobe` on each. Match takes to beats using the film card. If a beat has no take, say which one is missing and stop; do not invent footage.
3. Build the cut as `references/first-cut.md` describes, into `out/<slug>/cut.mp4`: 1080x1920, 30 fps, the user's own audio, captions from `style.md`.
4. Run `cs check out/<slug>/cut.mp4`. Fix every FLAG it prints (shape, frame rate, missing audio, loudness) and run it again until it prints none.
5. Run `cs watch out/<slug>/cut.mp4 --no-transcript --out out/<slug>/watch` to get frame sheets. Run `cs beats scripts/<slug>/beats.md` again to confirm the timing still holds.
6. Start three `content-studio:viewer` agents at once, one per viewer in `brands/<name>/viewers.md`. Give each only the path of its viewer text, the frame sheet and `script.md`. Collect their replies.
7. Show the user the three replies and the one change each suggests. Make the changes they choose, then repeat from step 4. Stop after two rounds unless they ask for more.
8. Offer a cover with `/content-studio:cover`.
9. Tell the user plainly what this is: a first cut from their own takes. Music, effects and animation are not part of v0.1; they can add them in any editor. They post it themselves; you never do.

Never download or add music. If the user wants a trending sound, they add it in the app when they post.
