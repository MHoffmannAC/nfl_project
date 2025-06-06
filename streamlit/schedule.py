import streamlit as st
import pandas as pd
import dill

from datetime import datetime
import pytz
from tzlocal import get_localzone

from sources.plots import plot_win_probabilities
from sources.sql import create_sql_engine, get_current_week, query_db, update_week, update_full_schedule
from sources.long_queries import query_plays

sql_engine = create_sql_engine()

current_week, current_season, current_game_type = get_current_week()

@st.cache_resource(show_spinner=False)
def update_week_cached(week, season, game_type, _sql_engine):
    update_week(week, season, game_type, sql_engine)

with st.spinner("Updating Schedule..."):
    update_week_cached(current_week, current_season, current_game_type, sql_engine)
    
if "game_type" not in st.session_state:
    st.session_state["game_type"] = current_game_type

st.markdown("""
    <style>
    h1, h2, h3, h4, h5, h6 {
        pointer-events: none; /* Disable link functionality */
    }
    [data-testid="stHeaderActionElements"] {
        display: none; /* Hide the copy link icon */
    }
    .streamlit-header:hover a {
        display: none; /* Hide the copy link icon */
    }
    </style>
""", unsafe_allow_html=True)


st.title("Schedule")

col1, col2, col3 = st.columns([1,3,1])
with col1:
    all_seasons = [i['season'] for i in query_db(sql_engine, "SELECT Distinct(season) FROM games ORDER BY season DESC;")]
    season = st.selectbox("Season", options=all_seasons, index=all_seasons.index(current_season))
if st.session_state.get("roles", False) == "admin":
    with col3:
        if st.button("Update all season standings"):
            with st.spinner("Updating full Schedule..."):
                update_full_schedule(season, sql_engine)

col1, col2, col3 = st.columns([1,3,1])
with col1:
    game_type = st.radio("Game Type", ["Regular", "Postseason"], index=0 if st.session_state["game_type"]=="regular-season" else 1, horizontal=True)
    
    game_type = 'regular-season' if game_type=='Regular' else 'post-season'
    
    if st.session_state["game_type"] != game_type:
        st.session_state["game_type"] = game_type
        st.rerun()

    week_mapping= {"SuperBowl": 5, "ConfChamp": 3, "DivRound": 2, "WildCard": 1}
    inverse_week_mapping = {v: k for k, v in week_mapping.items()}
    if game_type == "regular-season":
        week_options = list(range(1, 19))
        week = st.selectbox("Week", options=week_options, index=week_options.index(current_week))
    else:
        week_options = ["SuperBowl", "ConfChamp", "DivRound", "WildCard"]
        week = st.selectbox("Week", options=week_options, index=week_options.index(inverse_week_mapping[current_week]))

    if (type(week)==str):
        week = week_mapping[week]
with col3:
    if st.button("Update standings"):
        with st.spinner("Updating Schedule..."):
            update_week(week, season, game_type, sql_engine)

games = query_db(sql_engine, f"SELECT * FROM games WHERE season={season} AND week={week} AND game_type='{game_type}' ORDER BY date;")

teams = pd.DataFrame(query_db(sql_engine, f"SELECT * FROM teams;"))

st.write("")
st.write("")

col1, col2, col3, col4, col5 = st.columns([1,1,0.5,0.5, 0.5])
with col1:
    st.subheader("Home team")
with col2:
    st.subheader("Away team")
with col3:
    st.subheader("Scheduled")
with col4:
    st.subheader("Score")
with col5:
    st.subheader("Odds")
st.divider()

with open('streamlit/sources/nn_regressor.pkl', 'rb') as f:
    nn_regressor = dill.load(f)

for game in games:
    query = query_plays(game['game_id'])
    if int(game['game_status'])>1:
        plays = pd.DataFrame(query_db(sql_engine, query))
    col1, col2, col3, col4, col5 = st.columns([1,1,0.5,0.5, 0.5])
    with col1:
        st.subheader(teams.loc[teams['team_id']==game['home_team_id']]['name'].values[0])
    with col2:
        st.subheader(teams.loc[teams['team_id']==game['away_team_id']]['name'].values[0])
    with col3:
        game_date = pytz.utc.localize(game['date'])
        game_date_local = game_date.astimezone(get_localzone())

        if int(game['game_status'])==1:
            st.subheader(game_date_local)
        elif int(game['game_status'])==2:
            quarter = {1: "1st Qtr", 2: "2nd Qtr", 3: "3rd Qtr", 4: "4th Qtr", 5: "OT"}
            st.subheader(quarter[plays.iloc[-1]['quarter']])
        else:
            st.subheader("Final")

    with col4:
        if int(game['game_status'])>1:
            if int(game['game_status'])==2:
                score = "("+str(plays.iloc[-1]['homeScore'])+":"+str(plays.iloc[-1]['awayScore'])+")"
                st.markdown(
                    f"""<b><a href="/prediction?game={game['game_id']}" style="font-size: 1.6em; color: inherit;" target="_self">{score}</a></b>""",
                    unsafe_allow_html=True,
                )
            else:
                score = str(plays.iloc[-1]['homeScore'])+":"+str(plays.iloc[-1]['awayScore'])
                st.subheader(score)
    with col5:
        if int(game['game_status'])>1:
            probabilities = nn_regressor.predict(plays)[:,0]
            plot_win_probabilities(plays['totalTimeLeft'], probabilities, teams.loc[teams['team_id']==game['home_team_id']]['color'].values[0], teams.loc[teams['team_id']==game['away_team_id']]['color'].values[0], teams.loc[teams['team_id']==game['home_team_id']]['name'].values[0], teams.loc[teams['team_id']==game['away_team_id']]['name'].values[0])
        else:
            st.write("")
