#!/usr/bin/env python3
"""
XXT Novel Rewriter App
Paste a chapter -> auto-audit -> rewrite -> save frameworks -> repeat
"""
import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# --- Persistence Layer ----------------------------------------------
DATA_DIR = Path(__file__).parent / ".claude" / "novel-data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "voice_contract": "voice_contract.json",
    "character_profiles": "character_profiles.json",
    "scene_maps": "scene_maps.json",
    "voice_lock": "voice_lock.json",
    "emotion_lexicon": "emotion_lexicon.json",
    "feedback_log": "feedback_log.json",
    "emotion_ledger": "emotion_ledger.json",
}

def load(name: str) -> dict:
    path = DATA_DIR / FILES[name]
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

def save(name: str, data: dict):
    path = DATA_DIR / FILES[name]
    data["_updated"] = datetime.now().isoformat()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def get(key: str, subkey: str = None) -> Any:
    data = load(key)
    return data.get(subkey) if subkey else data

def set_key(key: str, subkey: str, value: Any):
    data = load(key)
    data[subkey] = value
    save(key, data)

def append(key: str, item: dict):
    data = load(key)
    if not isinstance(data.get("entries"), list):
        data["entries"] = []
    item["_timestamp"] = datetime.now().isoformat()
    data["entries"].append(item)
    save(key, data)

# --- Framework Extraction (from pasted prose) -----------------------
CLICHE_PATTERNS = [
    r"a wave of \w+ washed over",
    r"heart (?:broke|pounded|raced|skipped)",
    r"she felt (?:nothing|everything|numb)",
    r"tears streamed down",
    r"a lump in (?:his|her|their) throat",
    r"blood ran cold",
    r"breath caught in (?:his|her|their) throat",
]

def detect_cliches(text: str) -> List[str]:
    found = []
    for pattern in CLICHE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found.extend(matches)
    return found

def extract_chapters(text: str) -> List[Dict]:
    """Split text into chapters by 'Chapter X' markers."""
    pattern = r'(?:^|\n)\s*(Chapter\s+\d+[:\s]*)'
    parts = re.split(pattern, text, flags=re.IGNORECASE)
    chapters = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = parts[i+1].strip() if i+1 < len(parts) else ""
        chapters.append({"title": title, "content": content})
    if not chapters:
        chapters = [{"title": "Chapter 1", "content": text.strip()}]
    return chapters

