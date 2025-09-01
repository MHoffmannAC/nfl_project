import streamlit as st
import numpy as np
import pandas as pd

from sklearn.tree import export_graphviz, DecisionTreeClassifier
from sklearn.tree._tree import TREE_LEAF

import tensorflow as tf

import dill 
import pickle 
from datetime import datetime

from sources.long_queries import query_plays
from sources.plots import plot_play_probabilities, plot_points, plot_win_probabilities, display_tree, prune_duplicate_leaves
from sources.sql import query_db, create_sql_engine, get_current_week, get_existing_ids, update_running_game, update_week
sql_engine = create_sql_engine()

st.markdown("""
    <style>
        .custom-code {
            color: #ffffff !important;  /* White text */
            background-color: #800020;  /* Dark background */
            padding: 3px 6px !important;
            border-radius: 5px !important;
            font-family: 'Courier New', Courier, monospace !important;
        }
        .st-emotion-cache-1jyaehf {
            color: #ffffff !important;  /* White text */
            background-color: #800020;  /* Dark background */
            padding: 3px 6px !important;
            border-radius: 5px !important;
            font-family: 'Courier New', Courier, monospace !important;
        }
        .st-emotion-cache-mka0c2 {
            color: #ffffff !important;  /* White text */
        }
    </style>
""", unsafe_allow_html=True)

week, season, game_type = get_current_week()

def update_week_dummy(week, season, game_type, sql_engine):
    #st.error("update_week is a DUMMY function, remember to change it!!")
    pass

@st.cache_resource(show_spinner=False)
def update_week_cached(week, season, game_type, _sql_engine):
    update_week(week, season, game_type, sql_engine)

def display_buttons(position):
    if st.button("Update latest play", key=f"restart{position}"):
        update_running_game(play_data['game_id'], sql_engine)
        st.rerun()
    st.write("Updating the latest play relies on the update of the ESPN database. In case they are falling behind, feel free to modify the game situation manually.")
    if st.button("Modify manually", key=f"manual{position}"):
        st.session_state["choice"] = "User Input (Full)"
        st.rerun()

# Main Page
st.title("NFL Predictor", anchor=False)

if ("game" in st.query_params) and (not st.query_params['game'] == "None"):
    selected_game = query_db(sql_engine, f"SELECT name FROM games WHERE game_id={st.query_params.game};")[0]['name']
    st.session_state["choice"] = "Live Game"
    st.session_state["game_name_selected"] = selected_game
    st.query_params.game = "None"

if "choice" not in st.session_state:
    st.session_state["choice"] = None
# Main st.session_state["choice"] buttons
st.session_state["choice"] = st.segmented_control("Choose an option:", ["Live Game", "User Input (Full)", "User Input (Tree)"], default=st.session_state["choice"], selection_mode="single")

if st.session_state["choice"] == "Live Game":
    # Live Game Page

    play_data = {'next_down': 0} # dummy

    with st.spinner("Updating Database"):
        update_week_cached(week, season, game_type, sql_engine)
        running_games = query_db(sql_engine, "SELECT * FROM games WHERE game_status=2;")

    st.subheader("Live Game", anchor=False)
    game_mapping = {game['name']: game for game in running_games}
    game_mapping[None] = None
    if not "game_name_selected" in st.session_state:
        st.session_state["game_name_selected"] = None
    st.session_state["game_name_selected"] = st.selectbox("Games", options=[i['name'] for i in running_games], index=None if st.session_state["game_name_selected"]==None else [i['name'] for i in running_games].index(st.session_state["game_name_selected"]), placeholder="Please select a game")
    game_selected = game_mapping[st.session_state["game_name_selected"]]
    if len(running_games) == 0:
        st.error("There isn't any game running right now. Please check back when the next one begins.")
        if st.button("Refresh"):
            st.rerun()
    if game_selected:
        query = query_plays(game_selected['game_id'])
        plays = query_db(sql_engine, query)
        plays_df = pd.DataFrame(plays)
        plays_df['completionRate'] = plays_df['completionRate'].fillna(0.7)
        plays_df['passToRushRatio'] = plays_df['passToRushRatio'].fillna(1)
        plays_df = plays_df.loc[plays_df['next_down']>0]
        play_data = plays_df.iloc[-1]
        st.session_state["play_data"] = play_data
        if(play_data['next_down']<1):
            col1, _, col3 = st.columns(3)
            with col1:
                st.write("Next play is a PAT or 2PT attempt. No model for this yet!")
            with col3:
                display_buttons("PAT")

