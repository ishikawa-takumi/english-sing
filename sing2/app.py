import html
import json
import math
import re
from pathlib import Path

import streamlit as st


@st.cache_data(show_spinner=False)
def load_script_data():
    """Load Sing 2 script data from JSON file."""
    data_path = Path(__file__).parent / "data" / "sing2_scripts.json"
    with open(data_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_scenes_in_timeline(dialogues):
    """Get unique scenes in first-appearance order (timeline order)."""
    ordered_scenes = []
    seen = set()
    for item in dialogues:
        scene = item["scene"]
        if scene not in seen:
            seen.add(scene)
            ordered_scenes.append(scene)
    return ordered_scenes


def line_state_key(dialogue_id):
    return f"line_show_japanese_{dialogue_id}"


def get_line_language(dialogue_id):
    """True means Japanese is shown, False means English is shown."""
    key = line_state_key(dialogue_id)
    if key not in st.session_state:
        st.session_state[key] = False
    return st.session_state[key]


def toggle_line_language(dialogue_id):
    key = line_state_key(dialogue_id)
    st.session_state[key] = not st.session_state.get(key, False)


def character_initial(character_name):
    """Get one avatar initial from the character name."""
    cleaned = character_name.strip()
    if not cleaned:
        return "?"
    for token in cleaned.split():
        if token and token[0].isalnum():
            return token[0].upper()
    return cleaned[0].upper()


# Character-specific avatar colors for visual distinction
CHARACTER_COLORS = {
    "Buster Moon": ("#6C5CE7", "#DCD6F7"),
    "Johnny": ("#00B894", "#D5F5E3"),
    "Ash": ("#E17055", "#FDEBD0"),
    "Meena": ("#0984E3", "#D6EAF8"),
    "Gunter": ("#FDCB6E", "#FEF9E7"),
    "Rosita": ("#E84393", "#FADBD8"),
    "Clay Calloway": ("#636E72", "#E5E7E9"),
    "Jimmy Crystal": ("#D63031", "#FADBD8"),
    "Porsha Crystal": ("#A29BFE", "#EDE7F6"),
    "Suki Lane": ("#00CEC9", "#D1F2EB"),
    "Nooshy": ("#FF7675", "#FDEBD0"),
    "Alfonso": ("#55EFC4", "#D5F5E3"),
    "Miss Crawly": ("#B2BEC3", "#F2F3F4"),
    "Klaus": ("#2D3436", "#E5E7E9"),
    "Klaus Kickenklober": ("#2D3436", "#E5E7E9"),
    "Nana Noodleman": ("#9B59B6", "#F5EEF8"),
    "Darius": ("#F39C12", "#FEF9E7"),
    "Jerry": ("#5DADE2", "#D6EAF8"),
    "Big Daddy": ("#784212", "#F5E6CC"),
    "Norman": ("#45B39D", "#D5F5E3"),
    "Linda": ("#C39BD3", "#F5EEF8"),
    "Linda Le Bon": ("#C39BD3", "#F5EEF8"),
    "Barry": ("#7F8C8D", "#E5E7E9"),
    "Rick": ("#E74C3C", "#FADBD8"),
}

DEFAULT_COLORS = ("#6C5CE7", "#DCD6F7")


def get_char_colors(character):
    return CHARACTER_COLORS.get(character, DEFAULT_COLORS)


def underline_idioms_in_text(text, idioms):
    """Highlight idiom expressions in the text with underline styling."""
    if not idioms:
        return html.escape(text)

    safe_text = html.escape(text)

    for idiom in idioms:
        expr = html.escape(idiom["expression"])
        pattern = re.compile(re.escape(expr), re.IGNORECASE)
        replacement = f'<span class="idiom-highlight">{expr}</span>'
        safe_text = pattern.sub(replacement, safe_text, count=1)

    return safe_text


def scene_summary(scene_dialogues):
    """Build a short summary line shown above the script list."""
    if not scene_dialogues:
        return "No lines available for this script."

    speakers = sorted({item["character"] for item in scene_dialogues})
    speaker_preview = ", ".join(speakers[:3])
    if len(speakers) > 3:
        speaker_preview += f", +{len(speakers) - 3} more"

    count = len(scene_dialogues)
    idiom_lines = sum(1 for d in scene_dialogues if d.get("idioms"))
    noun = "line" if count == 1 else "lines"
    return f"{speaker_preview} — {count} {noun}, {idiom_lines} with idioms. Tap any sentence to switch EN/JP."


def filter_dialogues(dialogues, search_query, idioms_only):
    result = dialogues
    if idioms_only:
        result = [item for item in result if item.get("idioms")]
    if search_query.strip():
        query = search_query.lower().strip()
        result = [
            item
            for item in result
            if query in item["english"].lower()
            or query in item["japanese"]
            or any(
                query in idiom["expression"].lower()
                or query in idiom["meaning"].lower()
                or query in idiom.get("meaning_ja", "")
                for idiom in item.get("idioms", [])
            )
        ]
    return result


def paginate_dialogues(dialogues, page_size, page):
    """Return one page of dialogues and paging metadata."""
    total = len(dialogues)
    if total == 0:
        return [], 1, 0, 0, 1
    total_pages = max(1, math.ceil(total / page_size))
    safe_page = min(max(1, page), total_pages)
    start_idx = (safe_page - 1) * page_size
    end_idx = min(start_idx + page_size, total)
    return dialogues[start_idx:end_idx], total_pages, start_idx, end_idx, safe_page


def apply_custom_style():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+JP:wght@400;500;600;700&display=swap');

        :root {
            --bg: #0f0e17;
            --bg-card: #1a1932;
            --bg-card-hover: #222046;
            --ink-main: #fffffe;
            --ink-soft: #a7a9be;
            --ink-muted: #72738c;
            --accent: #ff6e6c;
            --accent-2: #7f5af0;
            --accent-3: #2cb67d;
            --accent-soft: rgba(127, 90, 240, 0.15);
            --border: rgba(167, 169, 190, 0.12);
            --idiom-bg: rgba(255, 110, 108, 0.08);
            --idiom-border: rgba(255, 110, 108, 0.25);
        }

        .stApp {
            background: var(--bg);
            font-family: 'Inter', 'Noto Sans JP', sans-serif;
            color: var(--ink-main);
        }

        [data-testid="stAppViewContainer"] {
            background: var(--bg);
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 960px;
            padding-top: 0.8rem;
            padding-bottom: 1rem;
        }

        .app-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.15rem;
        }

        .logo-badge {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
            color: #ffffff;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.35rem;
            font-weight: 900;
            line-height: 1;
            box-shadow: 0 4px 16px rgba(127, 90, 240, 0.35);
        }

        .app-title {
            font-size: 1.75rem;
            line-height: 1.1;
            font-weight: 900;
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
        }

        .app-subtitle {
            font-size: 0.85rem;
            color: var(--ink-soft);
            margin-bottom: 0.4rem;
        }

        .scene-intro {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-bottom: none;
            border-radius: 14px 14px 0 0;
            padding: 0.65rem 0.85rem;
            color: var(--ink-soft);
            font-size: 0.88rem;
            line-height: 1.35;
        }

        .scene-name {
            color: var(--ink-main);
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.06rem;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--border);
            border-radius: 0 0 14px 14px;
            background: var(--bg-card);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
            padding: 0.4rem 0.7rem 0.65rem;
        }

        .line-row {
            padding: 0.35rem 0;
        }

        .avatar {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.95rem;
            font-weight: 800;
            margin-top: 0.06rem;
        }

        .speaker-row {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            margin-bottom: 0.06rem;
        }

        .speaker-name {
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }

        .lang-chip {
            border-radius: 999px;
            font-size: 0.58rem;
            font-weight: 700;
            padding: 0.04rem 0.32rem;
        }

        .lang-chip.en {
            background: rgba(127, 90, 240, 0.18);
            color: #a78bfa;
            border: 1px solid rgba(127, 90, 240, 0.3);
        }

        .lang-chip.jp {
            background: rgba(44, 182, 125, 0.18);
            color: #6ee7b7;
            border: 1px solid rgba(44, 182, 125, 0.3);
        }

        .idiom-count-badge {
            display: inline-block;
            border-radius: 999px;
            background: var(--idiom-bg);
            border: 1px solid var(--idiom-border);
            color: var(--accent);
            font-size: 0.62rem;
            font-weight: 700;
            padding: 0.02rem 0.38rem;
            margin-left: 0.2rem;
        }

        .idiom-highlight {
            text-decoration: underline;
            text-decoration-color: var(--accent);
            text-underline-offset: 0.18em;
            text-decoration-thickness: 2px;
            cursor: help;
        }

        .idiom-card {
            background: var(--idiom-bg);
            border: 1px solid var(--idiom-border);
            border-radius: 10px;
            padding: 0.55rem 0.7rem;
            margin: 0.25rem 0 0.15rem;
        }

        .idiom-expression {
            font-weight: 700;
            color: var(--accent);
            font-size: 0.88rem;
            margin-bottom: 0.2rem;
        }

        .idiom-meaning {
            color: var(--ink-soft);
            font-size: 0.82rem;
            line-height: 1.4;
        }

        .idiom-meaning-ja {
            color: var(--ink-muted);
            font-size: 0.8rem;
            line-height: 1.4;
            margin-top: 0.12rem;
        }

        .line-divider {
            border-bottom: 1px solid var(--border);
            margin-top: 0.15rem;
        }

        div[data-testid="stButton"] > button {
            width: 100%;
            border: none;
            background: transparent;
            color: var(--ink-main);
            text-align: left;
            font-size: 0.91rem;
            line-height: 1.4;
            font-weight: 500;
            padding: 0;
            margin: 0;
            font-family: 'Noto Sans JP', 'Inter', sans-serif;
            white-space: normal;
        }

        div[data-testid="stButton"] > button:hover {
            color: #ffffff;
            text-decoration: underline;
            text-decoration-color: rgba(255, 255, 255, 0.3);
            text-underline-offset: 0.18em;
            background: transparent;
        }

        div[data-testid="stButton"] > button:focus {
            outline: none;
            box-shadow: none;
            color: #ffffff;
        }

        [data-testid="stSelectbox"] label,
        [data-testid="stTextInput"] label,
        [data-testid="stCheckbox"] label {
            color: var(--ink-soft) !important;
            font-weight: 600;
            font-size: 0.82rem !important;
        }

        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stTextInput"] input {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
            color: var(--ink-main) !important;
            min-height: 2.15rem;
        }

        /* Expander styling for idioms */
        [data-testid="stExpander"] {
            background: transparent;
            border: none;
        }

        [data-testid="stExpander"] details {
            background: transparent;
            border: 1px solid var(--idiom-border);
            border-radius: 10px;
        }

        [data-testid="stExpander"] summary {
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 600;
        }

        /* Stats bar */
        .stats-bar {
            display: flex;
            gap: 1.2rem;
            margin: 0.3rem 0 0.5rem;
            flex-wrap: wrap;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }

        .stat-number {
            font-size: 1.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .stat-label {
            font-size: 0.72rem;
            color: var(--ink-muted);
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        @media (max-width: 900px) {
            [data-testid="stMainBlockContainer"] {
                padding-top: 0.5rem;
            }
            .app-title {
                font-size: 1.4rem;
            }
            .logo-badge {
                width: 38px;
                height: 38px;
                font-size: 1.15rem;
            }
            .avatar {
                width: 34px;
                height: 34px;
                font-size: 0.88rem;
            }
            .speaker-name {
                font-size: 0.7rem;
            }
            div[data-testid="stButton"] > button {
                font-size: 0.86rem;
            }
            .stats-bar {
                gap: 0.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_idioms(idioms):
    """Render idiom cards for a dialogue line."""
    if not idioms:
        return

    for idiom in idioms:
        expr = html.escape(idiom["expression"])
        meaning = html.escape(idiom["meaning"])
        meaning_ja = html.escape(idiom.get("meaning_ja", ""))

        ja_html = ""
        if meaning_ja:
            ja_html = f"<div class='idiom-meaning-ja'>{meaning_ja}</div>"

        st.markdown(
            f"""<div class='idiom-card'>
                <div class='idiom-expression'>{expr}</div>
                <div class='idiom-meaning'>{meaning}</div>
                {ja_html}
            </div>""",
            unsafe_allow_html=True,
        )


def render_line(dialogue):
    is_japanese = get_line_language(dialogue["id"])
    has_japanese = bool(dialogue.get("japanese", "").strip())
    idioms = dialogue.get("idioms", [])

    if is_japanese and has_japanese:
        language = "JP"
        line_text = dialogue["japanese"]
        lang_class = "jp"
    else:
        language = "EN"
        line_text = dialogue["english"]
        lang_class = "en"

    speaker = dialogue["character"]
    fg, bg = get_char_colors(speaker)

    avatar_col, content_col = st.columns([0.6, 9.4], gap="small")
    with avatar_col:
        st.markdown(
            f"<div class='avatar' style='background:{bg};color:{fg};'>"
            f"{html.escape(character_initial(speaker))}</div>",
            unsafe_allow_html=True,
        )
    with content_col:
        idiom_badge = ""
        if idioms:
            n = len(idioms)
            word = "idiom" if n == 1 else "idioms"
            idiom_badge = f"<span class='idiom-count-badge'>{n} {word}</span>"

        st.markdown(
            f"<div class='speaker-row'>"
            f"<span class='speaker-name' style='color:{fg};'>{html.escape(speaker)}</span>"
            f"<span class='lang-chip {lang_class}'>{language}</span>"
            f"{idiom_badge}"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Show text with underlined idioms (EN mode) or plain Japanese
        if language == "EN" and idioms:
            highlighted = underline_idioms_in_text(dialogue["english"], idioms)
            st.markdown(
                f"<div style='font-size:0.91rem;line-height:1.4;font-weight:500;"
                f"font-family:Inter,Noto Sans JP,sans-serif;margin-bottom:0.1rem;'>"
                f"{highlighted}</div>",
                unsafe_allow_html=True,
            )
            # Toggle button (smaller, just for switching)
            if st.button(
                "JP",
                key=f"toggle_{dialogue['id']}",
                help="Switch to Japanese",
            ):
                toggle_line_language(dialogue["id"])
                st.rerun()
        else:
            if st.button(
                line_text,
                key=f"line_toggle_{dialogue['id']}",
                use_container_width=True,
            ):
                toggle_line_language(dialogue["id"])
                st.rerun()

        # Expandable idiom section
        if idioms:
            with st.expander(f"View {len(idioms)} idiom{'s' if len(idioms) > 1 else ''}"):
                render_idioms(idioms)


def main():
    st.set_page_config(
        page_title="Sing 2 - Idiom Explorer",
        page_icon=":performing_arts:",
        layout="wide",
    )

    apply_custom_style()
    data = load_script_data()
    all_dialogues = sorted(data["dialogues"], key=lambda item: item["id"])
    scenes = get_scenes_in_timeline(all_dialogues)
    script_options = ["All Scenes"] + scenes

    # Count stats
    total_idioms = sum(len(d.get("idioms", [])) for d in all_dialogues)
    lines_with_idioms = sum(1 for d in all_dialogues if d.get("idioms"))

    # Header
    st.markdown(
        "<div class='app-header'>"
        "<div class='logo-badge'>S2</div>"
        "<h1 class='app-title'>Sing 2 Idiom Explorer</h1>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='app-subtitle'>"
        "Learn English idioms & expressions from Sing 2. "
        "Tap any line to toggle EN/JP. Idioms are <span class='idiom-highlight'>underlined</span>."
        "</div>",
        unsafe_allow_html=True,
    )

    # Stats bar
    st.markdown(
        f"<div class='stats-bar'>"
        f"<div class='stat-item'><span class='stat-number'>{len(all_dialogues)}</span>"
        f"<span class='stat-label'>Lines</span></div>"
        f"<div class='stat-item'><span class='stat-number'>{total_idioms}</span>"
        f"<span class='stat-label'>Idioms</span></div>"
        f"<div class='stat-item'><span class='stat-number'>{len(scenes)}</span>"
        f"<span class='stat-label'>Scenes</span></div>"
        f"<div class='stat-item'><span class='stat-number'>{lines_with_idioms}</span>"
        f"<span class='stat-label'>Lines with idioms</span></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Controls
    ctrl1, ctrl2, ctrl3 = st.columns([1.2, 1.8, 0.6], gap="small")
    with ctrl1:
        selected_scene = st.selectbox("Scene", script_options, index=0)
    with ctrl2:
        search_query = st.text_input(
            "Search",
            placeholder="Search lines, idioms, meanings...",
        )
    with ctrl3:
        idioms_only = st.checkbox("Idioms only", value=False)

    # Filter
    if selected_scene == "All Scenes":
        scene_dialogues = all_dialogues
        scene_title = "All Scenes"
        scene_blurb = (
            f"{len(scenes)} scenes, {len(all_dialogues)} lines, {total_idioms} idioms. "
            "Tap any sentence to switch EN/JP."
        )
    else:
        scene_dialogues = [
            item for item in all_dialogues if item["scene"] == selected_scene
        ]
        scene_title = selected_scene
        scene_blurb = scene_summary(scene_dialogues)

    filtered_dialogues = filter_dialogues(scene_dialogues, search_query, idioms_only)

    filter_signature = (
        selected_scene,
        search_query.strip().lower(),
        idioms_only,
        len(filtered_dialogues),
    )
    if st.session_state.get("filter_signature") != filter_signature:
        st.session_state["filter_signature"] = filter_signature
        st.session_state["page_num"] = 1

    st.markdown(
        f"<div class='scene-intro'>"
        f"<div class='scene-name'>{html.escape(scene_title)}</div>"
        f"{html.escape(scene_blurb)}"
        f"</div>",
        unsafe_allow_html=True,
    )

    if not filtered_dialogues:
        st.info("No lines match your search.")
        return

    # Pagination
    pager1, pager2, pager3 = st.columns([1, 1, 2], gap="small")
    with pager1:
        page_size = st.selectbox(
            "Lines / page", [20, 40, 80, 120], index=1, key="page_size"
        )
    paged_dialogues, total_pages, start_idx, end_idx, safe_page = paginate_dialogues(
        filtered_dialogues,
        page_size,
        int(st.session_state.get("page_num", 1)),
    )
    with pager2:
        st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=safe_page,
            step=1,
            key="page_num",
        )
    with pager3:
        st.caption(
            f"Showing lines {start_idx + 1}–{end_idx} of {len(filtered_dialogues)}"
        )

    # Render lines
    with st.container(height=780, border=True):
        for dialogue in paged_dialogues:
            st.markdown("<div class='line-row'>", unsafe_allow_html=True)
            render_line(dialogue)
            st.markdown(
                "<div class='line-divider'></div></div>", unsafe_allow_html=True
            )


if __name__ == "__main__":
    main()
