# app.py

import pandas as pd
from sources.sql import create_sql_engine, query_db, validate_username
from streamlit_extras.let_it_rain import rain
from streamlit_server_state import no_rerun, server_state, server_state_lock

import streamlit as st

sql_engine = create_sql_engine()
NUM_PLAYERS = 2


def display_user_settings() -> None:
    with st.form("ttt-settings-form"):
        teams = pd.DataFrame(
            query_db(
                sql_engine,
                "SELECT name, logo from teams WHERE team_id NOT IN (-2, -1, 31, 32, 38)",
            ),
        )
        if st.session_state.get("username", None):
            st.session_state["ttt-user"] = st.session_state["username"]
        else:
            ttt_username_input = st.text_input("Select your nickname")
            if ttt_username_input:
                if validate_username(ttt_username_input):
                    st.session_state["ttt-user"] = ttt_username_input
                else:
                    st.warning("Please use a different name!")

        team_name = st.selectbox(
            "Select your Team",
            options=teams["name"],
            index=None,
            placeholder="Select your favorite team",
        )
        if team_name:
            team_logo = teams.loc[teams["name"] == team_name, "logo"].to_numpy()[0]
        if st.form_submit_button("Join lobby"):
            if st.session_state.get("ttt-user") and team_logo:
                st.session_state["ttt-team"] = team_logo
                st.rerun()
            else:
                st.error("Provide User Name and Logo")


def create_id() -> str:
    """Generates a unique game ID."""
    if "ttt-last-id" not in server_state:
        server_state["ttt-last-id"] = 0
    server_state["ttt-last-id"] += 1
    return str(server_state["ttt-last-id"]).zfill(6)


def check_win(board: list[list[str]]) -> str | None:
    """Checks for a win on the given board."""
    # Check rows
    for row in board:
        if row[0] != "" and row[0] == row[1] == row[2]:
            return row[0]
    # Check columns
    for col in range(3):
        if board[0][col] != "" and board[0][col] == board[1][col] == board[2][col]:
            return board[0][col]
    # Check diagonals
    if board[0][0] != "" and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] != "" and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
    return None


def check_draw(board: list[list[str]]) -> bool:
    """Checks if the game is a draw."""
    return all("" not in row for row in board)


# --- Game Logic Functions ---


def create_new_game() -> None:
    """Handles the creation of a new game."""
    with no_rerun, server_state_lock["games_lock"]:
        # Generate a unique game ID and add it to the server state
        game_id = create_id()
        if "games" not in server_state:
            server_state.games = {}
        server_state.games[game_id] = {
            "board": [["" for _ in range(3)] for _ in range(3)],
            "players": {
                "X": {
                    "name": st.session_state["ttt-user"],
                    "logo": st.session_state["ttt-team"],
                },
            },
            "current_turn": "X",
            "next_turn": "O",
            "winner": None,
            "status": "waiting",
        }
        st.session_state.game_id = game_id
        st.session_state.my_symbol = "X"
    st.rerun()


def join_game(game_id: str) -> None:
    """Handles a player joining an existing game."""
    with server_state_lock["games_lock"]:
        # Check if the game exists and is waiting for a player
        if (
            game_id in server_state.games
            and server_state.games[game_id]["status"] == "waiting"
        ):
            # Add the second player to the game and start it
            server_state.games[game_id]["players"]["O"] = {
                "name": st.session_state["ttt-user"],
                "logo": st.session_state["ttt-team"],
            }
            server_state.games[game_id]["status"] = "playing"
            st.session_state.game_id = game_id
            st.session_state.my_symbol = "O"
        else:
            # Handle the case where the game is no longer available
            st.warning("Sorry, this game is no longer available.")
            return


