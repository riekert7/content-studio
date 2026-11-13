#!/usr/bin/env bash
# Leak scan: deny-list terms and secret patterns in files (and optionally git history).
# Usage: leakscan.sh [--history] [--staged] [--] [PATH...]
# PATH may be a file or a directory (scanned recursively). --staged scans the index copy of each PATH (pre-commit).
# Deny-list: $CS_DENYLIST or ~/.config/content-studio/denylist.txt (one term per line, # comments,
# case-insensitive). It lives outside the repo because it names private things.
# Exit: 0 clean, 1 finding (file:line: term), 2 deny-list missing or empty, or a PATH that does not exist.
# A file that cannot be read, or a grep/strings error while scanning it, is reported as a finding
# ("file:0: unreadable" / "file:0: scan error", exit 1): a scan that could not look must never pass.
export LC_ALL=C
history=0
staged=0
paths=()
while [ $# -gt 0 ]; do
  case "$1" in
    --history) history=1 ;;
    --staged) staged=1 ;;
    --) shift; paths+=("$@"); break ;;
    *) paths+=("$1") ;;
  esac
  shift
done

list="${CS_DENYLIST:-$HOME/.config/content-studio/denylist.txt}"
[ -r "$list" ] || { echo "leakscan: deny-list not found: $list" >&2; exit 2; }
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
terms="$work/terms"
sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$list" | grep -v -e '^#' -e '^$' > "$terms"
[ -s "$terms" ] || { echo "leakscan: deny-list has no terms: $list" >&2; exit 2; }

# patterns are written so this file does not match itself (PRIV[A]TE)
secrets="$work/secrets"
cat > "$secrets" <<'PAT'
sk-[A-Za-z0-9]{20,}
ghp_[A-Za-z0-9]{30,}
AKIA[0-9A-Z]{16}
-----BEGIN .*PRIV[A]TE KEY-----
PAT

have() { command -v "$1" >/dev/null 2>&1; }
found=0
report() { found=1; printf '%s\n' "$1"; }

# expand directories, reject missing paths (never a silent pass)
if [ ${#paths[@]} -eq 0 ]; then
  if git rev-parse --git-dir >/dev/null 2>&1; then
    # default list only: skip tracked-but-deleted files and dangling symlinks (explicit paths still fail closed)
    mapfile -d '' -t paths < <(git ls-files -co --exclude-standard -z)
    kept=(); for p in "${paths[@]}"; do [ -e "$p" ] && kept+=("$p"); done; paths=("${kept[@]}")
  else
    mapfile -d '' -t paths < <(find . -type f -not -path './.git/*' -print0)
  fi
elif [ "$staged" = 0 ]; then
  expanded=()
  for p in "${paths[@]}"; do
    fs="$p"; case "$p" in -*) fs="./$p" ;; esac
    if [ -d "$fs" ]; then
      while IFS= read -r -d '' x; do expanded+=("$x"); done < <(find "$fs" -type f -not -path '*/.git/*' -print0)
    elif [ -e "$fs" ]; then
      expanded+=("$p")
    else
      echo "leakscan: path not found: $p" >&2; exit 2
    fi
  done
  paths=("${expanded[@]}")
fi

# "label:line: term" for each grep -n/-o hit on stdin; ENVIRON keeps backslashes and | in names intact
fmt() { L="$1" awk -F: '{n=$1; sub(/^[0-9]+:/,""); print ENVIRON["L"] ":" n ": " $0}'; }

# scan_content LABEL FILE: FILE is a readable-or-not filesystem path holding the content to scan
scan_content() {
  local label="$1" f="$2" out rc
  [ -r "$f" ] || { report "$label:0: unreadable"; return; }
  grep -qI '' -- "$f" 2>/dev/null; rc=$?
  if [ $rc -eq 0 ]; then
    out=$(grep -naoiF -f "$terms" -- "$f"; echo "rc=$?")
    rc=${out##*rc=}; out=${out%rc=*}
    [ "$rc" -ge 2 ] && report "$label:0: scan error"
    [ -n "$out" ] && report "$(printf '%s' "$out" | fmt "$label")"
    out=$(grep -naE -f "$secrets" -- "$f" | cut -d: -f1; echo "rc=${PIPESTATUS[0]}")
    rc=${out##*rc=}; out=${out%rc=*}
    [ "$rc" -ge 2 ] && report "$label:0: scan error"
    for n in $out; do report "$label:$n: secret pattern"; done
  elif [ $rc -eq 1 ]; then
    # ponytail: binary hits have no line number; strings is optional, grep -a is the fallback
    local dump="$work/dump" fs="$f"; case "$f" in -*) fs="./$f" ;; esac
    if have strings; then strings -a -n 3 -- "$fs" > "$dump" || report "$label:0: scan error"
    else grep -a -o '[[:print:]]\{3,\}' -- "$f" > "$dump"; fi
    meta_dump "$fs" >> "$dump"
    grep -aoiF -f "$terms" "$dump" | sort -u | while IFS= read -r t; do printf '%s:0: binary contains %s\n' "$label" "$t"; done > "$work/hits"
    [ -s "$work/hits" ] && report "$(cat "$work/hits")"
    grep -qaE -f "$secrets" "$dump" && report "$label:0: secret pattern"
  else
    report "$label:0: scan error"
  fi
}

# media tags via ffprobe / exiftool when present (both optional); $1 is already ./-safe
meta_dump() {
  have ffprobe && ffprobe -v quiet -show_format "$1" 2>/dev/null | grep -i '^TAG:'
  have exiftool && exiftool "$1" 2>/dev/null
  return 0
}

scan_file() {
  local f="$1" t base fs="$1"
  case "$f" in -*) fs="./$f" ;; esac
  # names: deny-list term in the path, or an .env file
  grep -oiF -f "$terms" <<<"$f" | while IFS= read -r t; do printf '%s:0: path contains %s\n' "$f" "$t"; done > "$work/hits"
  [ -s "$work/hits" ] && report "$(cat "$work/hits")"
  base=$(basename -- "$f")
  case "$base" in .env*) report "$f:0: .env file" ;; esac
  if [ "$staged" = 1 ]; then
    # scan what is staged, not the working-tree copy
    git show ":$f" > "$work/staged" 2>/dev/null || { report "$f:0: unreadable"; return; }
    scan_content "$f" "$work/staged"
  else
    scan_content "$f" "$fs"
  fi
}

for f in "${paths[@]}"; do scan_file "$f"; done

if [ "$history" = 1 ] && git rev-parse --git-dir >/dev/null 2>&1; then
  log="$work/log"
  git log -p --all --text > "$log" 2>/dev/null || { echo "leakscan: git log failed" >&2; exit 2; }
  out=$(awk -v tf="$terms" '
    BEGIN { while ((getline t < tf) > 0) T[++n] = tolower(t) }
    /^commit / { c = substr($2, 1, 8); f = "" }
    /^\+\+\+ / { f = substr($0, 7) }
    { l = tolower($0); for (i = 1; i <= n; i++) if (index(l, T[i])) print "history " c ":" f ": " T[i] }
  ' "$log" | sort -u)
  [ -n "$out" ] && report "$out"
  for n in $(grep -naE -f "$secrets" "$log" | cut -d: -f1); do
    report "history $(head -n "$n" "$log" | grep -a '^commit ' | tail -1 | cut -c8-15): secret pattern"
  done
fi

exit "$found"
