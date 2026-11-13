#!/usr/bin/env bash
# Leak scan: deny-list terms and secret patterns in files (and optionally git history).
# Usage: leakscan.sh [--history] [--] [PATH...]
# Deny-list: $CS_DENYLIST or ~/.config/content-studio/denylist.txt (one term per line, # comments,
# case-insensitive). It lives outside the repo because it names private things.
# Exit: 0 clean, 1 finding (file:line: term), 2 deny-list missing or empty.
export LC_ALL=C
history=0
paths=()
while [ $# -gt 0 ]; do
  case "$1" in
    --history) history=1 ;;
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

if [ ${#paths[@]} -eq 0 ]; then
  if git rev-parse --git-dir >/dev/null 2>&1; then
    mapfile -d '' -t paths < <(git ls-files -co --exclude-standard -z)
  else
    mapfile -d '' -t paths < <(find . -type f -not -path './.git/*' -print0)
  fi
fi

# print "label:line: term" for each deny-list hit read from stdin (grep -n output)
fmt() { awk -F: -v l="$1" '{n=$1; sub(/^[0-9]+:/,""); print l":"n": "$0}'; }

scan_file() {
  local f="$1" out
  # names: deny-list term in the path, or an .env file
  out=$(printf '%s\n' "$f" | grep -oiF -f "$terms" | sed "s|^|$f:0: path contains |")
  [ -n "$out" ] && report "$out"
  case "$(basename "$f")" in .env*) report "$f:0: .env file" ;; esac
  [ -f "$f" ] || return 0
  if grep -qI '' "$f" 2>/dev/null; then
    out=$(grep -naoiF -f "$terms" -- "$f" | fmt "$f")
    [ -n "$out" ] && report "$out"
    out=$(grep -naE -f "$secrets" -- "$f" | cut -d: -f1 | sed "s|\$|: secret pattern|;s|^|$f:|")
    [ -n "$out" ] && report "$out"
  else
    # ponytail: binary hits have no line number; strings is optional, grep -a is the fallback
    local dump="$work/dump"
    if have strings; then strings -a -n 3 "$f" > "$dump"; else grep -a -o '[[:print:]]\{3,\}' "$f" > "$dump"; fi
    meta_dump "$f" >> "$dump"
    out=$(grep -aoiF -f "$terms" "$dump" | sort -u | sed "s|^|$f:0: binary contains |")
    [ -n "$out" ] && report "$out"
    grep -qaE -f "$secrets" "$dump" && report "$f:0: secret pattern"
  fi
}

# media tags via ffprobe / exiftool when present (both optional)
meta_dump() {
  have ffprobe && ffprobe -v quiet -show_format "$1" 2>/dev/null | grep -i '^TAG:'
  have exiftool && exiftool "$1" 2>/dev/null
  return 0
}

for f in "${paths[@]}"; do scan_file "$f"; done

if [ "$history" = 1 ] && git rev-parse --git-dir >/dev/null 2>&1; then
  log="$work/log"
  git log -p --all --text > "$log" 2>/dev/null
  out=$(awk -v tf="$terms" '
    BEGIN { while ((getline t < tf) > 0) T[++n] = tolower(t) }
    /^commit / { c = substr($2, 1, 8) }
    /^\+\+\+ / { f = substr($0, 7) }
    { l = tolower($0); for (i = 1; i <= n; i++) if (index(l, T[i])) print "history " c ":" f ": " T[i] }
  ' "$log" | sort -u)
  [ -n "$out" ] && report "$out"
  for n in $(grep -naE -f "$secrets" "$log" | cut -d: -f1); do
    report "history $(head -n "$n" "$log" | grep -a '^commit ' | tail -1 | cut -c8-15): secret pattern"
  done
fi

exit "$found"