def make_move(row: int, col: int) -> None:
    """Handles a player's move and updates the server state."""
    game_id = st.session_state.game_id
    my_symbol = st.session_state.my_symbol

    game = server_state.games[game_id]
    # Check if it's the player's turn and the cell is empty
    if (
        game["current_turn"] == my_symbol
        and game["board"][row][col] == ""
        and game["winner"] is None
    ):
        # Update the board
        game["board"][row][col] = my_symbol
        # Check for a win or draw
        winner = check_win(game["board"])
        if winner:
            game["winner"] = winner
        elif check_draw(game["board"]):
            game["winner"] = "Draw"
        else:
            # Switch turns
            game["current_turn"], game["next_turn"] = (
                game["next_turn"],
                game["current_turn"],
            )


def reset_game(game_id: str | None = None) -> None:
    """Resets the player's session state to return to the lobby."""
    with server_state_lock["games_lock"]:
        if (
            "game_id" in st.session_state
            and st.session_state.game_id in server_state.games
        ):
            del server_state.games[st.session_state.game_id]
        if game_id:
            del server_state.games[game_id]
    if "game_id" in st.session_state:
        del st.session_state.game_id
    if "my_symbol" in st.session_state:
        del st.session_state.my_symbol

    st.rerun()


@st.dialog("Confirm game deletion")
def confirm_deletion() -> None:
    st.write("""Are you sure you want to end the game and delete it?\n
Click 'Delete' to confirm deletion or close this dialog to keep on playing.""")
    if st.button("Delete"):
        reset_game()


def _display_winner_screen(winner: str) -> None:
    """Display results and celebration for the game outcome."""
    if winner == "Draw":
        st.info("It's a draw!")
    elif winner == st.session_state.my_symbol:
        st.success("You won!")
        rain(emoji="🎉", font_size=66, falling_speed=5, animation_length="5s")
    else:
        st.error("You lost!")
        rain(emoji="☠️", font_size=66, falling_speed=5, animation_length="5s")

    if st.button("Start New Game"):
        reset_game()


def _display_player_info(current_turn: str) -> None:
    """Displays player info and current turn."""
    col1, col2 = st.columns([1, 5])
    with col1:
        st.write("Your team:")
    with col2:
        st.button(
            " ",
            key=f"cell_{st.session_state.my_symbol}_player",
            width="stretch",
            disabled=True,
        )

    players = server_state.games[st.session_state.game_id]["players"]
    if len(players) != NUM_PLAYERS:
        st.warning("Waiting for opponent!")
        return

    # Opponent info
    opponent_symbol = "X" if st.session_state.my_symbol == "O" else "O"
    opponent_name = players[opponent_symbol]["name"]

    col1, col2 = st.columns([1, 5])
    with col1:
        st.write("Opponent:")
    with col2:
        st.write(opponent_name)

    # Current turn
    col1, col2 = st.columns([1, 5])
    with col1:
        st.write("Current turn:")
    with col2:
        st.button(
            " ",
            key=f"cell_{current_turn}_current",
            width="stretch",
            disabled=True,
        )


def _render_board(
    board: list[list[str]],
    winner: str | None,
    current_turn: str,
) -> None:
    """Render the game board and CSS styles."""
    _apply_board_styles()

    with st.container(width=350):
        cols = st.columns([1, 1, 1])
        for i in range(3):
            with cols[i]:
                for j in range(3):
                    _render_cell(i, j, board, winner, current_turn)


def _render_cell(
    i: int,
    j: int,
    board: list[list[str]],
    winner: str | None,
    current_turn: str,
) -> None:
    """Render a single Tic-Tac-Toe cell."""
    cell_value = board[i][j]
    button_disabled = (
        cell_value != ""
        or winner is not None
        or current_turn != st.session_state.my_symbol
        or len(server_state.games[st.session_state.game_id]["players"]) != NUM_PLAYERS
    )
    st.button(
        cell_value if cell_value else " ",
        key=f"cell_{cell_value if cell_value else 'empty'}_{i}_{j}",
        on_click=make_move,
        args=(i, j),
        width="stretch",
        disabled=button_disabled,
    )


