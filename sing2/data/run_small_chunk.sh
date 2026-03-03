#!/bin/bash
# Process smaller transcript chunks with Gemini
# Usage: bash run_small_chunk.sh <chunk_number> <chunk_size>

CHUNK=$1
CHUNK_SIZE=${2:-150}
RAW="data/sing2_script_raw.txt"
START=$((CHUNK * CHUNK_SIZE + 16))
END=$((START + CHUNK_SIZE - 1))

# Extract chunk
CHUNK_TEXT=$(sed -n "${START},${END}p" "$RAW")

if [ -z "$CHUNK_TEXT" ]; then
    echo "[]"
    exit 0
fi

PROMPT="Convert this Sing 2 (2021) subtitle text into individual dialogue entries.

RULES - READ CAREFULLY:
1. ONE entry per CHARACTER TURN. When a character says something, that is ONE entry.
2. Merge subtitle line-breaks that split a single sentence. Example: 'I can't tell\nif she's enjoying it' → 'I can't tell if she's enjoying it.'
3. Do NOT merge different characters' lines into one entry.
4. Do NOT merge lines from different conversations/moments.
5. Skip pure sound effects. But keep short dialogue like 'Oh!' or 'Wait!' or 'No!'
6. For songs: one entry per 4-6 lyric lines, labeled with singer name.
7. Identify the CHARACTER from context. Use full names: Buster Moon, not just Buster.

CHARACTERS: Buster Moon, Rosita, Gunter, Meena, Johnny, Ash, Miss Crawly, Nana Noodleman, Suki Lane, Jimmy Crystal, Porsha Crystal, Nooshy, Clay Calloway, Darius, Alfonso, Klaus, Jerry, Norman, Rick, Linda, Barry, Big Daddy

OUTPUT FORMAT: ONLY a JSON array. No markdown. Each element:
{\"scene\":\"...\",\"character\":\"...\",\"english\":\"...\",\"japanese\":\"...\",\"idioms\":[{\"expression\":\"...\",\"meaning\":\"...\",\"meaning_ja\":\"...\"}]}

Parse now:"

echo "$CHUNK_TEXT" | gemini "$PROMPT" --output-format text 2>&1
