import asyncio
import html
import random
import threading
import time

import pandas as pd
from sources.long_queries import query_players
from sources.sql import create_sql_engine, query_db, validate_username
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

MAX_GUESSERS_TO_SCORE = 5
LOG_MAX_ENTRIES = 20
LEADERBOARD_DISPLAY_TIME = 20


def state_inits() -> None:
    if "shared_memory" not in globals():
        globals()["shared_memory"] = {
            "guesses": [],
            "tiktok_logs": [],
            "secret_idx": None,
            "players_df": None,
            "tiktok_active": False,
            "tiktok_running": False,
            "initialized": False,
            "lock": threading.Lock(),
            "win_time": None,
            "round_winner": None,
            "leaderboard": {},
        }

    if "rosterle" not in st.session_state:
        st.session_state["rosterle"] = {
            "username": None,
            "admin_random_guess": False,
            "admin_random_guess_time": 30,
        }

    shared = globals()["shared_memory"]

    with shared["lock"]:
        if not shared["initialized"]:
            shared["players_df"] = get_players_data()
            if shared["players_df"] is not None:
                shared["secret_idx"] = random.SystemRandom().choice(
                    shared["players_df"].index.tolist(),
                )
                shared["initialized"] = True


def get_dynamic_font_size(name: str) -> str:
    length = len(name)
    return f"{max(0.6, min(1.0, 12 / length))}rem"


def get_players_data() -> pd.DataFrame | None:
    try:
        sql_engine = create_sql_engine()
        query = query_players()
        df = pd.DataFrame(query_db(sql_engine, query))
        if df.empty:
            return None
        df["jersey"] = pd.to_numeric(df["jersey"], errors="coerce")
        return df.dropna().reset_index(drop=True)
    except Exception:
        return None