def analyze_voice_contract(chapters: List[Dict]) -> dict:
    """Extract voice patterns from prose samples."""
    all_text = " ".join(c["content"] for c in chapters)
    sentences = re.split(r'[.!?]+', all_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    avg_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    rhythm = "short" if avg_len < 12 else "flowing" if avg_len < 20 else "mixed"

    # Detect POV
    pov_markers = {"I ": "first", "he ": "third", "she ": "third", "they ": "third"}
    pov = "close third"
    for marker, p in pov_markers.items():
        if all_text.lower().count(marker) > 5:
            pov = p
            break

    # Detect imagery fields
    imagery = []
    fields = {
        "nature": ["sky", "tree", "wind", "rain", "sun", "cloud", "bird", "leaf"],
        "city": ["street", "building", "car", "traffic", "neon", "sidewalk", "window"],
        "body": ["hand", "heart", "breath", "blood", "skin", "eye", "finger", "chest"],
        "domestic": ["cup", "chair", "table", "door", "kitchen", "bed", "blanket", "lamp"],
        "machinery": ["engine", "gear", "wire", "screen", "button", "circuit", "motor"],
    }
    all_lower = all_text.lower()
    for field, keywords in fields.items():
        if any(k in all_lower for k in keywords):
            imagery.append(field)

    return {
        "genre": "Literary Fiction",
        "target_reader": "Adult literary fiction readers",
        "pov": pov,
        "tense": "past",
        "narrator_distance": "close",
        "diction": "plain but sharp",
        "sentence_rhythm": rhythm,
        "imagery_fields": imagery or ["body", "domestic"],
        "humor": "dry",
        "emotional_register": "restrained",
        "taboos": ["no cliché emotional phrases", "no 'wave of sadness'"],
        "repeated_motifs": [],
        "what_narrator_notices_first": "hands, mouths, rooms, weather, small objects",
        "what_narrator_never_says_directly": "characters rarely confess deepest feelings",
    }

def extract_characters(chapters: List[Dict]) -> List[str]:
    """Find character names (capitalized words that appear frequently)."""
    all_text = " ".join(c["content"] for c in chapters)
    words = re.findall(r'\b[A-Z][a-z]+\b', all_text)
    freq = {}
    for w in words:
        if w not in ["Chapter", "The", "He", "She", "They", "It", "We", "I", "You", "A", "An"]:
            freq[w] = freq.get(w, 0) + 1
    # Return top 5 most frequent as likely characters
    return sorted(freq, key=freq.get, reverse=True)[:5]

def build_character_profiles(characters: List[str]) -> dict:
    """Create default emotional profiles for detected characters."""
    profiles = {}
    for name in characters:
        profiles[name] = {
            "name": name,
            "core_want": "TBD",
            "core_fear": "TBD",
            "wound": "TBD",
            "lie_they_believe": "TBD",
            "truth_they_need": "TBD",
            "defense_mechanism": "TBD",
            "triggers": [],
            "when_angry": "TBD",
            "when_ashamed": "TBD",
            "when_grieving": "TBD",
            "when_afraid": "TBD",
            "when_happy": "TBD",
            "physical_tells": [],
            "voice_signature": "TBD",
            "what_they_hide": "TBD",
            "what_they_reveal": "TBD",
            "emotional_arc": "TBD",
        }
    return profiles

# --- Audit & Rewrite Engine ----------------------------------------
def audit_chapter(chapter: Dict, voice_contract: dict, profiles: dict) -> dict:
    """Run 7-point audit on a chapter."""
    content = chapter["content"]
    issues = []

    # 1. Voice match - check sentence rhythm
    sentences = re.split(r'[.!?]+', content)
    avg_len = sum(len(s.split()) for s in sentences if s.strip()) / max(len([s for s in sentences if s.strip()]), 1)
    expected = voice_contract.get("sentence_rhythm", "mixed")
    if expected == "short" and avg_len > 15:
        issues.append(f"Sentence rhythm too long (avg {avg_len:.1f} words) for 'short' voice")
    elif expected == "flowing" and avg_len < 10:
        issues.append(f"Sentence rhythm too short (avg {avg_len:.1f} words) for 'flowing' voice")

    # 2. Cliché check
    cliches = detect_cliches(content)
    if cliches:
        issues.append(f"Clichés found: {', '.join(cliches[:3])}")

    # 3. Emotion naming (basic heuristic)
    emotion_words = ["felt", "feeling", "emotion", "sadness", "anger", "fear", "joy", "grief", "shame", "guilt"]
    named = [w for w in emotion_words if w in content.lower()]
    if named:
        issues.append(f"Emotion labels used: {', '.join(set(named))} -- show don't tell")

    # 4. Character behavior consistency (placeholder - would need deeper NLP)
    for name in profiles:
        if name in content:
            # Check if character acts per profile
            pass

    # 5. Subtext check - dialogue with no subtext
    dialogue = re.findall(r'"[^"]*"', content)
    if dialogue:
        direct = [d for d in dialogue if any(e in d.lower() for e in ["i feel", "i am", "i'm feeling"])]
        if direct:
            issues.append(f"Direct emotional declarations in dialogue: {len(direct)} instances")

    # 6. Emotional entrance/exit
    first_para = content.strip().split("\n")[0] if content.strip() else ""
    last_para = content.strip().split("\n")[-1] if content.strip() else ""
    if not any(e in first_para.lower() for e in ["feel", "mood", "tension", "quiet", "heavy", "light", "dark", "bright"]):
        issues.append("No clear emotional entrance in opening paragraph")
    if not any(e in last_para.lower() for e in ["feel", "mood", "quiet", "still", "changed", "different", "realiz", "understand"]):
        issues.append("No clear emotional exit in closing paragraph")

    return {
        "chapter": chapter["title"],
        "issues": issues,
        "passed": len(issues) == 0,
        "word_count": len(content.split()),
    }

def create_scene_map(chapter: Dict, voice_contract: dict, profiles: dict) -> dict:
    """Create a Scene Emotion Map for the chapter."""
    content = chapter["content"]
    # Simple heuristics for entry/exit emotions
    entry_keywords = {"fear": ["trembl", "heart pound", "breath", "fear", "afraid", "nervous"],
                      "anger": ["anger", "furious", "rage", "mad", "fuming", "seethe"],
                      "grief": ["grief", "loss", "gone", "empty", "miss", "funeral", "death"],
                      "shame": ["shame", "embarrass", "humiliat", "foolish", "stupid"],
                      "hope": ["hope", "maybe", "possib", "chance", "light", "future"],
                      "longing": ["long", "wish", "yearn", "ache", "miss", "want"]}

    exit_keywords = {"resolution": ["understand", "realiz", "accept", "decid", "clear", "peace"],
                     "tension": ["wait", "uncertain", "tension", "heavy", "still", "quiet"],
                     "shift": ["but", "however", "sudden", "then", "now", "change"]}

    first_para = content.strip().split("\n")[0].lower() if content.strip() else ""
    last_para = content.strip().split("\n")[-1].lower() if content.strip() else ""

    entry_emotion = "neutral"
    for emo, kws in entry_keywords.items():
        if any(kw in first_para for kw in kws):
            entry_emotion = emo
            break

    exit_emotion = "neutral"
    for emo, kws in exit_keywords.items():
        if any(kw in last_para for kw in kws):
            exit_emotion = emo
            break

    # Find main character
    main_char = list(profiles.keys())[0] if profiles else "Protagonist"

    return {
        "chapter": chapter["title"],
        "scene_purpose": "TBD - analyze for plot function",
        "entry_emotion": entry_emotion,
        "exit_emotion": exit_emotion,
        "character_objective": f"{main_char} wants... (TBD)",
        "obstacle": "TBD",
        "pressure": "TBD",
        "what_is_said": "TBD",
        "what_is_not_said": "TBD",
        "emotional_turn": f"{entry_emotion} -> {exit_emotion}",
        "body_behavior_details": "TBD",
        "image_motif": voice_contract.get("imagery_fields", ["body"])[0],
        "pacing": "TBD",
        "ending_emotional_image": last_para[:200] + "..." if len(last_para) > 200 else last_para,
    }

def rewrite_chapter(chapter: Dict, voice_contract: dict, profiles: dict, audit: dict) -> str:
    """Rewrite chapter to fix audit issues. This is a template - in practice you'd use an LLM."""
    content = chapter["content"]

    # This is a placeholder - real implementation would call an LLM
    # For now, we return the original with notes
    notes = []
    if audit["issues"]:
        notes.append("=== REWRITE NOTES ===")
        for issue in audit["issues"]:
            notes.append(f"FIX: {issue}")
        notes.append("=== END NOTES ===\n")

    return "\n".join(notes) + content

# --- Main App ------------------------------------------------------
def process_batch(pasted_text: str) -> dict:
    """Main pipeline: paste chapters -> audit -> rewrite -> save."""
    print("\n[PROCESSING] Processing batch...")

    # 1. Split into chapters
    chapters = extract_chapters(pasted_text)
    print(f"[CHAPTERS] Found {len(chapters)} chapter(s)")

    # 2. Load or create frameworks
    voice_contract = get("voice_contract")
    profiles = get("character_profiles")

    if not voice_contract:
        print("[VOICE] No Voice Contract found -- extracting from prose...")
        voice_contract = analyze_voice_contract(chapters)
        set_key("voice_contract", "data", voice_contract)
        print("[OK] Voice Contract created")

    if not profiles:
        print("[CHARS] No Character Profiles found -- extracting characters...")
        chars = extract_characters(chapters)
        profiles = build_character_profiles(chars)
        set_key("character_profiles", "data", profiles)
        print(f"[OK] Character Profiles created for: {', '.join(chars)}")

    # 3. Process each chapter
    results = []
    for ch in chapters:
        print(f"\n[CHAPTER] Processing {ch['title']}...")

        # Audit
        audit = audit_chapter(ch, voice_contract, profiles)
        passed_str = "PASS" if audit['passed'] else f"ISSUES: {len(audit['issues'])}"
        print(f"   Audit: {passed_str}")
        for issue in audit["issues"]:
            print(f"   - {issue}")

        # Scene Map
        scene_map = create_scene_map(ch, voice_contract, profiles)
        append("scene_maps", scene_map)
        print(f"   [MAP] Scene Map saved")

        # Rewrite
        rewritten = rewrite_chapter(ch, voice_contract, profiles, audit)

        # Update Emotion Ledger
        main_char = list(profiles.keys())[0] if profiles else "Protagonist"
        entry = scene_map["entry_emotion"]
        exit_ = scene_map["exit_emotion"]
        append("emotion_ledger", {
            "chapter": ch["title"],
            "character": main_char,
            "entry": entry,
            "exit": exit_,
            "transition": f"{entry} -> {exit_}"
        })

        results.append({
            "chapter": ch["title"],
            "audit": audit,
            "scene_map": scene_map,
            "rewritten": rewritten,
            "word_count": audit["word_count"],
        })

    # 4. Summary
    total_words = sum(r["word_count"] for r in results)
    total_issues = sum(len(r["audit"]["issues"]) for r in results)

    print(f"\n{'='*50}")
    print(f"[OK] BATCH COMPLETE")
    print(f"   Chapters: {len(results)}")
    print(f"   Total words: {total_words:,}")
    print(f"   Total issues: {total_issues}")
    print(f"   Frameworks saved to .claude/novel-data/")
    print(f"{'='*50}\n")

    return {
        "chapters_processed": len(results),
        "total_words": total_words,
        "total_issues": total_issues,
        "results": results,
        "voice_contract": voice_contract,
        "profiles": profiles,
    }

def show_frameworks():
    """Display current frameworks."""
    vc = get("voice_contract")
    profiles = get("character_profiles")
    ledger = load("emotion_ledger").get("entries", [])

    print("\n" + "="*50)
    print("[FRAMEWORKS] CURRENT FRAMEWORKS")
    print("="*50)

    if vc:
        print("\n[VOICE] VOICE CONTRACT:")
        for k, v in vc.items():
            if k != "_updated":
                print(f"   {k}: {v}")
    else:
        print("\n[VOICE] VOICE CONTRACT: Not set")

    if profiles:
        print(f"\n[CHARS] CHARACTER PROFILES ({len(profiles)}):")
        for name, p in profiles.items():
            print(f"   {name}: want={p.get('core_want','TBD')}, fear={p.get('core_fear','TBD')}")
    else:
        print("\n[CHARS] CHARACTER PROFILES: Not set")

    if ledger:
        print(f"\n[LEDGER] EMOTION LEDGER ({len(ledger)} entries):")
        for e in ledger[-5:]:
            print(f"   {e.get('chapter','?')}: {e.get('character','?')} - {e.get('transition','?')}")
    else:
        print("\n[LEDGER] EMOTION LEDGER: Empty")

def interactive_mode():
    """Run interactive CLI."""
    print("""
+══════════════════════════════════════════════════════════+
║  XXT NOVEL REWRITER -- Paste chapters, get rewrites      ║
║  Commands:                                                ║
║    paste  -- Paste 2-3 chapters (end with '###END###')    ║
║    show   -- Show current frameworks                       ║
║    quit   -- Exit                                          ║
+══════════════════════════════════════════════════════════+
""")

    while True:
        cmd = input("\n> ").strip().lower()

        if cmd in ("quit", "exit", "q"):
            print("[BYE] Goodbye!")
            break

        elif cmd == "show":
            show_frameworks()

        elif cmd == "paste":
            print("Paste chapters (end with '###END###' on its own line):")
            lines = []
            while True:
                line = input()
                if line.strip() == "###END###":
                    break
                lines.append(line)

            text = "\n".join(lines)
            if text.strip():
                process_batch(text)
            else:
                print("❌ No content pasted")

        else:
            print("Commands: paste, show, quit")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Batch mode: python novel_app.py "chapter text here"
        # or: python novel_app.py @file.txt
        arg = sys.argv[1]
        if arg.startswith("@"):
            path = Path(arg[1:])
            if path.exists():
                text = path.read_text(encoding="utf-8")
            else:
                print(f"File not found: {path}")
                sys.exit(1)
        else:
            text = arg
        process_batch(text)
    else:
        interactive_mode()