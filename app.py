import html
import json
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


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
    # Pause background loading while the user is actively reviewing lines.
    st.session_state["auto_load_enabled"] = False


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

def render_scroll_resume_script():
    """Resume auto-loading when the user starts scrolling."""
    components.html(
        """
        <script>
        const parentWin = window.parent;
        const parentDoc = parentWin.document;

        function findResumeButton() {
          const buttons = Array.from(parentDoc.querySelectorAll("button"));
          return buttons.find((btn) => btn.innerText.trim() === "Resume auto-load");
        }

        function tryResumeFromScroll() {
          const btn = findResumeButton();
          if (!btn) return;
          if (btn.dataset.scrollResumeArmed !== "1") return;
          btn.dataset.scrollResumeArmed = "0";
          btn.click();
        }

        // Arm on each rerun while paused; first user scroll resumes auto-load.
        const btn = findResumeButton();
        if (btn) btn.dataset.scrollResumeArmed = "1";

        parentWin.addEventListener("scroll", tryResumeFromScroll, { passive: true });
        parentWin.addEventListener("wheel", tryResumeFromScroll, { passive: true });
        parentWin.addEventListener("touchmove", tryResumeFromScroll, { passive: true });
        </script>
        """,
        height=0,
    )


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

        .scene-break {
            border-top: 1px solid #dde6f3;
            margin: 0.24rem 0 0.38rem;
            padding-top: 0.35rem;
        }

        .scene-break-name {
            color: #496383;
            font-size: 0.73rem;
            font-weight: 700;
            letter-spacing: 0.45px;
            text-transform: uppercase;
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

        div[data-testid="stButton"] > button:focus-visible {
            outline: 2px solid #5f7390;
            outline-offset: 2px;
            border-radius: 6px;
            color: #10223d;
        }

        [data-testid="stSelectbox"] label,
        [data-testid="stTextInput"] label,
        [data-testid="stNumberInput"] label {
            color: #4a5f7c !important;
            font-weight: 600;
            font-size: 0.84rem !important;
        }

        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input {
            background: #ffffff !important;
            border: 1px solid #ccd6e4 !important;
            border-radius: 8px !important;
            color: #1f2d43 !important;
            min-height: 2.15rem;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus {
            border-color: #5f7390 !important;
            box-shadow: 0 0 0 2px rgba(95, 115, 144, 0.22) !important;
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
                f"<span class='lang-chip'>{language}</span>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        st.button(
            line_text,
            key=f"line_toggle_{dialogue['id']}",
            use_container_width=True,
            on_click=toggle_line_language,
            args=(dialogue["id"],),
        )


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
        (
            "<div class='subtle-note'>Tap any sentence to toggle EN/JP.</div>"
        ),
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
        st.session_state["visible_count"] = min(1, len(filtered_dialogues))
        st.session_state["auto_load_enabled"] = True

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

    visible_count = int(st.session_state.get("visible_count", min(1, len(filtered_dialogues))))
    visible_count = min(max(1, visible_count), len(filtered_dialogues))
    visible_dialogues = filtered_dialogues[:visible_count]
    should_rerun = False

    st.caption(f"Showing lines 1-{visible_count} of {len(filtered_dialogues)}")
    with st.container(height=760, border=True):
        previous_scene = None

        for dialogue in visible_dialogues:
            if selected_scene == "All Scripts" and dialogue["scene"] != previous_scene:
                st.markdown(
                    (
                        "<div class='scene-break'>"
                        f"<span class='scene-break-name'>{html.escape(dialogue['scene'])}</span>"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )
            previous_scene = dialogue["scene"]

            st.markdown("<div class='line-row'>", unsafe_allow_html=True)
            render_line(dialogue)
            st.markdown("<div class='line-divider'></div></div>", unsafe_allow_html=True)

    if visible_count < len(filtered_dialogues):
        auto_load_enabled = st.session_state.get("auto_load_enabled", True)
        if not auto_load_enabled:
            st.caption("Auto-load paused while you review lines.")
            render_scroll_resume_script()
            if st.button("Resume auto-load", use_container_width=True, key="resume_auto_load"):
                st.session_state["auto_load_enabled"] = True
                should_rerun = True
        else:
            st.caption("Loading more lines automatically...")
            time.sleep(0.03)
            st.session_state["visible_count"] = min(len(filtered_dialogues), visible_count + 1)
            should_rerun = True

    if should_rerun:
        st.rerun()


if __name__ == "__main__":
    main()
