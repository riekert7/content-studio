# Third-party code

## instagram-agent-skill (vendored)

`src/content_studio/vendor/hookscore.py`, `detect.py` and `slop.json` are copied from
https://github.com/Jakeschincariol/instagram-agent-skill (MIT, commit `d03c56b`).
Only the local text scripts were taken; none of its posting, commenting or DM skills.

- `hookscore.py` scores a hook line on length, a concrete marker, stakes, payload first and a viewer. It catches weak hooks; it does not predict views (the upstream README reports AUC 0.56 between a creator's hits and misses). Use it to drop dealbreakers only.
- `detect.py` with `slop.json` flags AI-sounding phrases in a caption or script.

Changes from upstream: none. `detect.py` already finds `slop.json` next to itself, so it works as package data once `slop.json` is shipped in the wheel (see `pyproject.toml`). The only addition is an empty `vendor/__init__.py`.

### Licence

MIT License

Copyright (c) 2026 Jake Schincariol

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Linked, not bundled

Nothing below is copied into this repo or its package. They are listed in the README so a user can look at them and read the licence for themselves.

| Project | Licence (read on GitHub, 17 Nov 2026) | Note |
|---|---|---|
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Apache-2.0 | write videos as HTML; not used by v0.1 |
| [feitangyuan/onetake](https://github.com/feitangyuan/onetake) | PolyForm Noncommercial 1.0.0 | no commercial use without its paid licence |
| [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) | none stated (GitHub: NOASSERTION) | ideas only; ask the author before reusing anything |
| [JohnHeibel/ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase) | MIT | uses Anthropic's mascot artwork |
