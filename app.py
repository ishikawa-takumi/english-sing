import html
import json
import re
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
    st.session_state["active_line_id"] = dialogue_id
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


@st.cache_data(show_spinner=False)
def build_pronunciation_points(english_line):
    """Infer likely connected-speech points from an English line."""
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", english_line)
    lowered = [w.lower() for w in words]
    points = []
    seen = set()

    weak_form_notes = {
        "to": "弱形 /tə/ になりやすい（特に速い会話）。",
        "for": "弱形 /fər/ で短く聞こえやすい。",
        "and": "/ænd/ から /ən/・/n/ に縮約されやすい。",
        "of": "/əv/ または /ə/ まで弱化されることがある。",
        "can": "肯定文では /kən/ に弱化しやすい（否定の can't と対比）。",
        "have": "補助動詞としては /həv/ -> /əv/ に弱化されやすい。",
        "has": "弱形 /həz/ -> /əz/ になることがある。",
        "had": "弱形 /həd/ -> /əd/ になることがある。",
        "him": "語中では /h/ が落ちて /ɪm/ に寄ることがある。",
        "her": "語中では /h/ が落ちて /ər/ に寄ることがある。",
        "them": "弱形 /ðəm/ -> /ðm/ のように短くなることがある。",
        "your": "速い会話で /jər/ へ弱化しやすい。",
        "are": "無強勢では /ər/ と短く聞こえることが多い。",
    }
    vowels = set("aeiou")

    def add_point(kind, pattern, note):
        normalized = (kind, pattern.lower())
        if normalized in seen:
            return
        seen.add(normalized)
        points.append({"kind": kind, "pattern": pattern, "note": note})

    for token in lowered:
        if token in weak_form_notes:
            add_point("Weak Form", token, weak_form_notes[token])

    for left, right in zip(lowered, lowered[1:]):
        if left.endswith("r") and right and right[0] in vowels:
            add_point(
                "R-Linking",
                f"{left} {right}",
                "語末の /r/ が次語の母音と連結して聞こえやすい。",
            )

        if left and right and left[-1].isalpha() and left[-1] not in vowels and right[0] in vowels:
            add_point(
                "Linking",
                f"{left} {right}",
                "前語の語末子音が次語の語頭母音に連結し、区切れが弱くなる。",
            )

        if left.endswith(("t", "d")) and right and right[0] in vowels:
            add_point(
                "Flap (AmE)",
                f"{left} {right}",
                "米語では /t,d/ が [ɾ] に近くなり、ラ行っぽく聞こえることがある。",
            )

        if left.endswith(("t", "d")) and right and right[0] not in vowels:
            add_point(
                "Elision",
                f"{left} {right}",
                "子音連続で /t,d/ が弱まる・落ちる（聞こえにくくなる）ことがある。",
            )

        if left.endswith("n") and right and right[0] in "pbm":
            add_point(
                "Assimilation",
                f"{left} {right}",
                "/n/ が後続音の影響で [m] に寄って聞こえることがある。",
            )

        if left in {"did", "would", "could", "should", "don't", "won't", "can't"} and right == "you":
            add_point(
                "Yod Coalescence",
                f"{left} {right}",
                "\"... you\" が /dʒ/ や /tʃ/ に寄って聞こえることがある（did you -> didja）。",
            )

        if right in {"him", "her", "his", "have", "has", "had"}:
            add_point(
                "H-Dropping",
                f"{left} {right}",
                "無強勢の機能語では語頭 /h/ が落ちることがある。",
            )

    if not points:
        points.append(
            {
                "kind": "Rhythm",
                "pattern": "stress timing",
                "note": "内容語を強く、機能語を短くすると自然な英語リズムに近づく。",
            }
        )

    return points[:8]