elif st.session_state["choice"] == "User Input (Full)":

    if "play_data" in st.session_state:
        play_data = st.session_state["play_data"]
    else:
        play_data = {'quarter': 1, 'clock_seconds': 900, 'offenseAtHome': 1, 'possessionChange': 0, 'down': 1, 'next_down': 1, 'distance': 10, 'next_distance': 10, 'yardsToEndzone': 70, 'next_yardsToEndzone': 70, 'season': 2024, 'game_type': 'regular-season', 'week': 1, 'homeScore': 0, 'awayScore': 0, 'scoreDiff': 0, 'standing_home_overall_win': 0, 'standing_home_home_win': 0, 'standing_home_road_win': 0, 'standing_home_overall_loss': 0, 'standing_home_home_loss': 0, 'standing_home_road_loss': 0, 'standing_away_overall_win': 0, 'standing_away_home_win': 0, 'standing_away_road_win': 0, 'standing_away_overall_loss': 0, 'standing_away_home_loss': 0, 'standing_away_road_loss': 0, 'homeAbr': 'ATL', 'awayAbr': 'BUF', 'homeName': 'Atlanta Falcons', 'awayName': 'Buffalo Bills', 'totalTimeLeft': 3600, 'completionRate': 0.7, 'passToRushRatio': 1}

if (st.session_state["choice"] == "User Input (Full)") or ((st.session_state["choice"] == "Live Game") and (play_data['next_down']>0)):

    # Initialize session state with default values


