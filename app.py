import html
import json
import math
from pathlib import Path

import streamlit as st


@st.cache_data(show_spinner=False)
def load_script_data():
    """Load script data from JSON file."""
    data_path = Path(__file__).parent / "data" / "scripts.json"
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


def scene_summary(scene_dialogues):
    """Build a short summary line shown above the script list."""
    if not scene_dialogues:
        return "No lines available for this script."

    speakers = sorted({item["character"] for item in scene_dialogues})
    speaker_preview = ", ".join(speakers[:2])
    if len(speakers) > 2:
        speaker_preview += ", and others"

    count = len(scene_dialogues)
    noun = "line" if count == 1 else "lines"
    return f"{speaker_preview}. {count} {noun} in this script. Tap any sentence to switch EN/JP."


def filter_dialogues(dialogues, search_query):
    if not search_query.strip():
        return dialogues

    query = search_query.lower().strip()
    return [
        item
        for item in dialogues
        if query in item["english"].lower() or query in item["japanese"]
    ]


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
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&family=Noto+Sans+JP:wght@400;500;700&display=swap');

        :root {
            --bg: #eef1f5;
            --ink-main: #1f2d43;
            --ink-soft: #5d6f87;
            --card: #ffffff;
            --card-border: #d6deea;
            --accent: #e5ad08;
            --accent-soft: #fff6d1;
        }

        .stApp {
            background: var(--bg);
            font-family: 'Manrope', 'Noto Sans JP', sans-serif;
            color: var(--ink-main);
        }

        [data-testid="stAppViewContainer"] {
            background: var(--bg);
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1000px;
            padding-top: 0.85rem;
            padding-bottom: 1rem;
        }

        .app-header {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 0.15rem;
        }

        .moon-badge {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: var(--accent);
            color: #ffffff;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.35rem;
            font-weight: 800;
            line-height: 1;
            box-shadow: 0 4px 10px rgba(182, 134, 0, 0.22);
        }

        .app-title {
            font-size: 1.8rem;
            line-height: 1.1;
            font-weight: 800;
            color: var(--ink-main);
            margin: 0;
        }

        .subtle-note {
            color: var(--ink-soft);
            font-size: 0.9rem;
            margin-bottom: 0.35rem;
        }

        .scene-intro {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-bottom: none;
            border-radius: 12px 12px 0 0;
            padding: 0.6rem 0.8rem;
            color: var(--ink-soft);
            font-size: 0.9rem;
            line-height: 1.35;
        }

        .scene-name {
            color: #324763;
            font-size: 0.98rem;
            font-weight: 700;
            margin-bottom: 0.08rem;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--card-border);
            border-radius: 0 0 12px 12px;
            background: var(--card);
            box-shadow: 0 6px 18px rgba(31, 45, 67, 0.08);
            padding: 0.38rem 0.7rem 0.6rem;
        }

        .line-row {
            padding: 0.32rem 0.08rem;
        }

        .avatar {
            width: 38px;
            height: 38px;
            border-radius: 999px;
            background: var(--accent-soft);
            border: 1px solid #ead26d;
            color: #9b6b00;
            font-size: 1rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 0.08rem;
        }

        .speaker-row {
            display: flex;
            align-items: center;
            gap: 0.32rem;
            margin-bottom: 0.08rem;
        }

        .speaker-name {
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.6px;
            color: #33445d;
            text-transform: uppercase;
        }

        .play-icon {
            width: 16px;
            height: 16px;
            border-radius: 999px;
            background: #95a3b9;
            color: #ffffff;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.47rem;
            padding-left: 2px;
        }

        .lang-chip {
            margin-left: 0.1rem;
            border-radius: 999px;
            border: 1px solid #cfd7e5;
            color: #5f7390;
            font-size: 0.61rem;
            font-weight: 700;
            padding: 0.03rem 0.32rem;
            background: #f8fafe;
        }

        .line-divider {
            border-bottom: 1px solid #edf2f8;
            margin-top: 0.14rem;
        }

        div[data-testid="stButton"] > button {
            width: 100%;
            border: none;
            background: transparent;
            color: var(--ink-main);
            text-align: left;
            font-size: 0.92rem;
            line-height: 1.35;
            font-weight: 500;
            padding: 0;
            margin: 0;
            font-family: 'Noto Sans JP', 'Manrope', sans-serif;
            white-space: normal;
        }

        div[data-testid="stButton"] > button:hover {
            color: #10223d;
            text-decoration: underline;
            text-decoration-color: rgba(16, 34, 61, 0.28);
            text-underline-offset: 0.18em;
            background: transparent;
        }

        div[data-testid="stButton"] > button:focus {
            outline: none;
            box-shadow: none;
            color: #10223d;
        }

        [data-testid="stSelectbox"] label,
        [data-testid="stTextInput"] label {
            color: #4a5f7c !important;
            font-weight: 600;
            font-size: 0.84rem !important;
        }

        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stTextInput"] input {
            background: #ffffff !important;
            border: 1px solid #ccd6e4 !important;
            border-radius: 8px !important;
            color: #1f2d43 !important;
            min-height: 2.15rem;
        }

        @media (max-width: 900px) {
            [data-testid="stMainBlockContainer"] {
                padding-top: 0.6rem;
            }

            .app-title {
                font-size: 1.5rem;
            }

            .moon-badge {
                width: 36px;
                height: 36px;
                font-size: 1.2rem;
            }

            .avatar {
                width: 34px;
                height: 34px;
                font-size: 0.95rem;
            }

            .speaker-name {
                font-size: 0.74rem;
            }

            div[data-testid="stButton"] > button {
                font-size: 0.88rem;
                line-height: 1.3;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_line(dialogue):
    is_japanese = get_line_language(dialogue["id"])
    has_japanese = bool(dialogue.get("japanese", "").strip())
    if is_japanese and has_japanese:
        language = "JP"
        line_text = dialogue["japanese"]
    elif is_japanese and not has_japanese:
        language = "EN"
        line_text = dialogue["english"]
    else:
        language = "EN"
        line_text = dialogue["english"]
    speaker = html.escape(dialogue["character"])

    avatar_col, content_col = st.columns([0.65, 9.35], gap="small")
    with avatar_col:
        st.markdown(
            f"<div class='avatar'>{html.escape(character_initial(dialogue['character']))}</div>",
            unsafe_allow_html=True,
        )
    with content_col:
        st.markdown(
            (
                "<div class='speaker-row'>"
                f"<span class='speaker-name'>{speaker}</span>"
                "<span class='play-icon'>&#9654;</span>"
                f"<span class='lang-chip'>{language}</span>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        if st.button(line_text, key=f"line_toggle_{dialogue['id']}", use_container_width=True):
            toggle_line_language(dialogue["id"])
            st.rerun()


def main():
    st.set_page_config(
        page_title="Moon Theater Script Reader",
        page_icon=":crescent_moon:",
        layout="wide",
    )

    apply_custom_style()
    data = load_script_data()
    all_dialogues = sorted(data["dialogues"], key=lambda item: item["id"])
    scenes = get_scenes_in_timeline(all_dialogues)
    script_options = ["All Scripts"] + scenes

    st.markdown(
        (
            "<div class='app-header'>"
            "<div class='moon-badge'>&#9789;</div>"
            "<h1 class='app-title'>Moon Theater</h1>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='subtle-note'>Tap any sentence to toggle that specific line between English and Japanese.</div>",
        unsafe_allow_html=True,
    )

    control_col_1, control_col_2 = st.columns([1.15, 1.85], gap="small")
    with control_col_1:
        selected_scene = st.selectbox("Script", script_options, index=0)
    with control_col_2:
        search_query = st.text_input(
            "Search in this script",
            placeholder="Search English or Japanese",
        )

    if selected_scene == "All Scripts":
        scene_dialogues = all_dialogues
        scene_title = "All Scripts"
        scene_blurb = (
            f"{len(scenes)} scripts, {len(all_dialogues)} lines total. "
            "Tap any sentence to switch EN/JP."
        )
    else:
        scene_dialogues = [item for item in all_dialogues if item["scene"] == selected_scene]
        scene_title = selected_scene
        scene_blurb = scene_summary(scene_dialogues)

    filtered_dialogues = filter_dialogues(scene_dialogues, search_query)

    filter_signature = (selected_scene, search_query.strip().lower(), len(filtered_dialogues))
    if st.session_state.get("filter_signature") != filter_signature:
        st.session_state["filter_signature"] = filter_signature
        st.session_state["page_num"] = 1

    st.markdown(
        (
            "<div class='scene-intro'>"
            f"<div class='scene-name'>{html.escape(scene_title)}</div>"
            f"{html.escape(scene_blurb)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    if not filtered_dialogues:
        st.info("No lines match your search in this script.")
        return

    pager_col_1, pager_col_2, pager_col_3 = st.columns([1, 1, 2], gap="small")
    with pager_col_1:
        page_size = st.selectbox("Lines / page", [40, 80, 120, 200], index=1, key="page_size")

    paged_dialogues, total_pages, start_idx, end_idx, safe_page = paginate_dialogues(
        filtered_dialogues,
        page_size,
        int(st.session_state.get("page_num", 1)),
    )

    with pager_col_2:
        page_num = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=safe_page,
            step=1,
            key="page_num",
        )

    with pager_col_3:
        st.caption(
            f"Showing lines {start_idx + 1}-{end_idx} of {len(filtered_dialogues)}"
        )

    # Keep page state clamped to current range after user edits page/filters.
    st.session_state["page_num"] = min(max(1, int(page_num)), total_pages)

    with st.container(height=760, border=True):
        for dialogue in paged_dialogues:
            st.markdown("<div class='line-row'>", unsafe_allow_html=True)
            render_line(dialogue)
            st.markdown("<div class='line-divider'></div></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
