#!/usr/bin/env bash
# Wrapper for novel_db.py - makes it callable from skills
# Usage: novel.sh <command> [args...]

python "$(dirname "$0")/novel_db.py" "$@"