# Reset to default function


    clock_seconds = play_data['clock_seconds']
    minutes = clock_seconds // 60
    seconds = clock_seconds % 60
    input_time = f"{int(minutes):02}:{int(seconds):02}"

    # Use columns to ensure inputs are half-width
    col1, col2, col3 = st.columns(3)

    with col1:
        game_type = st.radio("Game Type", ["Regular", "Postseason"], index=0 if play_data['game_type'] == 'regular-season' else 1, disabled=(st.session_state["choice"] == "Live Game"))
    with col2:
        season = st.selectbox("Season", options=range(2009,2025), index=list(range(2009,2025)).index(2024), disabled=(st.session_state["choice"] == "Live Game"))
        week_options = list(range(1, 19)) if game_type == "Regular" else ["SuperBowl", "ConfChamp", "DivRound", "WildCard"]
        try:
            week = st.selectbox("Week", options=week_options, index=week_options.index(play_data['week'] if isinstance(play_data['week'], int) else play_data['week']), disabled=(st.session_state["choice"] == "Live Game"))
        except:
            week = st.selectbox("Week", options=week_options, disabled=(st.session_state["choice"] == "Live Game"))
        if (type(week)==str):
            week_mapping= {"SuperBowl": 5, "ConfChamp": 3, "DivRound": 2, "WildCard": 1}
            week = week_mapping[week]
    
    if (st.session_state["choice"] == "Live Game"):
        with col3:
            display_buttons("top")

    st.divider()

    col1, col2, _ = st.columns(3)

    all_teams = list(get_existing_ids(sql_engine, 'teams', 'name'))
    team_to_abr = {i["name"]: i["abbreviation"] for i in query_db(sql_engine, "SELECT abbreviation, name FROM teams;")}
    team_to_color = {i["name"]: i["color"] for i in query_db(sql_engine, "SELECT color, name FROM teams;")}

    with col1:
        home_team = st.selectbox("Select Home Team", options=all_teams, index=all_teams.index(play_data['homeName']), disabled=(st.session_state["choice"] == "Live Game"))
        home_score = st.number_input("Home Team Score", min_value=0, step=1, value=play_data['homeScore'], disabled=(st.session_state["choice"] == "Live Game"))

    with col2:
        away_team = st.selectbox("Select Away Team", options=all_teams, index=all_teams.index(play_data['awayName']), disabled=(st.session_state["choice"] == "Live Game"))
        away_score = st.number_input("Away Team Score", min_value=0, step=1, value=play_data['awayScore'], disabled=(st.session_state["choice"] == "Live Game"))

    st.divider()

    col1, col2, _ = st.columns(3)
    with col1:
        quarter = st.slider("Quarter", min_value=1, max_value=4, step=1, value=play_data['quarter'], disabled=(st.session_state["choice"] == "Live Game"))  
    with col2:
        time = st.text_input("Time (format mm:ss)", value=input_time, disabled=(st.session_state["choice"] == "Live Game"))  
        try:
            parsed_time = datetime.strptime(time, "%M:%S")
            clock_seconds = parsed_time.minute * 60 + parsed_time.second
        except ValueError:
            st.error("Invalid time format. Please enter in mm:ss format.")

    st.divider()

    col1, col2, _ = st.columns(3)
    with col1:
        team_possession = st.radio("Team in Possession", options=[home_team, away_team], index=1 if (play_data['offenseAtHome']==play_data['possessionChange']) else 0, disabled=(st.session_state["choice"] == "Live Game")) 
        yards_to_endzone = st.slider("Yards to Endzone", min_value=1, max_value=100, step=1, value=play_data['next_yardsToEndzone'], disabled=(st.session_state["choice"] == "Live Game")) 
    with col2:
        down = st.slider("Down", min_value=1, max_value=4, step=1, value=play_data['next_down'], disabled=(st.session_state["choice"] == "Live Game"))  
        yards_for_first = st.number_input("Yards for 1st", min_value=1, step=1, value=play_data['next_distance'], disabled=(st.session_state["choice"] == "Live Game")) 

    st.divider()

    standings_input = "No"
    if not (st.session_state["choice"] == "Live Game"):
        col1, _, _ = st.columns(3)
        with col1:
            standings_input = st.radio("Hide standings?", options=["No", "Yes"], index=1)  

    if (standings_input == "No"):
        col1, col2, _ = st.columns(3)

        with col1:
            standing_home_overall_win = st.number_input(
                "Home Team Overall Wins", 
                min_value=0, 
                step=1, 
                value=play_data['standing_home_overall_win'], disabled=(st.session_state["choice"] == "Live Game")
            )
            standing_home_overall_loss = st.number_input(
                "Home Team Overall Losses", 
                min_value=0, 
                step=1, 
                value=play_data['standing_home_overall_loss'], disabled=(st.session_state["choice"] == "Live Game")
            )
            standing_home_home_win = st.number_input(
                "Home Team Wins at Home", 
                min_value=0, 
                step=1, 
                value=play_data['standing_home_home_win'], disabled=(st.session_state["choice"] == "Live Game")
            )
            standing_home_home_loss = st.number_input(
                "Home Team Losses at Home", 
                min_value=0, 
                step=1, 
                value=play_data['standing_home_home_loss'], disabled=(st.session_state["choice"] == "Live Game")
            )
            standing_home_road_win = st.number_input(
                "Home Team Wins on Road", 
                min_value=0, 
                step=1, 
                value=play_data['standing_home_road_win'], disabled=(st.session_state["choice"] == "Live Game")
            )
            standing_home_road_loss = st.number_input(
                "Home Team Losses on Road", 
                min_value=0, 
                step=1, 
                value=play_data['standing_home_road_loss'], disabled=(st.session_state["choice"] == "Live Game")
            )

        with col2:
            # Away Team Standings (depending on offenseAtHome)
            standing_away_overall_win = st.number_input(
                "Away Team Overall Wins", 
                min_value=0, 
                step=1, 
                value=play_data['standing_away_overall_win'], disabled=(st.session_state["choice"] == "Live Game")
            )
            standing_away_overall_loss = st.number_input(
                "Away Team Overall Losses", 
                min_value=0, 
                step=1, 
                value=play_data['standing_away_overall_loss'], disabled=(st.session_state["choice"] == "Live Game")
            )
            standing_away_home_win = st.number_input(
                "Away Team Wins at Home", 
                min_value=0, 
                step=1, 
                value=play_data['standing_away_home_win'], disabled=(st.session_state["choice"] == "Live Game")
            )
            standing_away_home_loss = st.number_input(
                "Away Team Losses at Home", 
                min_value=0, 
                step=1, 
                value=play_data['standing_away_home_loss'], disabled=(st.session_state["choice"] == "Live Game")
            )
            standing_away_road_win = st.number_input(
                "Away Team Wins on Road", 
                min_value=0, 
                step=1, 
                value=play_data['standing_away_road_win'], disabled=(st.session_state["choice"] == "Live Game")
            )
            standing_away_road_loss = st.number_input(
                "Away Team Losses on Road", 
                min_value=0, 
                step=1, 
                value=play_data['standing_away_road_loss'], disabled=(st.session_state["choice"] == "Live Game")
            )
    else:
        standing_home_overall_win = play_data["standing_home_overall_win"]
        standing_home_home_win = play_data["standing_home_home_win"]
        standing_home_road_win = play_data["standing_home_road_win"]
        standing_home_overall_loss = play_data["standing_home_overall_loss"]
        standing_home_home_loss = play_data["standing_home_home_loss"]
        standing_home_road_loss = play_data["standing_home_road_loss"]
        standing_away_overall_win = play_data["standing_away_overall_win"]
        standing_away_home_win = play_data["standing_away_home_win"]
        standing_away_road_win = play_data["standing_away_road_win"]
        standing_away_overall_loss = play_data["standing_away_overall_loss"]
        standing_away_home_loss = play_data["standing_away_home_loss"]
        standing_away_road_loss = play_data["standing_away_road_loss"]

    st.divider()

    prediction_data = {'quarter': quarter, 'clock_seconds': clock_seconds, 'offenseAtHome': 1 if team_possession==home_team else 0, 'down': down, 'distance': yards_for_first, 'yardsToEndzone': yards_to_endzone, 'season': season, 'game_type': "regular-season" if game_type=="Regular" else "post-season", 'week': week,
    'homeScore': home_score,
    'awayScore': away_score,
    'offenseScore': home_score if team_possession==home_team else away_score,
    'defenseScore': away_score if team_possession==home_team else home_score,
    'scoreDiff': home_score-away_score if team_possession==home_team else away_score-home_score,
    'standing_offense_overall_win': standing_home_overall_win if team_possession==home_team else standing_away_overall_win,
    'standing_offense_home_win': standing_home_home_win if team_possession==home_team else standing_away_home_win,
    'standing_offense_road_win': standing_home_road_win if team_possession==home_team else standing_away_road_win,
    'standing_offense_overall_loss': standing_home_overall_loss if team_possession==home_team else standing_away_overall_loss,
    'standing_offense_home_loss': standing_home_home_loss if team_possession==home_team else standing_away_home_loss,
    'standing_offense_road_loss': standing_home_road_loss if team_possession==home_team else standing_away_road_loss,
    'standing_defense_overall_win': standing_away_overall_win if team_possession==home_team else standing_home_overall_win,
    'standing_defense_home_win': standing_away_home_win if team_possession==home_team else standing_home_home_win,
    'standing_defense_road_win': standing_away_road_win if team_possession==home_team else standing_home_road_win,
    'standing_defense_overall_loss': standing_away_overall_loss if team_possession==home_team else standing_home_overall_loss,
    'standing_defense_home_loss': standing_away_home_loss if team_possession==home_team else standing_home_home_loss,
    'standing_defense_road_loss': standing_away_road_loss if team_possession==home_team else standing_home_road_loss,
    'standing_home_overall_win': standing_home_overall_win,
    'standing_home_home_win': standing_home_home_win,
    'standing_home_road_win': standing_home_road_win,
    'standing_home_overall_loss': standing_home_overall_loss,
    'standing_home_home_loss': standing_home_home_loss,
    'standing_home_road_loss': standing_home_road_loss,
    'standing_away_overall_win': standing_away_overall_win,
    'standing_away_home_win': standing_away_home_win,
    'standing_away_road_win': standing_away_road_win,
    'standing_away_overall_loss': standing_away_overall_loss,
    'standing_away_home_loss': standing_away_home_loss,
    'standing_away_road_loss': standing_away_road_loss,
    'homeAbr': team_to_abr[home_team],
    'awayAbr': team_to_abr[away_team],
    'offenseAbr': team_to_abr[home_team] if team_possession==home_team else team_to_abr[away_team],
    'defenseAbr': team_to_abr[away_team] if team_possession==home_team else team_to_abr[home_team],
    'totalTimeLeft': (clock_seconds + (4 - quarter) * 15 * 60), 'completionRate': play_data['completionRate'], 'passToRushRatio': play_data['passToRushRatio']}

    with open('streamlit/sources/nn_classifier.pkl', 'rb') as f:
        nn_classifier = dill.load(f)
    with open('streamlit/sources/nn_encoder.pkl', 'rb') as f:
        nn_encoder = dill.load(f)

    try:
        class_probabilities = nn_classifier.predict_proba(pd.DataFrame.from_dict(prediction_data, orient='index').T)
    except:
        st.rerun()

    col1, col2, = st.columns(2)
    with col1:
        st.subheader("Play probabilities:", anchor=False)
        plot_play_probabilities(nn_encoder.categories_[0], class_probabilities)

    with open('streamlit/sources/nn_regressor.pkl', 'rb') as f:
        nn_regressor = dill.load(f)
    st.divider()
    if (st.session_state["choice"] == "Live Game"):
        with col2:
            display_buttons("bottom")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Win probabilities:", anchor=False)
            win_probabilities = nn_regressor.predict(plays_df)
            plot_win_probabilities(plays_df['totalTimeLeft'], win_probabilities[:,0], plays_df['homeColor'].values[0], plays_df['awayColor'].values[0], plays_df['homeName'].values[0], plays_df['awayName'].values[0])
        with col2:
            st.subheader("Scores:", anchor=False)
            plot_points(plays_df['totalTimeLeft'], plays_df['homeScore'], plays_df['awayScore'], plays_df['homeColor'].values[0], plays_df['awayColor'].values[0], plays_df['homeName'].values[0], plays_df['awayName'].values[0])
    else:
        st.subheader("Win probabilities:", anchor=False)
        probabilities = nn_regressor.predict(pd.DataFrame.from_dict(prediction_data, orient='index').T)
        #st.write(f"Home team win probability: {np.round(probabilities[0][0]*100)}%")
        #st.write(f"Away team win probability: {np.round(probabilities[0][1]*100)}%")
        #if (np.round(probabilities[0][2]*100))>0:
        #    st.write(f"Tie probability: {np.round(probabilities[0][2]*100)}%")
            
        home_prob = probabilities[0][0] * 100
        away_prob = probabilities[0][1] * 100
        tie_prob = probabilities[0][2] * 100

        def render_side(prob, color, left_text="", right_text="", show_text=True):
            if not show_text:
                return f'<div style="flex:{prob}; background-color:{color}; overflow:hidden;"></div>'
            return (f'<div style="flex:{prob}; background-color:{color}; display:flex; '
                    f'justify-content:space-between; align-items:center; padding:0 8px; '
                    f'color:white; font-weight:bold;">'
                    f'<span style="text-align:left;">{left_text}</span>'
                    f'<span style="text-align:right;">{right_text}</span>'
                    f'</div>')

        home_html = render_side(
            prob=home_prob,
            color=f"#{team_to_color[home_team]}",
            left_text=team_to_abr[home_team],
            right_text=f"{home_prob:.0f}%",
            show_text=home_prob > 10
        )

        tie_html = render_side(
            prob=tie_prob,
            color="#444444",
            show_text=False
        )

        away_html = render_side(
            prob=away_prob,
            color=f"#{team_to_color[away_team]}",
            left_text=f"{away_prob:.0f}%",
            right_text=team_to_abr[away_team],
            show_text=away_prob > 10
        )

        bar_html = f'<div style="display:flex; height:40px; width:50%; border-radius:8px; overflow:hidden; border:1px solid #ccc;">{home_html}{away_html}</div>'

        st.markdown(bar_html, unsafe_allow_html=True)




