#!/usr/bin/env python3
"""
Pre-process Sing 2 raw transcript: merge broken subtitle lines into complete
dialogue turns, identify speakers, detect songs vs dialogue.
Output: one JSON line per dialogue turn, ready for translation.
"""
import json
import re


def preprocess(filepath):
    with open(filepath) as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    entries = []
    current_speaker = None
    current_parts = []
    in_song = False
    current_song = None
    song_speaker = None
    song_parts = []
    line_idx = 0

    def is_stage_dir(s):
        return bool(re.match(r'^\([^"]*\)$', s))

    def is_trivial(s):
        """Skip very short non-content lines."""
        clean = re.sub(r'\([^)]*\)', '', s).strip()
        return len(clean) <= 2

    def clean_text(s):
        """Remove inline trivial stage directions."""
        s = re.sub(r'\((?:grunts?|sighs?|gasps?|screams?|yelps?|groans?|panting|whimpers?|sobs?|laughs?|chuckles?|giggles?|stammers?|clears throat|coughs?|sniffs?|straining|grunting|creaking|squeaking|breathing (?:sharply|heavily))\)', '', s)
        return re.sub(r'\s+', ' ', s).strip()

    def extract_speaker(s):
        """Extract SPEAKER: prefix. Returns (speaker, rest) or (None, s)."""
        m = re.match(r'^([A-Z][A-Z\s.\'\-]+?)(?:\s*\(.*?\))?\s*:\s*(.*)', s)
        if m and len(m.group(1).strip()) <= 25:
            return m.group(1).strip().title(), m.group(2).strip()
        return None, s

    def flush_dialogue():
        nonlocal current_speaker, current_parts
        if current_speaker and current_parts:
            text = ' '.join(current_parts)
            text = clean_text(text)
            text = re.sub(r'^\s*-\s*', '', text)
            if text and len(text) > 1:
                entries.append({
                    'speaker': current_speaker,
                    'text': text,
                    'type': 'dialogue',
                    'line': line_idx,
                })
        current_speaker = None
        current_parts = []

    def flush_song_section():
        nonlocal song_speaker, song_parts
        if song_speaker and song_parts:
            text = ' '.join(song_parts)
            text = clean_text(text)
            if text and len(text) > 3:
                entries.append({
                    'speaker': song_speaker,
                    'text': text,
                    'type': 'song',
                    'song': current_song,
                    'line': line_idx,
                })
        song_speaker = None
        song_parts = []

    i = 0
    while i < len(lines):
        raw = lines[i].strip()
        i += 1
        line_idx = i

        if not raw:
            continue

        # Skip Illumination intro
        if i <= 16 and ('Illumination' in raw or 'Minionese' in raw):
            continue

        # Song start detection
        song_match = re.match(r'^\("(.+?)"\s*(?:by .+?)?\s*playing', raw)
        if not song_match and raw.startswith('("') and i < len(lines):
            next_line = lines[i].strip() if i < len(lines) else ''
            if 'playing' in next_line:
                title_match = re.match(r'^\("(.+?)"', raw)
                if title_match:
                    song_match = title_match
                    i += 1

        if song_match:
            flush_dialogue()
            flush_song_section()
            in_song = True
            current_song = song_match.group(1)
            continue

        # Song end
        if raw in ('(song ends)', '(music stops)', '(music fades)'):
            flush_song_section()
            in_song = False
            current_song = None
            continue

        # Pure stage direction - skip (but handle scene transitions)
        if is_stage_dir(raw):
            continue

        # In song mode
        if in_song:
            speaker, rest = extract_speaker(raw)
            if speaker:
                flush_song_section()
                song_speaker = speaker
                if rest:
                    song_parts.append(rest)
                continue

            # Dash-prefixed song line with speaker
            if raw.startswith('- '):
                inner = raw[2:]
                sp, rest = extract_speaker(inner)
                if sp:
                    flush_song_section()
                    song_speaker = sp
                    if rest:
                        song_parts.append(rest)
                    continue
                inner_clean = re.sub(r'\([^)]*\)', '', inner).strip()
                if inner_clean:
                    if not song_speaker:
                        song_speaker = current_song or 'Song'
                    song_parts.append(inner_clean)
                continue

            clean = re.sub(r'\([^)]*\)', '', raw).strip()
            if clean:
                if not song_speaker:
                    song_speaker = current_song or 'Song'
                song_parts.append(clean)
            continue

        # === DIALOGUE MODE ===

        # Check for speaker prefix
        speaker, rest = extract_speaker(raw)
        if speaker:
            flush_dialogue()
            current_speaker = speaker
            if rest:
                current_parts.append(rest)
            continue

        # Check for "(style): text" like "(laughing): Well..."
        style_match = re.match(r'^\((\w+)\):\s*(.*)', raw)
        if style_match and style_match.group(2):
            # Keep current speaker, add text
            if current_speaker:
                current_parts.append(style_match.group(2))
            continue

        # Dash-prefixed lines - could be alternating speakers
        if raw.startswith('- '):
            inner = raw[2:]

            # Check for speaker prefix after dash
            sp, rest = extract_speaker(inner)
            if sp:
                flush_dialogue()
                current_speaker = sp
                if rest:
                    current_parts.append(rest)
                continue

            # Stage direction after dash
            if is_stage_dir(inner):
                continue

            # Dialogue continuation or interjection
            clean = re.sub(r'\([^)]*\)', '', inner).strip()
            if clean and not is_trivial(clean):
                # Heuristic: if current text ends with sentence-ending punctuation,
                # this dash line is a new turn (flush and start fresh)
                if current_parts:
                    joined = ' '.join(current_parts)
                    if joined.rstrip().endswith(('.', '!', '?', '"')):
                        flush_dialogue()
                        # Use previous speaker as fallback
                        if entries:
                            current_speaker = entries[-1]['speaker']
                        else:
                            current_speaker = 'Unknown'
                        current_parts = [clean]
                        continue
                if current_speaker:
                    current_parts.append(clean)
                continue
            continue

        # Regular continuation line
        clean = re.sub(r'^\([^)]*\)\s*', '', raw)  # Remove leading stage dir
        clean = re.sub(r'\s*\([^)]*\)$', '', clean)  # Remove trailing stage dir
        clean = clean.strip()

        if clean and not is_trivial(clean):
            if current_speaker:
                # Check if this starts a new sentence after completed text
                if current_parts:
                    joined = ' '.join(current_parts)
                    # If we have 3+ complete sentences, flush to keep entries granular
                    sentence_ends = len(re.findall(r'[.!?](?:\s|$)', joined))
                    if sentence_ends >= 3:
                        flush_dialogue()
                        if entries:
                            current_speaker = entries[-1]['speaker']
                        else:
                            current_speaker = 'Unknown'
                current_parts.append(clean)
            else:
                # No current speaker - use previous
                if entries:
                    current_speaker = entries[-1]['speaker']
                else:
                    current_speaker = 'Unknown'
                current_parts.append(clean)

    flush_dialogue()
    if in_song:
        flush_song_section()

    return entries


