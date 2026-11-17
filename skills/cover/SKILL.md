---
name: cover
description: Make a cover image for a finished video (a chosen frame with an optional title, plus a preview of how it crops on a profile grid) or a contact sheet to choose the frame from. Use when the user asks for a cover, thumbnail or cover frame for a video in out/<slug>/.
license: MIT
compatibility: Needs ffmpeg and ffprobe.
allowed-tools: Bash(uvx --from "${CLAUDE_SKILL_DIR}/../.." cs *) Read
---

# Cover

`cs` below means `uvx --from "${CLAUDE_SKILL_DIR}/../.." cs`.

0. Run `cs doctor`. If ffmpeg is MISSING, stop and hand over to the doctor skill.
1. Ask which video (normally `out/<slug>/cut.mp4`).
2. Make a contact sheet to choose a frame: `cs cover out/<slug>/cut.mp4 --sheet --out out/<slug>/sheet.jpg`. Read the image and show it to the user with the timestamps.
3. Ask which second looks best (a clear face, hands or product, a moment mid-action) and whether the cover needs a title. A title is at most five words, in the brand's voice from `brands/<name>/voice.md`, no hype.
4. Make it: `cs cover out/<slug>/cut.mp4 --at <seconds> --title "<title>" --out out/<slug>/cover.jpg`. This also writes `cover.grid.jpg`, the middle 3:4 crop that profile grids show.
5. Read both images. Check the title is inside the grid crop and nothing important is cut off. If it is, change the second or the title and run step 4 again.
6. Tell the user where the files are. They upload the cover themselves.
