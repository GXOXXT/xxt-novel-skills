#!/usr/bin/env python3
"""
Tiny persistence layer for XXT Novel Skills.
Stores everything as JSON in .claude/novel-data/
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / "novel-data"
DATA_DIR.mkdir(exist_ok=True)

FILES = {
    "voice-contract": "voice_contract.json",
    "character-profiles": "character_profiles.json",
    "scene-maps": "scene_maps.json",
    "voice-lock": "voice_lock.json",
    "emotion-lexicon": "emotion_lexicon.json",
    "feedback-log": "feedback_log.json",
    "emotion-ledger": "emotion_ledger.json",
}

def load(name):
    path = DATA_DIR / FILES[name]
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

def save(name, data):
    path = DATA_DIR / FILES[name]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def get(key, subkey=None):
    data = load(key)
    if subkey:
        return data.get(subkey)
    return data

def set(key, subkey, value):
    data = load(key)
    data[subkey] = value
    data["_updated"] = datetime.now().isoformat()
    save(key, data)

def append(key, item):
    data = load(key)
    if not isinstance(data.get("entries"), list):
        data["entries"] = []
    item["_timestamp"] = datetime.now().isoformat()
    data["entries"].append(item)
    save(key, data)

def list_all(key):
    data = load(key)
    return data.get("entries", [])

# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python novel_db.py <command> [args...]")
        print("Commands: get, set, append, list")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "get":
        key = sys.argv[2]
        subkey = sys.argv[3] if len(sys.argv) > 3 else None
        result = get(key, subkey)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "set":
        key = sys.argv[2]
        subkey = sys.argv[3]
        value = json.loads(sys.argv[4]) if sys.argv[4].startswith("{") else sys.argv[4]
        set(key, subkey, value)
        print(f"Set {key}.{subkey}")

    elif cmd == "append":
        key = sys.argv[2]
        item = json.loads(sys.argv[3]) if sys.argv[3].startswith("{") else {"content": sys.argv[3]}
        append(key, item)
        print(f"Appended to {key}")

    elif cmd == "list":
        key = sys.argv[2]
        result = list_all(key)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}")