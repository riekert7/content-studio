# Options

Write `options.json` as a list. One object per option:

```
{"id": "a", "title": "...", "hook": "the first spoken line", "beats": "four to six short beats, one per line",
 "send_reason": "why a viewer would send this to a friend", "out_there": false, "recommended": false}
```

`recommended` is always false: you do not recommend, and the packet strips any hint of a pick.

Each option must have:
- **A real incident, tension or surprising number.** Something that happened, something people argue about, a figure someone can check. Not "5 tips".
- **A person and a stake in the first 1.5 seconds.** Someone is doing or losing something right now.
- **The brand as the turn, not the pitch.** The brand shows up as what changed or what fixed it, late, in one line.
- **A send reason.** One sentence on who would send it to whom.

Three options total. One has `"out_there": true`: a format, angle or voice the user would not normally pick. Say in `send_reason` what is risky about it.

Show them as a table to the user: id, hook, what happens, why send.