def add_log(msg: str) -> None:
    shared = globals()["shared_memory"]
    with shared["lock"]:
        shared["tiktok_logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        if len(shared["tiktok_logs"]) > LOG_MAX_ENTRIES:
            shared["tiktok_logs"].pop(0)


def calculate_score(guess: dict, secret_jersey: int) -> int:
    score = 0
    if guess["conference"]["correct"]:
        score += 100
    if guess["division"]["correct"]:
        score += 100
    if guess["team"]["correct"]:
        score += 100
    if guess["position"]["correct"]:
        score += 100
    try:
        diff = abs(int(secret_jersey) - int(guess["jersey"]["value"]))
        score += max(0, 100 - diff)
    except:
        pass
    return score


def process_guess(
    guess_name: str,
    user_nick: str = "System",
    *,
    is_tiktok: bool = False,
) -> bool:
    if not guess_name:
        return False
    add_log(
        f"Guess received from {user_nick}: {guess_name}"
        + (" (TikTok)" if is_tiktok else ""),
    )

    shared = globals()["shared_memory"]
    with shared["lock"]:
        if shared["win_time"] is not None:
            return False
        df = shared["players_df"]
        if df is None:
            return False

        secret = df.loc[shared["secret_idx"]]

        if any(
            g["player_name"].lower() == guess_name.lower().strip()
            for g in shared["guesses"]
        ):
            return False

        match = df[df["player_name"].str.lower() == guess_name.lower().strip()]
        if not match.empty:
            guess_data = match.iloc[0]
            try:
                g_jersey = int(guess_data["jersey"])
                s_jersey = int(secret["jersey"])
            except:
                g_jersey, s_jersey = 0, 0

            new_result = {
                "player_name": guess_data["player_name"],
                "guesser": user_nick,
                "conference": {
                    "value": guess_data["conference"],
                    "correct": guess_data["conference"] == secret["conference"],
                },
                "division": {
                    "value": guess_data["division"],
                    "correct": guess_data["division"] == secret["division"],
                },
                "team": {
                    "value": guess_data["team_name"],
                    "logo": guess_data["logo"],
                    "correct": guess_data["team_name"] == secret["team_name"],
                },
                "position": {
                    "value": guess_data["position"],
                    "correct": guess_data["position"] == secret["position"],
                },
                "jersey": {
                    "value": g_jersey,
                    "correct": g_jersey == s_jersey,
                    "direction": ("up" if g_jersey < s_jersey else "down")
                    if g_jersey != s_jersey
                    else None,
                },
                "timestamp": time.time(),
            }
            new_result["score"] = calculate_score(new_result, s_jersey)
            is_winner = all(
                new_result[k]["correct"]
                for k in ["conference", "division", "team", "position", "jersey"]
            )

            shared["guesses"].append(new_result)

            if is_winner:
                shared["win_time"] = time.time()
                shared["round_winner"] = user_nick
                distribute_points()
            return True
    return False


def distribute_points() -> None:
    shared = globals()["shared_memory"]
    sorted_guesses = sorted(
        shared["guesses"],
        key=lambda x: (-x["score"], x["timestamp"]),
    )
    unique_users = []
    points_tier = [1000, 500, 250, 150, 50]

    for g in sorted_guesses:
        u = g["guesser"]
        if u not in unique_users:
            unique_users.append(u)
        if len(unique_users) >= MAX_GUESSERS_TO_SCORE:
            break

    for i, user in enumerate(unique_users):
        shared["leaderboard"][user] = (
            shared["leaderboard"].get(user, 0) + points_tier[i]
        )


def start_tiktok_listener(unique_id: str, streamlit_ctx: object) -> None:
    add_script_run_ctx(threading.current_thread(), streamlit_ctx)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = TikTokLiveClient(unique_id=unique_id)

    @client.on(CommentEvent)
    async def on_comment(event: CommentEvent) -> None:
        try:
            comment = event.comment
            user = event.user

            nickname = (
                getattr(user, "nickname", None)
                or getattr(user, "unique_id", None)
                or "User"
            )

            if comment:
                process_guess(comment.strip(), nickname, is_tiktok=True)

        except Exception as e:
            add_log(f"Comment error: {e!r}")

    @client.on(ConnectEvent)
    async def on_connect(_: ConnectEvent) -> None:
        shared = globals()["shared_memory"]
        shared["tiktok_active"] = True
        add_log(f"CONNECTED to @{unique_id}")

    @client.on(DisconnectEvent)
    async def on_disconnect(_: DisconnectEvent) -> None:
        shared = globals()["shared_memory"]
        shared["tiktok_active"] = False
        add_log("DISCONNECTED")

    async def runner() -> None:
        shared = globals()["shared_memory"]
        shared["tiktok_running"] = True

        try:
            await client.start()

            while shared.get("tiktok_running", False):
                await asyncio.sleep(0.5)

        finally:
            try:
                await client.stop()
            except Exception:
                pass

    try:
        loop.run_until_complete(runner())
    except Exception as e:
        add_log(f"TIKTOK LISTENER CRASH: {e!r}")
    finally:
        loop.close()


# --------------------------------------------------
# UI
# --------------------------------------------------
def run_game() -> None:
    state_inits()

    st.markdown(
        """
        <style>
        .main-game-wrapper { max-width: 450px; margin: 0 auto; font-family: sans-serif; }
        .rosterle-grid {
            display: grid; grid-template-columns: 2.5fr 1fr 1fr 1.2fr 1fr 1fr;
            grid-column-gap: 4px; width: 100%; margin-bottom: 4px;
        }
        .grid-header { color: #8b949e; font-size: 0.6rem; font-weight: 800; text-align: center; padding-bottom: 4px; text-transform: uppercase; }
        .tile {
            height: 55px; background-color: #1f2933; border-radius: 4px;
            display: flex; align-items: center; justify-content: center;
            color: white; font-weight: bold; font-size: 0.85rem; text-align: center;
            overflow: hidden; padding: 2px; box-sizing: border-box;
        }
        .tile-player { justify-content: center; padding-left: 8px; text-align: left; }
        .correct { background-color: #16a34a !important; }
        .wrong { background-color: #121212 !important; border: 1px solid #333; }
        .team-logo { height: 80%; width: auto; object-fit: contain; }
        .arrow { font-size: 1.1rem; margin-left: 2px; line-height: 1; vertical-align: middle; }
        .leaderboard-row { display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid #30363d; font-size: 0.9rem; }
        .lb-rank { color: #8b949e; font-weight: bold; width: 30px; }
        .lb-user { flex-grow: 1; color: white; }
        .lb-winner { font-weight: 900; color: #ffd33d !important; text-shadow: 0 0 8px rgba(255, 211, 61, 0.2); }
        .lb-points { color: #16a34a; font-weight: bold; }
        .reveal-box { background: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 8px; margin-bottom: 15px; text-align: center; }
        .countdown { text-align: center; font-size: 0.7rem; color: #8b949e; margin-top: 10px; }
        </style>
    """,
        unsafe_allow_html=True,
    )

    if (
        st.session_state.get("username", None)
        and st.session_state["rosterle"]["username"] != st.session_state["username"]
    ):
        st.session_state["rosterle"]["username"] = st.session_state["username"]

    if not st.session_state["rosterle"]["username"]:
        st.markdown(
            "<div style='text-align: center; margin-top: 50px;'>",
            unsafe_allow_html=True,
        )
        st.title("🏈 NFL Rosterle")
        rosterle_username_input = st.text_input("Select your nickname")
        if rosterle_username_input:
            if validate_username(rosterle_username_input):
                st.session_state["rosterle"]["username"] = rosterle_username_input
                st.rerun()
            else:
                st.warning("Please use a different name!")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Admin Sidebar
    if st.session_state.get("roles") == "admin":
        with st.sidebar:
            st.header("TikTok Integration")

            shared = globals()["shared_memory"]
            if not shared["tiktok_active"]:
                tt_user = st.text_input("TikTok Username", key="tt_user_input")
                if st.button("Connect Stream") and tt_user:
                    shared["tiktok_running"] = True
                    ctx = get_script_run_ctx()
                    t = threading.Thread(
                        target=start_tiktok_listener,
                        args=(tt_user, ctx),
                        daemon=True,
                    )
                    t.start()
            else:
                st.success("Connected!")
                if st.button("Disconnect"):
                    shared["tiktok_running"] = False
                    shared["tiktok_active"] = False
                    st.rerun()

            st.divider()

            @st.fragment(run_every=10)
            def sidebar_logs() -> None:
                st.caption("📜 Guess and Tiktok Logs")

                if not shared["tiktok_logs"]:
                    st.markdown(
                        """
                        <div style="
                            height: 220px;
                            background: #0e1117;
                            color: #c9d1d9;
                            font-family: monospace;
                            font-size: 12px;
                            padding: 8px;
                            border-radius: 6px;
                            overflow-y: auto;
                            white-space: pre-wrap;
                            word-break: break-word;
                        ">Waiting for events...
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    return

                log_text = "\n".join(
                    html.escape(x).strip() for x in reversed(shared["tiktok_logs"])
                )

                st.markdown(
                    f"""
                    <div style="
                        height: 220px;
                        background: #0e1117;
                        color: #c9d1d9;
                        font-family: monospace;
                        font-size: 12px;
                        padding: 8px;
                        border-radius: 6px;
                        overflow-y: auto;
                        white-space: pre-wrap;
                        word-break: break-word;
                    ">{log_text}</div>
                    """,
                    unsafe_allow_html=True,
                )

            sidebar_logs()

    st.markdown('<div class="main-game-wrapper">', unsafe_allow_html=True)
    st.markdown("### 🏈 NFL Rosterle")

    @st.fragment(run_every=2)
    def display_board_fragment() -> None:
        shared = globals()["shared_memory"]
        if shared["win_time"] is not None:
            elapsed = time.time() - shared["win_time"]
            if elapsed >= LEADERBOARD_DISPLAY_TIME:
                with shared["lock"]:
                    shared["secret_idx"] = random.SystemRandom().choice(
                        shared["players_df"].index.tolist(),
                    )
                    shared["guesses"] = []
                    shared["win_time"] = None
                    shared["round_winner"] = None
                st.rerun()

            secret_player = shared["players_df"].loc[shared["secret_idx"]]
            st.markdown(
                f"""
                <div class="reveal-box">
                    <div style="font-size: 0.7rem; color: #8b949e; text-transform: uppercase;">The Secret Player was</div>
                    <div style="font-size: 1.4rem; font-weight: 900; color: white;">{secret_player["player_name"]}</div>
                    <div style="font-size: 1.0rem; font-weight: 900; color: white;">{secret_player["position"]} for the {secret_player["team_name"]} ({secret_player["division"]})</div>
                    <div style="font-size: 0.8rem; color: #3fb950; margin-top: 4px;">Guessed correctly by <b>{shared["round_winner"]}</b></div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown(
                "<div style='text-align:center; padding: 10px 0;'>",
                unsafe_allow_html=True,
            )
            st.markdown("#### 🏆 GLOBAL STANDINGS")
            sorted_lb = sorted(shared["leaderboard"].items(), key=lambda x: -x[1])[:10]
            for i, (user, pts) in enumerate(sorted_lb):
                if user not in ["admin", "anonymous"]:
                    is_winner_row = user == shared["round_winner"]
                    st.markdown(
                        f"""
                    <div class="leaderboard-row">
                        <span class="lb-rank">#{i + 1}</span>
                        <span class="lb-user {"lb-winner" if is_winner_row else ""}">{user}</span>
                        <span class="lb-points">{pts} pts</span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            remaining = int(LEADERBOARD_DISPLAY_TIME - elapsed)
            st.markdown(
                f'<div class="countdown">Next game in {remaining}s...</div>',
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
            return

        st.markdown(
            """
            <div class="rosterle-grid">
                <div class="grid-header">PLAYER</div>
                <div class="grid-header">CONF</div>
                <div class="grid-header">DIV</div>
                <div class="grid-header">TEAM</div>
                <div class="grid-header">POS</div>
                <div class="grid-header">#</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        history = shared["guesses"]
        if not history:
            for _ in range(6):
                st.markdown(
                    """<div class="rosterle-grid"><div class="tile" style="opacity: 0.1;"></div><div class="tile" style="opacity: 0.1;"></div><div class="tile" style="opacity: 0.1;"></div><div class="tile" style="opacity: 0.1;"></div><div class="tile" style="opacity: 0.1;"></div><div class="tile" style="opacity: 0.1;"></div></div>""",
                    unsafe_allow_html=True,
                )
            return

        best_guesses = sorted(
            history,
            key=lambda x: (-x.get("score", 0), x["timestamp"]),
        )[:5]
        last_guess = history[-1]

        def render_row(g: dict) -> str:
            arrow = (
                "↑"
                if g["jersey"]["direction"] == "up"
                else ("↓" if g["jersey"]["direction"] == "down" else "")
            )
            return f"""
            <div class="rosterle-grid">
                <div class="tile tile-player" style="font-size: {get_dynamic_font_size(g["player_name"])}">{g["player_name"]}</div>
                <div class="tile {"correct" if g["conference"]["correct"] else "wrong"}">{g["conference"]["value"]}</div>
                <div class="tile {"correct" if g["division"]["correct"] else "wrong"}">{g["division"]["value"]}</div>
                <div class="tile {"correct" if g["team"]["correct"] else "wrong"}"><img src="{g["team"]["logo"]}" class="team-logo"></div>
                <div class="tile {"correct" if g["position"]["correct"] else "wrong"}">{g["position"]["value"]}</div>
                <div class="tile {"correct" if g["jersey"]["correct"] else "wrong"}">{g["jersey"]["value"]}<span class="arrow">{arrow}</span></div>
            </div>
            """

        st.markdown(
            "<div style='color: #8b949e; font-size: 0.6rem; margin-bottom: 4px; text-align: center; font-weight: bold;'>TOP 5 GUESSES</div>",
            unsafe_allow_html=True,
        )
        for g in best_guesses:
            st.markdown(render_row(g), unsafe_allow_html=True)

        for _ in range(max(0, 5 - len(best_guesses))):
            st.markdown(
                """<div class="rosterle-grid"><div class="tile" style="opacity: 0.05;"></div><div class="tile" style="opacity: 0.05;"></div><div class="tile" style="opacity: 0.05;"></div><div class="tile" style="opacity: 0.05;"></div><div class="tile" style="opacity: 0.05;"></div><div class="tile" style="opacity: 0.05;"></div></div>""",
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="separator-label" style="font-size: 0.6rem; color: #8b949e; text-align: center; margin-top: 10px; font-weight: bold;">LATEST GUESS</div>',
            unsafe_allow_html=True,
        )
        st.markdown(render_row(last_guess), unsafe_allow_html=True)

    display_board_fragment()
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    @st.fragment()
    def input_controls_fragment() -> None:
        shared = globals()["shared_memory"]
        if shared["win_time"] is not None:
            return
        players_df = shared["players_df"]
        current_user = st.session_state["rosterle"].get("username", "Unknown")

        def handle_submission() -> None:
            val = st.session_state.rosterle_input_widget
            if val:
                if process_guess(val, current_user):
                    st.session_state.rosterle_input_widget = None
                else:
                    st.warning("Already guessed.")

        st.selectbox(
            "Search Player",
            options=sorted(players_df["player_name"].tolist())
            if players_df is not None
            else [],
            index=None,
            key="rosterle_input_widget",
        )
        st.button("Submit Guess", use_container_width=True, on_click=handle_submission)

    input_controls_fragment()

    if st.session_state.get("roles") == "admin":
        st.toggle(
            "Enable Random Guessing (Admin Only)",
            value=st.session_state["rosterle"]["admin_random_guess"],
            key="admin_random_guess",
            on_change=lambda: st.session_state["rosterle"].update(
                {"admin_random_guess": st.session_state["admin_random_guess"]},
            ),
        )

        if st.session_state["rosterle"]["admin_random_guess"]:
            random_guess_time = st.slider(
                "Random Guess Interval (seconds)",
                min_value=5,
                max_value=300,
                value=st.session_state["rosterle"]["admin_random_guess_time"],
                key="admin_random_guess_time",
            )

            @st.fragment(run_every=random_guess_time)
            def random_guess_fragment() -> None:
                if shared["win_time"] is not None:
                    return
                players_df = shared["players_df"]
                if players_df is not None:
                    random_player = players_df.sample(1).iloc[0]["player_name"]
                    process_guess(random_player, user_nick="anonymous", is_tiktok=False)

            random_guess_fragment()
