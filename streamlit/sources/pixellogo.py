import random
from datetime import datetime, timedelta, timezone
from io import BytesIO
from time import sleep
from typing import TypeVar

import pandas as pd
import requests
from PIL import Image
from sources.sql import create_sql_engine, query_db, validate_username
from sources.utils import display_table
from streamlit_autorefresh import st_autorefresh
from streamlit_server_state import no_rerun, server_state, server_state_lock

import streamlit as st

sql_engine = create_sql_engine()

IMAGE_SIZE = 512


def get_random_logo() -> tuple[str, Image.Image]:
    random_team = random.SystemRandom().choice(server_state["pl_all_teams"])
    team_name = random_team["name"]
    team_logo = random_team["logo"]
    response = requests.get(team_logo, timeout=10)
    team_img = Image.open(BytesIO(response.content))
    return team_name, team_img


def select_name() -> None:
    def add_to_leaderboard(player_name: str) -> None:
        if player_name not in server_state["pl_leaderboard"]["Player Name"].to_numpy():
            with no_rerun, server_state_lock["pl_leaderboard"]:
                server_state["pl_leaderboard"] = pd.concat(
                    [
                        server_state["pl_leaderboard"],
                        pd.DataFrame(
                            [[player_name, 0, 0, 0]],
                            columns=server_state["pl_leaderboard"].columns,
                        ),
                    ],
                    ignore_index=True,
                )

    if st.session_state.get("username", None):
        st.session_state["pl_player_name"] = st.session_state["username"]
        add_to_leaderboard(st.session_state["pl_player_name"])
        st.rerun()
    else:
        player_name = st.text_input("Enter your name:")
        if st.button("Select name"):
            if validate_username(player_name):
                st.session_state["pl_player_name"] = player_name
                add_to_leaderboard(st.session_state["pl_player_name"])
            else:
                st.error("Please use a different name!")
                st.stop()
        else:
            st.stop()


def _init_server_state(key: str, default_value: TypeVar("T")) -> None:
    if key not in server_state:
        with server_state_lock[key]:
            server_state[key] = default_value


def initialize_game() -> None:
    with no_rerun:
        _init_server_state("pl_sec_per_round", 5)
        _init_server_state(
            "pl_all_teams",
            query_db(
                sql_engine,
                "SELECT name, logo FROM teams WHERE `name` NOT IN ('Afc', 'Nfc', 'TBD');",
            ),
        )
        _init_server_state(
            "pl_available_stages",
            [4, 8, 16, 32, 64, 512, 9999, 9999],
        )
        _init_server_state("pl_current_logo", get_random_logo())
        _init_server_state("pl_current_stage", 0)
        _init_server_state("pl_last_update", datetime.now(timezone.utc))
        _init_server_state(
            "pl_leaderboard",
            pd.DataFrame(
                columns=[
                    "Player Name",
                    "Total score",
                    "Total games",
                    "Points per game",
                ],
            ),
        )

    # session_state initialization (no flake8 issues here)
    st.session_state.setdefault("pl_allowed_to_guess", True)
    st.session_state.setdefault("pl_feedback", "")
    if "pl_player_name" not in st.session_state:
        select_name()


def update_server() -> None:
    with no_rerun:
        with server_state_lock["pl_update"]:
            if datetime.now(timezone.utc) - server_state["pl_last_update"] > timedelta(
                seconds=server_state["pl_sec_per_round"],
            ):
                with server_state_lock["pl_current_stage"]:
                    server_state["pl_current_stage"] = (
                        server_state["pl_current_stage"] + 1
                    ) % len(server_state["pl_available_stages"])
                if server_state["pl_current_stage"] == 0:
                    with server_state_lock["pl_current_logo"]:
                        server_state["pl_current_logo"] = get_random_logo()
                with server_state_lock["pl_last_update"]:
                    server_state["pl_last_update"] = datetime.now(timezone.utc)
            else:
                sleep(0.1)
        if server_state["pl_current_stage"] == 0:
            st.session_state["pl_feedback"] = ""
            st.session_state["pl_allowed_to_guess"] = True


