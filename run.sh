#!/usr/bin/env bash
# One command: build the database from data/, run every test, then show the CEO's default view.
# No dependencies beyond Python 3.9+ (standard library only).
set -euo pipefail
cd "$(dirname "$0")"
python3 -m cockpit build
python3 -m unittest discover -s tests -v 2>&1 | tail -n 25
echo
python3 -m cockpit brief
