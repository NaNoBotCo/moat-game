#!/bin/zsh
# Double-click launcher for Moat.
cd "$(dirname "$0")"
python3 -m game
echo
echo "Press return to close."
read
