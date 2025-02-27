import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Load CSV file (Replace with GitHub URL if needed)
def load_data():
    file_path = "game_list.csv"  # Change this
    try:
        df = pd.read_csv(file_path)
    except:
        st.warning("Failed to load CSV from GitHub. Please select a local file.")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
        else:
            st.stop()

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()

    # Mapping expected column names to actual names (handling typos or case issues)
    column_mapping = {
        "board game": "board game",
        "game length (minutes)": "game length",
        "number of players supported": "number of players supported",
        "date last played by group": "date last played by group"
    }
    df = df.rename(columns={col: column_mapping[col] for col in df.columns if col in column_mapping})

    # Ensure proper data types
    df["date last played by group"] = pd.to_datetime(df.get("date last played by group"), errors='coerce')
    df["date last played by group"].fillna(pd.Timestamp("2023-01-01"), inplace=True)
    df["game length"] = pd.to_numeric(df.get("game length"), errors='coerce')
    df["number of players supported"] = pd.to_numeric(df.get("number of players supported"), errors='coerce')

    return df

def weighted_random_choice(df):
    if df.empty:
        return "No games available after filtering."

    today = datetime.today()
    df["days since played"] = df["date last played by group"].apply(
        lambda x: (today - x).days if pd.notnull(x) else 9999  # Favor unplayed games
    )

    # Assign probability proportional to time since last played (longer = higher chance)
    df["weight"] = df["days since played"] ** 2  # Squaring increases weight difference

    # Normalize weights
    total_weight = df["weight"].sum()
    df["weight"] = df["weight"] / total_weight

    return np.random.choice(df["board game"], p=df["weight"])

# Streamlit UI
st.title("Board Game Picker")
df = load_data()

# Sidebar Filters
st.sidebar.header("Filters")

# Initialize filter states in session_state if they don't exist
if "excluded_games" not in st.session_state:
    st.session_state.excluded_games = []
if "min_length" not in st.session_state:
    st.session_state.min_length = int(df["game length"].min())
if "max_length" not in st.session_state:
    st.session_state.max_length = int(df["game length"].max())
if "players_min" not in st.session_state:
    st.session_state.players_min = int(df["number of players supported"].min())
if "players_max" not in st.session_state:
    st.session_state.players_max = int(df["number of players supported"].max())
if "date_cutoff" not in st.session_state:
    st.session_state.date_cutoff = datetime.today() - timedelta(days=30)

if st.sidebar.button("Reset Filters"):
    st.session_state.excluded_games = []
    st.session_state.min_length = int(df["game length"].min())
    st.session_state.max_length = int(df["game length"].max())
    st.session_state.players_min = int(df["number of players supported"].min())
    st.session_state.players_max = int(df["number of players supported"].max())
    st.session_state.date_cutoff = datetime.today() - timedelta(days=30)

excluded_games = st.sidebar.multiselect("Exclude Games:", df["board game"].unique(), default=st.session_state.excluded_games)
min_length, max_length = st.sidebar.slider("Game Length (minutes):", int(df["game length"].min()), int(df["game length"].max()), (st.session_state.min_length, st.session_state.max_length))
players = st.sidebar.slider("Number of Players:", int(df["number of players supported"].min()), int(df["number of players supported"].max()), (st.session_state.players_min, st.session_state.players_max))
date_cutoff = st.sidebar.date_input("Only show games not played since:", st.session_state.date_cutoff)

# Update session state with current filter values
st.session_state.excluded_games = excluded_games
st.session_state.min_length = min_length
st.session_state.max_length = max_length
st.session_state.players_min = players[0]
st.session_state.players_max = players[1]
st.session_state.date_cutoff = date_cutoff

# Filtering
filtered_df = df[(~df["board game"].isin(excluded_games)) &
                 (df["game length"] >= min_length) & (df["game length"] <= max_length) &
                 (df["number of players supported"] >= players[0]) & (df["number of players supported"] <= players[1]) &
                 ((df["date last played by group"].isna()) | (df["date last played by group"] <= pd.to_datetime(date_cutoff)))]

# Show filtered games
st.write("### Available Games After Filtering:")
st.markdown(
    """
    <style>
        .dataframe th {
            white-space: normal !important;
            word-wrap: break-word !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)
filtered_df_display = filtered_df[["board game", "game length", "number of players supported", "date last played by group"]].copy()
filtered_df_display["date last played by group"] = filtered_df_display["date last played by group"].dt.strftime('%Y-%m-%d')
st.dataframe(filtered_df_display)

# Button to pick a random game
if st.button("Pick a Game!"):
    selected_game = weighted_random_choice(filtered_df)
    st.success(f"🎲 Your game to play: **{selected_game}**!")
