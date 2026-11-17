# First cut with ffmpeg

Work in `out/<slug>/`. Keep the raw takes untouched in `inbox/`.

## 1. Trim and conform each take

For each beat in `beats.md`, cut the matching take to its duration and conform it:

```
ffmpeg -y -ss <take-start> -i inbox/<take> -t <beat-length> \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -ar 48000 -ac 2 out/<slug>/part-<n>.mp4
```

If a take has no audio, add a silent track so concatenation works, then note it: a silent video is flagged by `cs check`.

## 2. Join

Write `out/<slug>/parts.txt` with one `file 'part-<n>.mp4'` line per beat in order, then:

```
ffmpeg -y -f concat -safe 0 -i out/<slug>/parts.txt -c copy out/<slug>/joined.mp4
```

## 3. Captions

Write `captions.srt` from `script.md` and the beat times. Style from `style.md` (position bottom third, two to four words at a time, accent colour on the key word). Burn in:

```
ffmpeg -y -i out/<slug>/joined.mp4 -vf "subtitles=out/<slug>/captions.srt:force_style='FontName=<font>,Bold=1,FontSize=14,Alignment=2,MarginV=300,PrimaryColour=&HFFFFFF&'" -c:a copy out/<slug>/cut.mp4
```

Colours in `force_style` are `&HBBGGRR&`, so convert the hex codes from `style.md`.

## 4. Loudness

Aim for about -14 LUFS. If `cs check` flags it, normalise in one pass:

```
ffmpeg -y -i out/<slug>/cut.mp4 -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:v copy out/<slug>/cut-loud.mp4
```

then use `cut-loud.mp4` as the cut and re-check.

## What this does not do

No music, no animation, no generated footage. Cuts land where `beats.md` says; keep the first beat under 3 seconds and vary shot lengths (`cs beats` checks).