def parse_int_or_none(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def render_live_hover_panel(visible_dialogues, selected_dialogue_id):
    """Live hover preview panel rendered in a component iframe."""
    by_id = {}
    by_text = {}

    for dialogue in visible_dialogues:
        did = str(dialogue["id"])
        by_id[did] = {
            "id": dialogue["id"],
            "english": dialogue["english"],
            "japanese": dialogue.get("japanese", ""),
            "points": build_pronunciation_points(dialogue["english"]),
        }

        english_text = dialogue["english"].strip()
        japanese_text = dialogue.get("japanese", "").strip()
        if english_text:
            by_text.setdefault(english_text, did)
        if japanese_text:
            by_text.setdefault(japanese_text, did)

    if not by_id:
        return

    selected_id = str(selected_dialogue_id)
    if selected_id not in by_id:
        selected_id = next(iter(by_id.keys()))

    payload = json.dumps(
        {
            "by_id": by_id,
            "by_text": by_text,
            "selected_id": selected_id,
        },
        ensure_ascii=False,
    )

    components.html(
        f"""
        <div id="live-hover-root"></div>
        <style>
          .live-card {{
            border: 1px solid #d6deea;
            border-radius: 12px;
            background: #ffffff;
            padding: 0.64rem 0.66rem 0.48rem;
            box-shadow: 0 4px 12px rgba(31,45,67,0.08);
            font-family: Manrope, "Noto Sans JP", sans-serif;
          }}
          .live-head {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.4rem;
            margin-bottom: 0.26rem;
          }}
          .live-title {{
            color: #2b4060;
            font-size: 0.9rem;
            font-weight: 800;
          }}
          .live-mode {{
            border-radius: 999px;
            border: 1px solid #ccdbf2;
            background: #eef4ff;
            color: #48678f;
            font-size: 0.6rem;
            font-weight: 700;
            padding: 0.06rem 0.38rem;
          }}
          .live-en {{
            color: #1f2d43;
            font-size: 0.83rem;
            line-height: 1.3;
            font-weight: 600;
            margin-bottom: 0.2rem;
          }}
          .live-ja {{
            color: #586e8d;
            font-size: 0.75rem;
            line-height: 1.25;
            margin-bottom: 0.32rem;
          }}
          .live-item {{
            border: 1px solid #e3eaf6;
            border-radius: 9px;
            background: #fbfdff;
            padding: 0.36rem 0.42rem;
            margin-bottom: 0.28rem;
          }}
          .live-kind {{
            color: #355077;
            font-size: 0.63rem;
            font-weight: 800;
            letter-spacing: 0.38px;
            text-transform: uppercase;
            margin-bottom: 0.05rem;
          }}
          .live-pattern {{
            color: #2f4668;
            font-size: 0.68rem;
            font-weight: 700;
            margin-bottom: 0.05rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
          }}
          .live-note {{
            color: #4e6281;
            font-size: 0.71rem;
            line-height: 1.25;
          }}
        </style>
        <script>
          const payload = {payload};
          const byId = payload.by_id || {{}};
          const byText = payload.by_text || {{}};
          const selectedId = String(payload.selected_id || "");
          const root = document.getElementById("live-hover-root");

          function esc(s) {{
            return String(s || "")
              .replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/\\\"/g, "&quot;")
              .replace(/'/g, "&#39;");
          }}

          function renderPanel(item, modeLabel) {{
            if (!item) return;
            const points = (item.points || []).map((point) => `
              <div class="live-item">
                <div class="live-kind">${{esc(point.kind)}}</div>
                <div class="live-pattern">${{esc(point.pattern)}}</div>
                <div class="live-note">${{esc(point.note)}}</div>
              </div>
            `).join("");

            root.innerHTML = `
              <div class="live-card">
                <div class="live-head">
                  <span class="live-title">Live Hover Preview</span>
                  <span class="live-mode">${{modeLabel}}</span>
                </div>
                <div class="live-en">${{esc(item.english)}}</div>
                <div class="live-ja">${{esc(item.japanese || "")}}</div>
                ${{points}}
              </div>
            `;
          }}

          let lastRenderKey = "";

          function pollHoveredButton() {{
            const parentDoc = window.parent.document;
            const hoveredButtons = Array.from(parentDoc.querySelectorAll("button:hover"));
            const hovered = hoveredButtons.length ? hoveredButtons[hoveredButtons.length - 1] : null;
            const label = hovered ? hovered.innerText.trim() : "";
            const hoverId = byText[label] ? String(byText[label]) : "";

            const renderId = hoverId || selectedId;
            const mode = hoverId ? "Hover" : "Selected";
            const renderKey = `${{renderId}}:${{mode}}`;
            if (renderKey === lastRenderKey) return;
            lastRenderKey = renderKey;
            renderPanel(byId[renderId], mode);
          }}

          pollHoveredButton();
          setInterval(pollHoveredButton, 220);
        </script>
        """,
        height=420,
    )


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

        .point-chip {
            margin-left: 0.1rem;
            border-radius: 999px;
            border: 1px solid #d9e3f1;
            color: #577195;
            font-size: 0.61rem;
            font-weight: 700;
            padding: 0.03rem 0.34rem;
            background: #f4f8ff;
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

        .coach-panel {
            border: 1px solid var(--card-border);
            border-radius: 12px;
            background: var(--card);
            padding: 0.72rem 0.74rem 0.55rem;
            box-shadow: 0 6px 18px rgba(31, 45, 67, 0.08);
            position: sticky;
            top: 0.6rem;
        }

        .coach-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.28rem;
        }

        .coach-title {
            font-size: 0.95rem;
            font-weight: 800;
            color: #2b4060;
        }

        .coach-mode {
            border-radius: 999px;
            border: 1px solid #ccdbf2;
            background: #eef4ff;
            color: #48678f;
            font-size: 0.62rem;
            font-weight: 700;
            padding: 0.08rem 0.42rem;
            white-space: nowrap;
        }

        .coach-line-en {
            color: #1f2d43;
            font-size: 0.9rem;
            line-height: 1.36;
            font-weight: 600;
            margin-bottom: 0.24rem;
        }

        .coach-line-ja {
            color: #5a6f8d;
            font-size: 0.82rem;
            line-height: 1.34;
            margin-bottom: 0.45rem;
        }

        .coach-item {
            border: 1px solid #e2e9f4;
            border-radius: 10px;
            background: #fbfdff;
            padding: 0.47rem 0.52rem;
            margin-bottom: 0.38rem;
        }

        .coach-item-kind {
            color: #355077;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.45px;
            text-transform: uppercase;
            margin-bottom: 0.08rem;
        }

        .coach-item-pattern {
            color: #2f4668;
            font-size: 0.77rem;
            font-weight: 700;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
            margin-bottom: 0.08rem;
        }

        .coach-item-note {
            color: #4e6281;
            font-size: 0.8rem;
            line-height: 1.33;
        }

        .coach-hint {
            color: #607493;
            font-size: 0.75rem;
            line-height: 1.3;
            margin-top: 0.2rem;
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

            .coach-panel {
                position: static;
                margin-top: 0.46rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_pronunciation_panel(dialogue, preview_mode):
    points = build_pronunciation_points(dialogue["english"])
    mode_label = "Hover Preview" if preview_mode else "Selected"
    english_line = html.escape(dialogue["english"])
    japanese_line = html.escape(dialogue.get("japanese", ""))

    st.markdown(
        (
            "<div class='coach-panel'>"
            "<div class='coach-head'>"
            "<span class='coach-title'>Pronunciation Coach</span>"
            f"<span class='coach-mode'>{mode_label}</span>"
            "</div>"
            f"<div class='coach-line-en'>{english_line}</div>"
            f"<div class='coach-line-ja'>{japanese_line}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    for point in points:
        st.markdown(
            (
                "<div class='coach-item'>"
                f"<div class='coach-item-kind'>{html.escape(point['kind'])}</div>"
                f"<div class='coach-item-pattern'>{html.escape(point['pattern'])}</div>"
                f"<div class='coach-item-note'>{html.escape(point['note'])}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div class='coach-hint'>Tip: hover for quick preview, click to keep the explanation fixed.</div>",
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
    point_count = len(build_pronunciation_points(dialogue["english"]))

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
                f"<span class='point-chip'>P {point_count}</span>"
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
    return line_text


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
            "<div class='subtle-note'>Tap to toggle EN/JP. "
            "Hover for pronunciation preview, click to keep it fixed in the right panel.</div>"
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
        if filtered_dialogues:
            st.session_state["active_line_id"] = filtered_dialogues[0]["id"]

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
    selected_id = parse_int_or_none(st.session_state.get("active_line_id"))
    if selected_id is None or selected_id not in {item["id"] for item in filtered_dialogues}:
        selected_id = filtered_dialogues[0]["id"]
        st.session_state["active_line_id"] = selected_id

    dialogue_index = {item["id"]: item for item in all_dialogues}
    target_dialogue = dialogue_index.get(selected_id, filtered_dialogues[0])

    script_col, coach_col = st.columns([1.55, 1.0], gap="large")
    should_rerun = False

    with script_col:
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

    with coach_col:
        render_live_hover_panel(visible_dialogues, selected_dialogue_id=selected_id)
        render_pronunciation_panel(target_dialogue, preview_mode=False)

    if should_rerun:
        st.rerun()


if __name__ == "__main__":
    main()
