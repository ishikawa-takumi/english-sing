import json
from pathlib import Path

import streamlit as st


def load_script_data():
    """Load script data from JSON file."""
    data_path = Path(__file__).parent / "data" / "scripts.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_unique_values(dialogues, key):
    """Get unique values for a given key from dialogues."""
    return sorted(set(d[key] for d in dialogues))


def apply_custom_style():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Noto+Sans+JP:wght@400;500;700&display=swap');

        :root {
            --bg-top: #0f172a;
            --bg-bottom: #111827;
            --panel: rgba(17, 24, 39, 0.75);
            --panel-border: rgba(56, 189, 248, 0.3);
            --text-main: #f8fafc;
            --text-soft: #cbd5e1;
            --accent: #22d3ee;
            --accent-strong: #f59e0b;
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 0%, rgba(245, 158, 11, 0.15), transparent 35%),
                radial-gradient(circle at 85% 12%, rgba(34, 211, 238, 0.16), transparent 40%),
                linear-gradient(180deg, var(--bg-top), var(--bg-bottom));
            color: var(--text-main);
            font-family: 'Space Grotesk', sans-serif;
        }

        [data-testid="stAppViewContainer"] {
            background: transparent;
        }

        h1, h2, h3 {
            font-family: 'Space Grotesk', sans-serif !important;
            letter-spacing: 0.2px;
        }

        .app-shell {
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            margin: 0.6rem 0 1rem 0;
            box-shadow: 0 14px 36px rgba(15, 23, 42, 0.35);
        }

        .section-title {
            font-weight: 700;
            color: var(--text-main);
            font-size: 1.02rem;
            margin-bottom: 0.15rem;
        }

        .section-note {
            color: var(--text-soft);
            font-size: 0.95rem;
        }

        .meta-row {
            color: #93c5fd;
            font-weight: 500;
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
        }

        .id-chip {
            display: inline-block;
            border: 1px solid rgba(245, 158, 11, 0.4);
            color: #fde68a;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.13rem 0.6rem;
            margin-right: 0.55rem;
        }

        .lang-chip {
            display: inline-block;
            border: 1px solid rgba(34, 211, 238, 0.45);
            color: #a5f3fc;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.1rem 0.5rem;
            margin-left: 0.2rem;
        }

        div[data-testid="stButton"] > button {
            width: 100%;
            text-align: left;
            border-radius: 14px;
            border: 1px solid rgba(148, 163, 184, 0.4);
            background: rgba(15, 23, 42, 0.82);
            color: var(--text-main);
            padding: 0.95rem 1rem;
            min-height: 3.2rem;
            line-height: 1.45;
            font-size: 1.02rem;
            font-family: 'Noto Sans JP', 'Space Grotesk', sans-serif;
        }

        div[data-testid="stButton"] > button:hover {
            border-color: rgba(34, 211, 238, 0.85);
            background: rgba(30, 41, 59, 0.95);
            color: #ffffff;
        }

        div[data-testid="stButton"] > button:focus {
            border-color: rgba(245, 158, 11, 0.95);
            box-shadow: 0 0 0 0.1rem rgba(245, 158, 11, 0.28);
        }

        [data-testid="stSelectbox"] label,
        [data-testid="stTextInput"] label {
            color: #dbeafe !important;
            font-weight: 600;
        }

        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stTextInput"] input {
            border-radius: 12px !important;
            border: 1px solid rgba(148, 163, 184, 0.45) !important;
            background: rgba(15, 23, 42, 0.75) !important;
            color: #f8fafc !important;
        }

        [data-testid="stCaptionContainer"] p,
        .stMarkdown p {
            color: var(--text-soft);
        }

        @media (max-width: 900px) {
            .app-shell {
                padding: 0.85rem;
                border-radius: 14px;
            }
            div[data-testid="stButton"] > button {
                font-size: 0.98rem;
                min-height: 2.9rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_line_language(dialogue_id):
    """Track whether a line is displayed in Japanese or English."""
    key = f"line_show_japanese_{dialogue_id}"
    if key not in st.session_state:
        st.session_state[key] = False
    return st.session_state[key]


def toggle_line_language(dialogue_id):
    key = f"line_show_japanese_{dialogue_id}"
    st.session_state[key] = not st.session_state[key]


def reset_line_language(dialogues):
    for dialogue in dialogues:
        st.session_state[f"line_show_japanese_{dialogue['id']}"] = False


def filter_dialogues(dialogues, selected_scene, selected_character, search_query):
    filtered = dialogues

    if selected_scene != "All Scenes":
        filtered = [d for d in filtered if d["scene"] == selected_scene]

    if selected_character != "All Characters":
        filtered = [d for d in filtered if d["character"] == selected_character]

    if search_query:
        search_lower = search_query.lower().strip()
        filtered = [
            d
            for d in filtered
            if search_lower in d["english"].lower() or search_lower in d["japanese"]
        ]

    return filtered


def render_dialogue_line(dialogue):
    is_japanese = get_line_language(dialogue["id"])
    lang_tag = "JP" if is_japanese else "EN"
    line_text = dialogue["japanese"] if is_japanese else dialogue["english"]

    st.markdown(
        f"""
        <div class="meta-row">
            <span class="id-chip">#{dialogue['id']}</span>
            {dialogue['scene']} · {dialogue['character']}
            <span class="lang-chip">{lang_tag}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(line_text, key=f"line_toggle_{dialogue['id']}", use_container_width=True):
        toggle_line_language(dialogue["id"])
        st.rerun()



def main():
    st.set_page_config(
        page_title="Sing Script Toggle Reader",
        page_icon="🎤",
        layout="wide",
    )

    apply_custom_style()

    data = load_script_data()
    dialogues = data["dialogues"]

    st.title("🎤 Sing Script Toggle Reader")
    st.caption("Tap a sentence to switch between English and Japanese for that line.")

    st.markdown('<div class="app-shell">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Filter Lines</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.6, 0.7])
    scenes = ["All Scenes"] + get_unique_values(dialogues, "scene")
    characters = ["All Characters"] + get_unique_values(dialogues, "character")

    with col1:
        selected_scene = st.selectbox("Scene", scenes)
    with col2:
        selected_character = st.selectbox("Character", characters)
    with col3:
        search_query = st.text_input("Search", placeholder="Type an English or Japanese keyword")
    with col4:
        st.write("")
        if st.button("Reset All", use_container_width=True):
            reset_line_language(dialogues)
            st.rerun()

    filtered_dialogues = filter_dialogues(
        dialogues,
        selected_scene,
        selected_character,
        search_query,
    )

    st.markdown(
        f'<div class="section-note">Showing {len(filtered_dialogues)} of {len(dialogues)} lines</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if not filtered_dialogues:
        st.info("No lines match your filters.")
        return

    st.markdown('<div class="app-shell">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">Script Lines</div><div class="section-note">Each tap toggles only that sentence.</div>',
        unsafe_allow_html=True,
    )

    for dialogue in filtered_dialogues:
        render_dialogue_line(dialogue)

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