def _apply_board_styles() -> None:
    """Inject custom CSS styles for the Tic-Tac-Toe grid."""
    game = server_state.games[st.session_state.game_id]
    st.markdown(
        f"""
        <style>
        div.stElementContainer[class*="st-key-cell_X_"] button {{
            background-image: url({game["players"].get("X", {}).get("logo")});
            background-color: black !important;
            background-size: auto 70%;
            background-position: center;
            background-repeat: no-repeat;
            width: 100px;
            height: 100px;
            color: transparent !important;
        }}
        div.stElementContainer[class*="st-key-cell_O_"] button {{
            background-image: url({game["players"].get("O", {}).get("logo")});
            background-color: white !important;
            background-size: auto 70%;
            background-position: center;
            background-repeat: no-repeat;
            width: 100px;
            height: 100px;
            color: transparent !important;
        }}
        div.stElementContainer[class*="st-key-cell_empty_"] button {{
            background-color: #888888 !important;
            width: 100px;
            height: 100px;
            color: transparent !important;
        }}
        div.stElementContainer[class*="st-key-cell_"] button:hover {{
            opacity: 0.8;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.fragment(run_every="3s")
def display_board(game: dict[str, object]) -> None:
    """Renders the Tic-Tac-Toe board and game status."""
    if not server_state.games.get(st.session_state.game_id):
        reset_game()
        return

    st.header(f"Game ID: {st.session_state.game_id}", anchor=False)
    board = game["board"]
    winner = game["winner"]
    current_turn = game["current_turn"]

    if winner:
        _display_winner_screen(winner)
    else:
        _display_player_info(current_turn)
        _render_board(board, winner, current_turn)

        st.divider()
        if st.button("Delete Game"):
            confirm_deletion()


@st.fragment(run_every="5s")
def display_lobby() -> None:
    """Renders the game lobby with open games."""
    st.title("Tic-Tac-Toe Lobby", anchor=False)
    st.write(
        f"Welcome {st.session_state['ttt-user']}! Create a new game or join an open one.",
    )
    if st.button("Create New Game"):
        create_new_game()

    st.subheader("Open Games", anchor=False)
    if (
        "games" not in server_state
        or not server_state.games
        or not server_state.get("games")
    ):
        st.info("No open games available. Be the first to create one!")
    else:
        cols = st.columns(3)
        for col_ind, (game_id, game) in enumerate(server_state.games.items()):
            with cols[col_ind % 3], st.container(border=True):
                st.subheader(f"Game: {game_id}", anchor=False)
                col1, col2, col3 = st.columns([2, 1, 5])
                with col1:
                    st.write("Player 1:")
                with col2:
                    st.image(game["players"]["X"]["logo"], width=25)
                with col3:
                    if game["winner"]:
                        st.badge(
                            f"{game['players']['X']['name']}",
                            icon=":material/trophy:"
                            if game["winner"] == "X"
                            else ":material/cancel:",
                            color="green" if game["winner"] == "X" else "red",
                        )
                    else:
                        st.write(f"{game['players']['X']['name']}")
                with col1:
                    st.write("Player 2:")
                if "O" in game["players"]:
                    with col2:
                        st.image(game["players"]["O"]["logo"], width=25)
                    with col3:
                        if game["winner"]:
                            st.badge(
                                f"{game['players']['O']['name']}",
                                icon=":material/trophy:"
                                if game["winner"] == "O"
                                else ":material/cancel:",
                                color="green" if game["winner"] == "O" else "red",
                            )
                        else:
                            st.write(
                                f"{game['players']['O']['name'] if game['players'].get('O') else ''}",
                            )
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        "Join Game",
                        key=f"lobby-{game_id}",
                        disabled=game["status"] != "waiting",
                    ):
                        join_game(game_id)
                        st.rerun()
                if st.session_state.get("roles", False) == "admin":
                    with col2:
                        if st.button("Delete Game", key=f"delete-{game_id}"):
                            reset_game(game_id)
                            st.rerun()


def run_game() -> None:
    if st.session_state.get("ttt-user") and st.session_state.get("ttt-team"):
        if "game_id" in st.session_state:
            if st.session_state.game_id in server_state.games:
                game = server_state.games[st.session_state.game_id]
                display_board(game)
            else:
                reset_game()
        else:
            display_lobby()
    else:
        display_user_settings()
