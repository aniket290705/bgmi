import streamlit as st
import numpy as np
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt

st.set_page_config(page_title="3D Chess Game", layout="wide")

# ---------------------------
# MongoDB CONNECTION
# ---------------------------
@st.cache_resource
def get_db():
    try:
        client = MongoClient(st.secrets["mongo"]["uri"])
        db = client[st.secrets["mongo"]["db"]]
        return db
    except Exception as e:
        st.warning(f"⚠️ MongoDB connection error: {e}")
        return None

db = get_db()
games = db["games"] if db else None

# ---------------------------
# INITIAL BOARD SETUP
# ---------------------------
def create_board():
    board = np.array([
        ["r","n","b","q","k","b","n","r"],
        ["p","p","p","p","p","p","p","p"],
        [".",".",".",".",".",".",".","."],
        [".",".",".",".",".",".",".","."],
        [".",".",".",".",".",".",".","."],
        [".",".",".",".",".",".",".","."],
        ["P","P","P","P","P","P","P","P"],
        ["R","N","B","Q","K","B","N","R"]
    ])
    return board

if "board" not in st.session_state:
    st.session_state.board = create_board()
if "moves" not in st.session_state:
    st.session_state.moves = []

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def draw_board(board):
    fig, ax = plt.subplots(figsize=(6,6))
    ax.imshow(np.indices((8,8)).sum(axis=0) % 2, cmap="binary", vmin=0, vmax=1)

    for i in range(8):
        for j in range(8):
            piece = board[i, j]
            if piece != ".":
                ax.text(j, i, piece, ha="center", va="center", fontsize=18, color="red" if piece.islower() else "blue")

    ax.set_xticks(np.arange(8))
    ax.set_yticks(np.arange(8))
    ax.set_xticklabels(list("ABCDEFGH"))
    ax.set_yticklabels(list("87654321"))
    ax.invert_yaxis()
    st.pyplot(fig)

def move_piece(board, move):
    # move format: "e2 e4"
    try:
        from_sq, to_sq = move.split()
        cols = {"a":0,"b":1,"c":2,"d":3,"e":4,"f":5,"g":6,"h":7}
        fr = 8 - int(from_sq[1])
        fc = cols[from_sq[0].lower()]
        tr = 8 - int(to_sq[1])
        tc = cols[to_sq[0].lower()]

        piece = board[fr, fc]
        if piece == ".":
            return board, False

        board[fr, fc] = "."
        board[tr, tc] = piece
        return board, True
    except Exception:
        return board, False

# ---------------------------
# UI
# ---------------------------
st.title("♟️ Simplified 3D Chess (NumPy + Pandas + MongoDB)")

col1, col2 = st.columns([1, 1])

with col1:
    draw_board(st.session_state.board)
    move = st.text_input("Enter move (e.g., e2 e4):")
    if st.button("Make Move"):
        st.session_state.board, valid = move_piece(st.session_state.board, move)
        if valid:
            st.session_state.moves.append(move)
        else:
            st.error("Invalid move format or empty square!")

    if st.button("Reset Game"):
        st.session_state.board = create_board()
        st.session_state.moves = []

with col2:
    st.subheader("Game Moves History")
    df = pd.DataFrame({"Move #": range(1, len(st.session_state.moves)+1), "Move": st.session_state.moves})
    st.dataframe(df, use_container_width=True)

    if db:
        if st.button("💾 Save Game"):
            games.insert_one({"moves": st.session_state.moves})
            st.success("Game saved to MongoDB!")

        if st.button("📂 Load Last Game"):
            last = games.find_one(sort=[("_id", -1)])
            if last:
                st.session_state.moves = last["moves"]
                st.session_state.board = create_board()
                for mv in st.session_state.moves:
                    st.session_state.board, _ = move_piece(st.session_state.board, mv)
                st.success("Loaded last saved game!")
            else:
                st.warning("No previous games found.")

st.caption("Developed using Streamlit + NumPy + Pandas + MongoDB. No chess library used.")