if st.session_state["choice"] == 'User Input (Tree)':
   
    with st.spinner("Planting Tree..."):
        with open('streamlit/sources/decision_tree_model.pkl', 'rb') as f:
            clf = pickle.load(f)
            prune_duplicate_leaves(clf.named_steps['classifier'])

    st.header('Interactive Decision Tree Classifier', anchor=False)

    if "current_node" not in st.session_state:
        st.session_state.current_node = 0  # Start at root
        st.session_state.path = []  # Store path decisions

    tree = clf.named_steps['classifier'].tree_
    current_node = st.session_state.current_node

    class_probabilities = tree.value[current_node].flatten() / tree.value[current_node].sum()
    predicted_class = np.argmax(class_probabilities)

    col1, col2 = st.columns(2, vertical_alignment="center")
    with col1:
        # Check if the current node is a leaf
        if tree.children_left[current_node] == -1 and tree.children_right[current_node] == -1:
            st.success(f"The most likely next play is a &nbsp;&nbsp;&nbsp; **{clf.classes_[predicted_class]}** &nbsp;&nbsp;&nbsp; with a probability of &nbsp;&nbsp;&nbsp; **{round(class_probabilities[predicted_class]*100)}%**")

            # Reset button
            if st.button("Restart"):
                st.session_state.current_node = 0
                st.session_state.path = []
                st.rerun()

        else:
            # Current feature and threshold
            feature = tree.feature[current_node]
            threshold = tree.threshold[current_node]
            feature_name = clf.named_steps['preprocessing'].get_feature_names_out()[feature].replace('num_pipe__', '').replace('cat_pipe__', '')

            # Display the decision
            st.markdown(f"Is&nbsp;&nbsp; <span class='custom-code'>{feature_name}</span> &nbsp; <= &nbsp; {threshold}?", unsafe_allow_html=True)

            # Checkbox for each decision
            if st.checkbox(f"Yes:&nbsp;  {feature_name}  <=&nbsp; {threshold}", key=f"left_{current_node}"):
                next_node = tree.children_left[current_node]
                st.session_state.path.append([feature_name, threshold, True, current_node])
                st.session_state.current_node = next_node
                st.rerun()

            if st.checkbox(f"No:&nbsp;&nbsp;  {feature_name}  >&nbsp; {threshold}", key=f"right_{current_node}"):
                next_node = tree.children_right[current_node]
                st.session_state.path.append([feature_name, threshold, False, current_node])
                st.session_state.current_node = next_node
                st.rerun()
                
            #st.write(f"Current predicted class: {clf.classes_[predicted_class]}")

    with col2:
        plot_play_probabilities(clf.classes_, class_probabilities)


    if "show_tree" not in st.session_state:
        st.session_state["show_tree"] = False

    toggled = st.toggle("Toggle path visualization (Text or Tree)", value =st.session_state["show_tree"])
            
    if toggled:
        st.session_state["show_tree"] = True
        dtree = clf.named_steps['classifier'] 
        feature_names = clf.named_steps['preprocessing'].get_feature_names_out()
        display_tree(dtree, feature_names, highlight=[i[3] for i in st.session_state.path] + [current_node])
    else:
        st.session_state["show_tree"] = False
        st.write("Path through the tree:")        
        for step in st.session_state.path:
            st.markdown(f"{step[0]}&nbsp;&nbsp;&nbsp;<=&nbsp;&nbsp;&nbsp;{step[1]}&nbsp;?&nbsp;&nbsp; {':green-badge[:material/check: True]' if step[2] else ':red-badge[:material/close_small: False]'}")
            
        






            
