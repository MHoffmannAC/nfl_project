import streamlit as st
from streamlit_server_state import server_state, server_state_lock, no_rerun
from streamlit_autorefresh import st_autorefresh

from PIL import Image
import random
import requests
from io import BytesIO
import datetime as dt
import pandas as pd
from time import sleep

from sources.sql import create_sql_engine, query_db, validate_username
sql_engine = create_sql_engine()

def get_random_logo():
    random_team = random.choice(server_state["pl_all_teams"])
    team_name = random_team['name']
    team_logo = random_team['logo']
    response = requests.get(team_logo)
    team_img = Image.open(BytesIO(response.content))
    return team_name, team_img

def select_name():
    def add_to_leaderboard(player_name):
        if not player_name in server_state["pl_leaderboard"]["Player Name"].values:
            with no_rerun:
                with server_state_lock["pl_leaderboard"]:
                    server_state["pl_leaderboard"] = pd.concat([server_state["pl_leaderboard"], pd.DataFrame([[player_name, 0, 0, 0]], columns=server_state["pl_leaderboard"].columns)], ignore_index=True)
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

def initialize_game():
    with no_rerun:
        if "pl_sec_per_round" not in server_state:
            with server_state_lock["pl_sec_per_round"]:
                server_state["pl_sec_per_round"] = 5
        if "pl_all_teams" not in server_state:
            with server_state_lock["pl_all_teams"]:
                server_state["pl_all_teams"] = query_db(sql_engine, "SELECT name, logo FROM teams WHERE `name` NOT IN ('Afc', 'Nfc', 'TBD');")
        if "pl_available_stages" not in server_state:
            with server_state_lock["pl_available_stages"]:
                server_state["pl_available_stages"] = [4,8,16,32,64,512,9999,9999]  
        if "pl_current_logo" not in server_state:
            with server_state_lock["pl_current_logo"]:
                server_state["pl_current_logo"] = get_random_logo()
        if "pl_current_stage" not in server_state:
            with server_state_lock["pl_current_stage"]:
                server_state["pl_current_stage"] = 0           
        if "pl_last_update" not in server_state:
            with server_state_lock["pl_last_update"]:
                server_state["pl_last_update"] = dt.datetime.now()
        if "pl_leaderboard" not in server_state:
            with server_state_lock["pl_leaderboard"]:
                server_state["pl_leaderboard"] = pd.DataFrame(columns=["Player Name", "Total score", "Total games", "Points per game"])
                
    if "pl_allowed_to_guess" not in st.session_state:
        st.session_state["pl_allowed_to_guess"] = True
    if "pl_feedback" not in st.session_state:
        st.session_state["pl_feedback"] = ""
    if "pl_player_name" not in st.session_state:
        select_name()
            
            
def update_server():
    with no_rerun:
        with server_state_lock["pl_update"]:
            if dt.datetime.now() - server_state["pl_last_update"] > dt.timedelta(seconds=server_state["pl_sec_per_round"]):
                with server_state_lock["pl_current_stage"]:
                    server_state["pl_current_stage"] = (server_state["pl_current_stage"] + 1) % len(server_state["pl_available_stages"])
                if server_state["pl_current_stage"] == 0:
                    with server_state_lock["pl_current_logo"]:
                        server_state["pl_current_logo"] = get_random_logo()
                with server_state_lock["pl_last_update"]:
                    server_state["pl_last_update"] = dt.datetime.now()
            else:
                sleep(0.1)
        if server_state["pl_current_stage"] == 0:
            st.session_state["pl_feedback"] = ""
            st.session_state["pl_allowed_to_guess"] = True

def evaluate_guess(guess, target):
    if guess == target:
        st.session_state["pl_allowed_to_guess"] = False
        st.session_state["pl_feedback"] = f"You guessed correctly the {target}!"
        server_state["pl_leaderboard"].loc[server_state["pl_leaderboard"]["Player Name"] == st.session_state["pl_player_name"], "Total score"] += (5 - server_state["pl_current_stage"])
        server_state["pl_leaderboard"].loc[server_state["pl_leaderboard"]["Player Name"] == st.session_state["pl_player_name"], "Total games"] += 1
        server_state["pl_leaderboard"].loc[server_state["pl_leaderboard"]["Player Name"] == st.session_state["pl_player_name"], "Points per game"] = (
            server_state["pl_leaderboard"].loc[server_state["pl_leaderboard"]["Player Name"] == st.session_state["pl_player_name"], "Total score"] /
            server_state["pl_leaderboard"].loc[server_state["pl_leaderboard"]["Player Name"] == st.session_state["pl_player_name"], "Total games"]
            )
    elif guess in [i['name'] for i in server_state['pl_all_teams']]:
        st.session_state["pl_feedback"] = f"You guessed wrongly the {guess}.  \nThe correct team was the {target}!"
        st.session_state["pl_allowed_to_guess"] = False
        server_state["pl_leaderboard"].loc[server_state["pl_leaderboard"]["Player Name"] == st.session_state["pl_player_name"], "Total games"] += 1
        server_state["pl_leaderboard"].loc[server_state["pl_leaderboard"]["Player Name"] == st.session_state["pl_player_name"], "Points per game"] = (
            server_state["pl_leaderboard"].loc[server_state["pl_leaderboard"]["Player Name"] == st.session_state["pl_player_name"], "Total score"] /
            server_state["pl_leaderboard"].loc[server_state["pl_leaderboard"]["Player Name"] == st.session_state["pl_player_name"], "Total games"]
            )
    else:
        st.write("Your guess is not a valid team name, try again.")
    st.rerun()

def display_admin_panel():
    st.divider()
    st.subheader("Admin settings")
    if st.button("Reset leaderboard"):
        with no_rerun:
            server_state["pl_leaderboard"] = pd.DataFrame(columns=["Player Name", "Total score", "Total games", "Points per game"])
    player_to_delete = st.selectbox("Select a player to delete", server_state["pl_leaderboard"]["Player Name"].values)
    if st.button("Delete player"):
        server_state["pl_leaderboard"] = server_state["pl_leaderboard"][server_state["pl_leaderboard"]["Player Name"] != player_to_delete]

def display_leaderboard():
    st.title("Leaderboard")
    st.dataframe(server_state["pl_leaderboard"].sort_values(by=["Total score", "Total games"], ascending=[False, True]),
                     hide_index = True)
    if st.session_state.get("roles", False) == "admin":
        display_admin_panel()

def display_game():
    update_server()
    team_name, team_img = server_state["pl_current_logo"]
    res = server_state["pl_available_stages"][server_state["pl_current_stage"]]
    if res <= 512:
        st.header("Guess the logo")
        col1, col2 = st.columns([1,1])
        with col1:
            st.image(team_img.resize((res,res)).resize((512,512), resample=Image.NEAREST))
        with col2:
            if res < 512:
                user_guess = st.selectbox("Guess the team",
                                          [i['name'] for i in server_state['pl_all_teams']],
                                          key="pl_user_guess",
                                          placeholder="Guess a team",
                                          index=None,
                                          disabled=not st.session_state["pl_allowed_to_guess"])
                if st.session_state["pl_allowed_to_guess"]:
                    if st.button("Submit your guess"):
                        evaluate_guess(user_guess, team_name)
            elif st.session_state["pl_feedback"] == "":
                st.session_state["pl_feedback"] = f"The team we were looking for was: {team_name}!"
            st.header(st.session_state["pl_feedback"])
    else:
        display_leaderboard()

    st_autorefresh(max(1000, int((server_state["pl_sec_per_round"]-(dt.datetime.now() - server_state["pl_last_update"]).total_seconds())*1000)))