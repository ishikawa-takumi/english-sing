#!/usr/bin/env python3
"""Merge small Gemini-processed chunks into final sing2_scripts.json."""
import json
import re
import os

NUM_CHUNKS = 24

# Character name normalization
CHAR_MAP = {
    'Buster': 'Buster Moon', 'Mr. Moon': 'Buster Moon', 'Moon': 'Buster Moon',
    'Buster Moon': 'Buster Moon',
    'Miss Crawly': 'Miss Crawly', 'Crawly': 'Miss Crawly',
    'Nana': 'Nana Noodleman', 'Nana Noodleman': 'Nana Noodleman',
    'Suki': 'Suki Lane', 'Suki Lane': 'Suki Lane',
    'Mr. Crystal': 'Jimmy Crystal', 'Jimmy': 'Jimmy Crystal',
    'Jimmy Crystal': 'Jimmy Crystal', 'Crystal': 'Jimmy Crystal',
    'Porsha': 'Porsha Crystal', 'Porsha Crystal': 'Porsha Crystal',
    'Clay': 'Clay Calloway', 'Calloway': 'Clay Calloway',
    'Clay Calloway': 'Clay Calloway',
    'Big Daddy': 'Big Daddy', 'Norman': 'Norman',
}


def load_chunk(i):
    path = f'data/small_chunk_{i}.json'
    if not os.path.exists(path):
        print(f"  chunk {i}: MISSING")
        return []
    with open(path) as f:
        text = f.read()
    # Extract JSON array
    start = text.find('[')
    end = text.rfind(']')
    if start == -1 or end == -1:
        print(f"  chunk {i}: NO JSON")
        return []
    json_str = text[start:end+1]
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    try:
        data = json.loads(json_str)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        # Try truncation fix
        last = json_str.rfind('},')
        if last > 0:
            try:
                return json.loads(json_str[:last+1] + ']')
            except:
                pass
        print(f"  chunk {i}: PARSE ERROR")
        return []


def normalize_char(name):
    name = name.strip()
    if name in CHAR_MAP:
        return CHAR_MAP[name]
    # Title case
    titled = name.title()
    if titled in CHAR_MAP:
        return CHAR_MAP[titled]
    # Check if starts with known name
    for key, val in CHAR_MAP.items():
        if titled.startswith(key):
            return val
    return titled


def main():
    all_entries = []
    for i in range(NUM_CHUNKS):
        entries = load_chunk(i)
        print(f"  chunk {i}: {len(entries)} entries")
        all_entries.extend(entries)

    # Build final output
    dialogues = []
    for entry in all_entries:
        english = entry.get('english', '').strip()
        if not english:
            continue
        character = normalize_char(entry.get('character', 'Unknown'))
        japanese = entry.get('japanese', '').strip()
        scene = entry.get('scene', '')
        idioms = []
        for idiom in entry.get('idioms', []):
            if isinstance(idiom, dict) and 'expression' in idiom:
                idioms.append({
                    'expression': idiom.get('expression', ''),
                    'meaning': idiom.get('meaning', ''),
                    'meaning_ja': idiom.get('meaning_ja', ''),
                })
        dialogues.append({
            'id': len(dialogues) + 1,
            'scene': scene,
            'character': character,
            'english': english,
            'japanese': japanese,
            'idioms': idioms,
        })

    output = {'movie': 'Sing 2 (2021)', 'dialogues': dialogues}
    with open('data/sing2_scripts.json', 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Stats
    with_idioms = sum(1 for d in dialogues if d['idioms'])
    total_idioms = sum(len(d['idioms']) for d in dialogues)
    with_jp = sum(1 for d in dialogues if d['japanese'])
    chars = {}
    for d in dialogues:
        chars[d['character']] = chars.get(d['character'], 0) + 1
    scenes = {}
    for d in dialogues:
        scenes[d['scene']] = scenes.get(d['scene'], 0) + 1

    print(f"\n=== FINAL ===")
    print(f"Total entries: {len(dialogues)}")
    print(f"With idioms: {with_idioms} ({total_idioms} total)")
    print(f"With Japanese: {with_jp}")
    print(f"Characters: {len(chars)}")
    print(f"Scenes: {len(scenes)}")
    print(f"\nTop 15 characters:")
    for c, n in sorted(chars.items(), key=lambda x: -x[1])[:15]:
        print(f"  {c}: {n}")


if __name__ == '__main__':
    main()
