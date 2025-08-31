import streamlit as st
import pandas as pd
import numpy as np
import dill

from datetime import datetime
import pytz
from tzlocal import get_localzone
from client_timezone import client_timezone

from sources.plots import plot_win_probabilities, plot_points
from sources.sql import create_sql_engine, get_current_week, query_db, update_week, update_full_schedule
from sources.long_queries import query_plays, query_week

sql_engine = create_sql_engine()

current_week, current_season, current_game_type = get_current_week()

@st.cache_resource(show_spinner=False)
def update_week_cached(week, season, game_type, _sql_engine):
    update_week(week, season, game_type, sql_engine)

with st.spinner("Updating Schedule..."):
    update_week_cached(current_week, current_season, current_game_type, sql_engine)
    
if "game_type" not in st.session_state:
    if current_game_type == "preseason":
        current_game_type = "regular-season"
        current_week = 1
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

if all([game['game_status'] == '3' for game in games]):
    choice = st.segmented_control("Which games to display", ["All games", "Top games of the week"], default="All games", selection_mode="single")
else:
    choice = "All games"

st.write("")
st.write("")

with open('streamlit/sources/nn_regressor.pkl', 'rb') as f:
    nn_regressor = dill.load(f)

if choice == "All games":
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

    user_timezone = client_timezone()
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
            game_date_local = game_date.astimezone(user_timezone).strftime("%Y-%m-%d %H:%M")

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
else:
    query = query_week(week, season, game_type)
    games_df = pd.DataFrame(query_db(sql_engine, query))

    def get_game_summary(df_game):
        final = df_game.iloc[-1]
        home_team = final['home_team']
        away_team = final['away_team']
        home_score = final['home_score']
        away_score = final['away_score']
        winner = home_team if home_score > away_score else away_team
        loser = away_team if winner == home_team else home_team

        # Get initial and min/max win probs
        initial_home_wp = df_game.iloc[0]['home_wp']
        min_home_wp = df_game['home_wp'].min()
        max_home_wp = df_game['home_wp'].max()
        avg_home_wp = df_game['home_wp'].mean()

        # Lead changes
        lead_changes = ((df_game['home_wp'] > 0.5) != (df_game['home_wp'].shift(1) > 0.5)).sum()

        # Find point when win prob flipped decisively
        if winner == home_team:
            wp_series = df_game['home_wp']
        else:
            wp_series = 1 - df_game['home_wp']
        underdog_moments = df_game[wp_series < 0.5]
        late_flip_time = underdog_moments['time_left'].min() if not underdog_moments.empty else None

        return {
            'game_id': final['game_id'],
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'winner': winner,
            'loser': loser,
            'score_diff': abs(home_score - away_score),
            'initial_home_wp': initial_home_wp,
            'winner_wp_avg': avg_home_wp if winner == home_team else 1 - avg_home_wp,
            'winner_wp_min': min_home_wp if winner == home_team else 1 - max_home_wp,
            'volatility': df_game['home_wp'].std(),
            'lead_changes': lead_changes,
            'late_flip_time': late_flip_time
        }

    # Process all games
    games = games_df['game_id'].unique()
    game_summaries = [get_game_summary(games_df.loc[games_df['game_id'] == gid].reset_index(drop=True)) for gid in games]
    summary_df = pd.DataFrame(game_summaries)

    # Category winners
    winners = {
        "Biggest Blowout": summary_df.sort_values('score_diff', ascending=False).iloc[0],
        "Biggest Upset": summary_df.assign(
            underdog_wp=lambda x: np.where(x['initial_home_wp'] < 0.5, x['initial_home_wp'], 1 - x['initial_home_wp'])
        ).sort_values('underdog_wp').iloc[0],
        "Biggest Domination": summary_df.sort_values('winner_wp_avg', ascending=False).iloc[0],
        "Biggest Comeback": summary_df.sort_values('winner_wp_min').iloc[0],
        "Most Volatile Game": summary_df.sort_values('volatility', ascending=False).iloc[0],
        "Most Lead Changes": summary_df.sort_values('lead_changes', ascending=False).iloc[0],
        "Latest Game-Winning Turnaround": summary_df[summary_df['late_flip_time'].notna()].sort_values('late_flip_time', ascending=True).iloc[0]
    }

    # Display Results
    for category, row in winners.items():
        st.subheader(f"\n🏅 {category}")
        st.write(f"   → Game: {row['home_team']} vs {row['away_team']}")
        st.write(f"   → Winner: {row['winner']} | Final Score: {row['home_score']} - {row['away_score']}")
        cols = st.columns(2)
        with cols[0]:
            plot_win_probabilities(
                games_df.loc[games_df['game_id'] == row['game_id'], 'time_left'],
                games_df.loc[games_df['game_id'] == row['game_id'], 'home_wp'],
                teams.loc[teams['name'] == row['home_team'], 'color'].values[0],
                teams.loc[teams['name'] == row['away_team'], 'color'].values[0],
                row['home_team'],
                row['away_team']
            )
        with cols[1]:
            plot_points(
                games_df.loc[games_df['game_id'] == row['game_id'], 'time_left'],
                games_df.loc[games_df['game_id'] == row['game_id'], 'home_score'],
                games_df.loc[games_df['game_id'] == row['game_id'], 'away_score'],
                teams.loc[teams['name'] == row['home_team'], 'color'].values[0],
                teams.loc[teams['name'] == row['away_team'], 'color'].values[0],
                row['home_team'],
                row['away_team']
            )
        st.divider()
