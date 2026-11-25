#!/bin/sh
# Nocturne Codex - run (or double-click, if your file manager allows) to open the grimoire.
cd "$(dirname "$0")" || exit 1
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    exec "$candidate" -m nocturne "$@"
  fi
done
echo "The Codex needs Python 3.9 or newer: https://www.python.org/downloads/" >&2
exit 1
