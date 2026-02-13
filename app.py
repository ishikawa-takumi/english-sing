import streamlit as st
import json
from pathlib import Path


def load_script_data():
    """Load script data from JSON file."""
    data_path = Path(__file__).parent / "data" / "scripts.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_unique_values(dialogues, key):
    """Get unique values for a given key from dialogues."""
    return sorted(set(d[key] for d in dialogues))


def main():
    st.set_page_config(
        page_title="Sing Script Checker",
        page_icon="🎤",
        layout="wide"
    )

    # Custom CSS for better list view styling
    st.markdown("""
        <style>
        .dialogue-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #1f77b4;
        }
        .character-name {
            color: #1f77b4;
            font-weight: bold;
            font-size: 1.1em;
        }
        .scene-name {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 8px;
        }
        .english-text {
            font-size: 1.1em;
            color: #333;
            margin: 10px 0;
        }
        .japanese-text {
            font-size: 1em;
            color: #555;
            background-color: #e8f4f8;
            padding: 8px;
            border-radius: 5px;
            margin-top: 8px;
        }
        .stSelectbox > div > div {
            background-color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("🎤 Sing Movie Script Checker")
    st.markdown("Learn English with dialogues from the movie **Sing (2016)**")
    st.divider()

    # Load data
    data = load_script_data()
    dialogues = data["dialogues"]

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Scene filter
    scenes = ["All Scenes"] + get_unique_values(dialogues, "scene")
    selected_scene = st.sidebar.selectbox("Select Scene", scenes)

    # Character filter
    characters = ["All Characters"] + get_unique_values(dialogues, "character")
    selected_character = st.sidebar.selectbox("Select Character", characters)

    # Japanese translation toggle
    st.sidebar.divider()
    st.sidebar.header("🌐 Translation")
    show_japanese = st.sidebar.toggle("Show Japanese Translation", value=True)

    # Search functionality
    st.sidebar.divider()
    st.sidebar.header("🔎 Search")
    search_query = st.sidebar.text_input("Search in scripts", placeholder="Enter keyword...")

    # Filter dialogues
    filtered_dialogues = dialogues

    if selected_scene != "All Scenes":
        filtered_dialogues = [d for d in filtered_dialogues if d["scene"] == selected_scene]

    if selected_character != "All Characters":
        filtered_dialogues = [d for d in filtered_dialogues if d["character"] == selected_character]

    if search_query:
        search_lower = search_query.lower()
        filtered_dialogues = [
            d for d in filtered_dialogues
            if search_lower in d["english"].lower() or search_lower in d["japanese"]
        ]

    # Display count
    st.markdown(f"**Showing {len(filtered_dialogues)} of {len(dialogues)} dialogues**")
    st.divider()

    # Display dialogues in list view
    if not filtered_dialogues:
        st.info("No dialogues found matching your filters.")
    else:
        for dialogue in filtered_dialogues:
            with st.container():
                col1, col2 = st.columns([1, 10])

                with col1:
                    st.markdown(f"**#{dialogue['id']}**")

                with col2:
                    # Scene and Character info
                    st.markdown(f"📍 **{dialogue['scene']}**")
                    st.markdown(f"👤 *{dialogue['character']}*")

                    # English text
                    st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 12px; border-radius: 8px; margin: 8px 0;">
                        <strong>🇬🇧 English:</strong><br>
                        <span style="font-size: 1.1em;">{dialogue['english']}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Japanese text (with toggle)
                    if show_japanese:
                        st.markdown(f"""
                        <div style="background-color: #e8f4f8; padding: 12px; border-radius: 8px; margin: 8px 0;">
                            <strong>🇯🇵 Japanese:</strong><br>
                            <span style="font-size: 1em;">{dialogue['japanese']}</span>
                        </div>
                        """, unsafe_allow_html=True)

                st.divider()

    # Footer
    st.sidebar.divider()
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Sing Script Checker** v1.0")
    st.sidebar.markdown("Learn English with movie dialogues!")


if __name__ == "__main__":
    main()