def main():
    entries = preprocess('data/sing2_script_raw.txt')

    dialogue = [e for e in entries if e['type'] == 'dialogue']
    songs = [e for e in entries if e['type'] == 'song']
    print(f"Total entries: {len(entries)}")
    print(f"  Dialogue: {len(dialogue)}")
    print(f"  Songs: {len(songs)}")

    # Character stats
    chars = {}
    for e in entries:
        c = e['speaker']
        chars[c] = chars.get(c, 0) + 1
    print(f"\nTop 15 characters:")
    for c, n in sorted(chars.items(), key=lambda x: -x[1])[:15]:
        print(f"  {c}: {n}")

    # Average length
    avg = sum(len(e['text']) for e in entries) / len(entries)
    print(f"\nAvg entry length: {avg:.0f} chars")

    # Save for Gemini processing
    with open('data/preprocessed.json', 'w') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to data/preprocessed.json")

    # Preview
    print("\n--- First 20 entries ---")
    for e in entries[:20]:
        t = e['text'][:70] + ('...' if len(e['text']) > 70 else '')
        print(f"  [{e['type'][0].upper()}] {e['speaker']:15s} | {t}")

    print("\n--- Middle entries ---")
    mid = len(entries) // 2
    for e in entries[mid:mid+10]:
        t = e['text'][:70] + ('...' if len(e['text']) > 70 else '')
        print(f"  [{e['type'][0].upper()}] {e['speaker']:15s} | {t}")


if __name__ == '__main__':
    main()
