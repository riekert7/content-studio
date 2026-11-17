# Quickstart

Ten minutes from install to your first script. You need Claude Code. Nothing else costs money.

## 1. Make a project folder

Content Studio writes your brand files and videos into the folder you start Claude Code in, so pick a folder for it. Not your home folder.

```
mkdir ~/content
cd ~/content
claude
```

## 2. Install the plugin

Inside Claude Code:

```
/plugin marketplace add riekert7/content-studio
/plugin install content-studio@content-studio
```

## 3. Check your computer

```
/content-studio:doctor
```

It lists what is installed and what is missing, with the command to fix each one. You need `ffmpeg`, `yt-dlp` and `uv`. Run the fix commands it shows, then run the doctor again until nothing says MISSING.

## 4. Set up your brand

```
/content-studio:setup-brand
```

Claude asks about you one question at a time and writes five short files into `brands/<name>/`. Have three real things you have written or said ready to paste (posts, messages, voice-note text). To see what finished files look like, open `examples/lumen-coffee/` in this repo.

## 5. Research, then script

```
/content-studio:research
/content-studio:script
```

Research finds videos that already work for your viewers. Script gives you three options (one out there), a blind critic marks them, and you pick. You get `script.md`, `beats.md` and a film card telling you what to shoot.

## 6. Film, then build

Film the takes yourself, put them in `inbox/`, and run:

```
/content-studio:make-video
/content-studio:cover
```

You get a first cut and a cover. You post it yourself.

## If something goes wrong

- `MISSING` in the doctor: run the `fix:` line it shows.
- A link will not download: Instagram, TikTok and sometimes YouTube block it. Download the video yourself and give Claude the file.
- Claude asks permission for every command: run `/content-studio:doctor` and say yes when it offers the permission rules.
