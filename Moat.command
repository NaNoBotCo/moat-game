#!/bin/zsh
# Double-click launcher for Moat.
#
# Apple's stock /usr/bin/python3 is 3.9 and cannot even parse this codebase,
# and Homebrew's python@3.13 ships no bare `python3` symlink — so resolve a
# new-enough interpreter ourselves instead of trusting PATH.
cd "$(dirname "$0")"

PY=""
for cand in \
    /opt/homebrew/bin/python3.14 /opt/homebrew/bin/python3.13 \
    /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3 \
    /usr/local/bin/python3.14 /usr/local/bin/python3.13 \
    /usr/local/bin/python3.12 /usr/local/bin/python3 \
    python3.14 python3.13 python3.12 python3
do
    command -v "$cand" >/dev/null 2>&1 || continue
    "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null || continue
    PY="$cand"
    break
done

if [[ -z "$PY" ]]; then
    echo "Moat needs Python 3.12 or newer, and none was found."
    echo "Install one with:  brew install python@3.13"
else
    "$PY" -m game
fi

echo
echo "Press return to close."
read