def evaluate_guess(guess: str, target: str) -> None:
    if guess == target:
        st.session_state["pl_allowed_to_guess"] = False
        st.session_state["pl_feedback"] = f"You guessed correctly the {target}!"
        server_state["pl_leaderboard"].loc[
            server_state["pl_leaderboard"]["Player Name"]
            == st.session_state["pl_player_name"],
            "Total score",
        ] += 5 - server_state["pl_current_stage"]
        server_state["pl_leaderboard"].loc[
            server_state["pl_leaderboard"]["Player Name"]
            == st.session_state["pl_player_name"],
            "Total games",
        ] += 1
        server_state["pl_leaderboard"].loc[
            server_state["pl_leaderboard"]["Player Name"]
            == st.session_state["pl_player_name"],
            "Points per game",
        ] = (
            server_state["pl_leaderboard"].loc[
                server_state["pl_leaderboard"]["Player Name"]
                == st.session_state["pl_player_name"],
                "Total score",
            ]
            / server_state["pl_leaderboard"].loc[
                server_state["pl_leaderboard"]["Player Name"]
                == st.session_state["pl_player_name"],
                "Total games",
            ]
        )
    elif guess in [i["name"] for i in server_state["pl_all_teams"]]:
        st.session_state["pl_feedback"] = (
            f"You guessed wrongly the {guess}.  \nThe correct team was the {target}!"
        )
        st.session_state["pl_allowed_to_guess"] = False
        server_state["pl_leaderboard"].loc[
            server_state["pl_leaderboard"]["Player Name"]
            == st.session_state["pl_player_name"],
            "Total games",
        ] += 1
        server_state["pl_leaderboard"].loc[
            server_state["pl_leaderboard"]["Player Name"]
            == st.session_state["pl_player_name"],
            "Points per game",
        ] = (
            server_state["pl_leaderboard"].loc[
                server_state["pl_leaderboard"]["Player Name"]
                == st.session_state["pl_player_name"],
                "Total score",
            ]
            / server_state["pl_leaderboard"].loc[
                server_state["pl_leaderboard"]["Player Name"]
                == st.session_state["pl_player_name"],
                "Total games",
            ]
        )
    else:
        st.write("Your guess is not a valid team name, try again.")
    st.rerun()


def display_admin_panel() -> None:
    st.divider()
    st.subheader("Admin settings", anchor=False)
    if st.button("Reset leaderboard"):
        with no_rerun:
            server_state["pl_leaderboard"] = pd.DataFrame(
                columns=[
                    "Player Name",
                    "Total score",
                    "Total games",
                    "Points per game",
                ],
            )
    player_to_delete = st.selectbox(
        "Select a player to delete",
        server_state["pl_leaderboard"]["Player Name"].values,
    )
    if st.button("Delete player"):
        server_state["pl_leaderboard"] = server_state["pl_leaderboard"][
            server_state["pl_leaderboard"]["Player Name"] != player_to_delete
        ]


def display_leaderboard() -> None:
    st.header("Leaderboard", anchor=False)
    display_table(
        server_state["pl_leaderboard"]
        .sort_values(by=["Total score", "Total games"], ascending=[False, True])
        .set_index("Player Name"),
        1,
        3,
    )
    if st.session_state.get("roles", False) == "admin":
        display_admin_panel()


def display_game() -> None:
    update_server()
    team_name, team_img = server_state["pl_current_logo"]
    res = server_state["pl_available_stages"][server_state["pl_current_stage"]]
    if res <= IMAGE_SIZE:
        st.header("Guess the logo", anchor=False)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(
                team_img.resize((res, res)).resize(
                    (IMAGE_SIZE, IMAGE_SIZE),
                    resample=Image.NEAREST,
                ),
            )
        with col2:
            if res < IMAGE_SIZE:
                user_guess = st.selectbox(
                    "Guess the team",
                    [i["name"] for i in server_state["pl_all_teams"]],
                    key="pl_user_guess",
                    placeholder="Guess a team",
                    index=None,
                    disabled=not st.session_state["pl_allowed_to_guess"],
                )
                if st.session_state["pl_allowed_to_guess"]:  # noqa: SIM102
                    if st.button("Submit your guess"):
                        evaluate_guess(user_guess, team_name)
            elif st.session_state["pl_feedback"] == "":
                st.session_state["pl_feedback"] = (
                    f"The team we were looking for was: {team_name}!"
                )
            st.header(st.session_state["pl_feedback"], anchor=False)
    else:
        display_leaderboard()

    st_autorefresh(
        max(
            1000,
            int(
                (
                    server_state["pl_sec_per_round"]
                    - (
                        datetime.now(timezone.utc) - server_state["pl_last_update"]
                    ).total_seconds()
                )
                * 1000,
            ),
        ),
    )
