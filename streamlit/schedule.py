from pathlib import Path

import dill
import numpy as np
import pandas as pd
import pytz
from client_timezone import client_timezone
from sources.long_queries import query_plays, query_week
from sources.plots import plot_points, plot_win_probabilities
from sources.socialmedia import generate_game_stats_posts, generate_top_games_posts
from sources.sql import (
    create_sql_engine,
    get_current_week,
    query_db,
    update_full_schedule,
    update_running_game,
    update_week,
)
from sqlalchemy.engine import Engine

import streamlit as st

sql_engine = create_sql_engine()
THRESHOLD = 0.5
SCHEDULED_GAME = 1
RUNNING_GAME = 2
FINISHED_GAME = 3

current_week, current_season, current_game_type = get_current_week()

if "user_timezone" not in st.session_state:
    st.session_state["user_timezone"] = client_timezone()
    st.session_state["user_timezone_rerun"] = True
elif st.session_state.get("user_timezone_rerun", False):
    st.session_state["user_timezone"] = client_timezone()
    st.session_state["user_timezone_rerun"] = False


st.markdown(
    """
    <style>
        /* Match outer container classes like 'st-key-reload-...' */
        div[class*="st-key-reload"] button {
            border: none !important;
            padding: 4px 0 2px 0 !important;  /* Top padding adjusted */
            background: transparent !important;
            color: inherit !important;
            cursor: pointer;
            line-height: 1.4 !important; /* Adjust line height */
        }

        div[class*="st-key-reload"] button:hover {
            background-color: transparent !important;
            color: inherit !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)


def _load_game(game_id: int) -> dict:
    game = query_db(
        sql_engine,
        "SELECT * FROM games WHERE game_id=:game_id;",
        game_id=game_id,
    )[0]
    if st.session_state.get("update_schedule", False):
        with st.spinner(""):
            update_running_game(game["game_id"], sql_engine, update_status=True)
            game = query_db(
                sql_engine,
                "SELECT * FROM games WHERE game_id=:game_id;",
                game_id=game_id,
            )[0]
    return query_db(
        sql_engine,
        "SELECT * FROM games WHERE game_id=:game_id;",
        game_id=game_id,
    )[0]


def _render_reload_button(
    col: st.delta_generator.DeltaGenerator,
    game_id: int,
    game: dict,
) -> None:
    with col:
        if int(game["game_status"]) not in [SCHEDULED_GAME, FINISHED_GAME]:  # noqa: SIM102
            if st.button(":material/sync:", key=f"reload-{game_id}"):
                with st.spinner(""):
                    update_running_game(game_id, sql_engine, update_status=True)


def _render_team_names(
    col1: st.delta_generator.DeltaGenerator,
    col2: st.delta_generator.DeltaGenerator,
    game: dict,
) -> None:
    with col1:
        st.subheader(
            teams.loc[teams["team_id"] == game["home_team_id"], "name"].to_numpy()[0],
        )
    with col2:
        st.subheader(
            teams.loc[teams["team_id"] == game["away_team_id"], "name"].to_numpy()[0],
        )


def _get_plays_if_running(game: dict) -> pd.DataFrame | None:
    if int(game["game_status"]) > 1:
        query = query_plays(game["game_id"])
        return pd.DataFrame(query_db(sql_engine, query))
    return None


def _render_game_time(
    col: st.delta_generator.DeltaGenerator,
    game: dict,
    plays: pd.DataFrame | None,
) -> None:
    with col:
        game_date = pytz.utc.localize(game["date"])
        game_date_local = game_date.astimezone(
            st.session_state["user_timezone"],
        ).strftime(
            "%Y-%m-%d %H:%M",
        )
        status = int(game["game_status"])

        if status == SCHEDULED_GAME:
            st.subheader(game_date_local)
        elif status == RUNNING_GAME and plays is not None and not plays.empty:
            quarter = {
                1: "1st Qtr",
                2: "2nd Qtr",
                3: "3rd Qtr",
                4: "4th Qtr",
                5: "OT",
            }
            st.subheader(quarter[plays.iloc[-1]["quarter"]])
        elif status == FINISHED_GAME:
            st.subheader("Final")
        else:
            st.subheader("-")


def _render_score(
    col: st.delta_generator.DeltaGenerator,
    game: dict,
    plays: pd.DataFrame | None,
) -> None:
    with col:
        status = int(game["game_status"])
        if status > 1 and plays is not None and not plays.empty:
            if status == RUNNING_GAME:
                score = f"({plays.iloc[-1]['homeScore']}:{plays.iloc[-1]['awayScore']})"
                st.markdown(
                    f'<b><a href="/prediction?game={game["game_id"]}" style="font-size:1.6em;color:inherit;" target="_self">{score}</a></b>',
                    unsafe_allow_html=True,
                )
            else:
                score = f"{plays.iloc[-1]['homeScore']}:{plays.iloc[-1]['awayScore']}"
                st.subheader(score)


def _render_win_prob(
    col: st.delta_generator.DeltaGenerator,
    game: dict,
    plays: pd.DataFrame | None,
) -> None:
    with col:
        if plays is not None and not plays.empty:
            probabilities = nn_regressor.predict(plays)[:, 0]
            plot_win_probabilities(
                plays["totalTimeLeft"],
                probabilities,
                teams.loc[
                    teams["team_id"] == game["home_team_id"],
                    "color",
                ].to_numpy()[0],
                teams.loc[
                    teams["team_id"] == game["away_team_id"],
                    "color",
                ].to_numpy()[0],
                teams.loc[
                    teams["team_id"] == game["home_team_id"],
                    "name",
                ].to_numpy()[0],
                teams.loc[
                    teams["team_id"] == game["away_team_id"],
                    "name",
                ].to_numpy()[0],
            )
        else:
            st.write("")


@st.fragment
def display_game(game_id: int) -> None:
    game = _load_game(game_id)

    col0, col1, col2, col3, col4, col5 = st.columns([1, 1, 0.5, 0.1, 0.5, 0.5])

    _render_team_names(col0, col1, game)
    plays = _get_plays_if_running(game)
    _render_reload_button(col3, game_id, game)
    _render_game_time(col2, game, plays)
    _render_score(col4, game, plays)
    _render_win_prob(col5, game, plays)


@st.cache_resource(show_spinner=False)
def update_week_cached(
    week: int,
    season: int,
    game_type: str,
    _sql_engine: Engine,
) -> None:
    update_week(week, season, game_type, sql_engine)


if "update_schedule" not in st.session_state:
    st.session_state["update_schedule"] = False

if "game_type" not in st.session_state:
    if current_game_type == "preseason":
        current_game_type = "regular-season"
        current_week = 1
    st.session_state["game_type"] = current_game_type

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


st.title("Schedule")

col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    all_seasons = [
        i["season"]
        for i in query_db(
            sql_engine,
            "SELECT Distinct(season) FROM games ORDER BY season DESC;",
        )
    ]
    season = st.selectbox(
        "Season",
        options=all_seasons,
        index=all_seasons.index(current_season),
    )
if st.session_state.get("roles", False) == "admin":
    with col3:
        if st.button("Update all season standings"):
            with st.spinner("Updating full Schedule..."):
                update_full_schedule(season, sql_engine)

col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    game_type = st.radio(
        "Game Type",
        ["Regular", "Postseason"],
        index=0 if st.session_state["game_type"] == "regular-season" else 1,
        horizontal=True,
    )

    game_type = "regular-season" if game_type == "Regular" else "post-season"

    if st.session_state["game_type"] != game_type:
        st.session_state["game_type"] = game_type
        st.rerun()

    week_mapping = {"SuperBowl": 5, "ConfChamp": 3, "DivRound": 2, "WildCard": 1}
    inverse_week_mapping = {v: k for k, v in week_mapping.items()}
    if game_type == "regular-season":
        week_options = list(range(1, 19))
        week = st.selectbox(
            "Week",
            options=week_options,
            index=week_options.index(current_week),
        )
    else:
        week_options = ["SuperBowl", "ConfChamp", "DivRound", "WildCard"]
        week = st.selectbox(
            "Week",
            options=week_options,
            index=week_options.index(inverse_week_mapping[current_week]),
        )

    if isinstance(week, str):
        week = week_mapping[week]
with col3:
    if st.button("Update all standings"):
        st.session_state["update_schedule"] = True
        st.rerun()

games = query_db(
    sql_engine,
    "SELECT * FROM games WHERE season=:season AND week=:week AND game_type=:game_type ORDER BY date;",
    season=int(season),
    week=int(week),
    game_type=str(game_type),
)
teams = pd.DataFrame(
    query_db(
        sql_engine,
        "SELECT * FROM teams WHERE team_id NOT IN (-2, -1, 31, 32, 38);",
    ),
)

if all(game["game_status"] == "3" for game in games):
    choice = st.segmented_control(
        "Which games to display",
        ["All games", "Top games of the week"],
        default="All games",
        selection_mode="single",
    )
else:
    choice = "All games"

st.write("")
st.write("")

with Path("streamlit/sources/nn_regressor.pkl").open("rb") as f:
    nn_regressor = dill.load(f)  # noqa: S301 # TODO replace with keras load

if choice == "All games":
    col0, col1, col2, col3, col4, col5 = st.columns([1, 1, 0.5, 0.1, 0.5, 0.5])
    with col0:
        st.markdown(
            "<h3 style='text-decoration: underline;'>Home Team</h3>",
            unsafe_allow_html=True,
        )
    with col1:
        st.markdown(
            "<h3 style='text-decoration: underline;'>Away Team</h3>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<h3 style='text-decoration: underline;'>Scheduled</h3>",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            "<h3 style='text-decoration: underline;'>Score</h3>",
            unsafe_allow_html=True,
        )
    with col5:
        st.markdown(
            "<h3 style='text-decoration: underline;'>Odds</h3>",
            unsafe_allow_html=True,
        )
    st.divider()

    game_ids = [game["game_id"] for game in games]
    for game_id in game_ids:
        display_game(game_id)

    all_team_ids = set(teams["team_id"])
    playing_team_ids = set()
    for game in games:
        playing_team_ids.add(game["home_team_id"])
        playing_team_ids.add(game["away_team_id"])
    bye_team_ids = all_team_ids - playing_team_ids

    if bye_team_ids:
        bye_teams = (
            teams.loc[teams["team_id"].isin(bye_team_ids), "name"]
            .sort_values()
            .to_list()
        )
        st.divider()
        st.markdown(
            "<h2 style='text-decoration: underline;'>Bye Week Teams</h2>",
            unsafe_allow_html=True,
        )
        for team in bye_teams:
            st.subheader(team)

    if st.session_state.get("roles", False) == "admin":  # noqa: SIM102
        if st.button("Generate Social Media Posts"):
            generate_game_stats_posts(season, week, games, teams)
else:
    query = query_week(week, season, game_type)
    games_df = pd.DataFrame(query_db(sql_engine, query))

    def get_game_summary(df_game: pd.DataFrame) -> dict[str, object]:
        final = df_game.iloc[-1]
        home_team = final["home_team"]
        away_team = final["away_team"]
        home_score = final["home_score"]
        away_score = final["away_score"]
        winner = (
            " Tie "
            if home_score == away_score
            else (home_team if home_score > away_score else away_team)
        )
        loser = (
            " Tie "
            if winner == " Tie "
            else (away_team if winner == home_team else home_team)
        )

        # Get initial and min/max win probs
        initial_home_wp = df_game.iloc[0]["home_wp"]
        min_home_wp = df_game["home_wp"].min()
        max_home_wp = df_game["home_wp"].max()
        avg_home_wp = df_game["home_wp"].mean()

        # Lead changes
        lead_changes = (
            (df_game["home_wp"] > THRESHOLD)
            != (df_game["home_wp"].shift(1) > THRESHOLD)
        ).sum()

        # Find point when win prob flipped decisively
        if winner == home_team:
            wp_series = df_game["home_wp"]
        else:
            wp_series = 1 - df_game["home_wp"]
        underdog_moments = df_game[wp_series < THRESHOLD]
        late_flip_time = (
            underdog_moments["time_left"].min() if not underdog_moments.empty else None
        )

        return {
            "game_id": final["game_id"],
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "winner": winner,
            "loser": loser,
            "score_diff": abs(home_score - away_score),
            "total_score": home_score + away_score,
            "initial_home_wp": initial_home_wp,
            "winner_wp_avg": avg_home_wp if winner == home_team else 1 - avg_home_wp,
            "winner_wp_min": min_home_wp if winner == home_team else 1 - max_home_wp,
            "volatility": df_game["home_wp"].std(),
            "lead_changes": lead_changes,
            "late_flip_time": late_flip_time,
        }

    # Process all games
    games = games_df["game_id"].unique()
    game_summaries = [
        get_game_summary(
            games_df.loc[games_df["game_id"] == gid].reset_index(drop=True),
        )
        for gid in games
    ]
    summary_df = pd.DataFrame(game_summaries)

    # upsets
    summary_df = summary_df.assign(
        underdog_wp=np.where(
            summary_df["initial_home_wp"] < THRESHOLD,
            summary_df["initial_home_wp"],
            1 - summary_df["initial_home_wp"],
        ),
        underdog_team=np.where(
            summary_df["initial_home_wp"] < THRESHOLD,
            summary_df["home_team"],
            summary_df["away_team"],
        ),
    )
    upsets = summary_df[summary_df["winner"] == summary_df["underdog_team"]]

    # Category winners
    winners = {
        "Biggest Blowout": summary_df.sort_values("score_diff", ascending=False).iloc[
            0
        ],
        "Biggest Shutout": summary_df[
            summary_df["score_diff"] == summary_df["total_score"]
        ]
        .sort_values("score_diff", ascending=False)
        .iloc[0]
        if not summary_df[summary_df["score_diff"] == summary_df["total_score"]].empty
        else None,
        "Closest Game": summary_df.sort_values("score_diff").iloc[0],
        "Highest Scoring Game": summary_df.sort_values(
            "total_score",
            ascending=False,
        ).iloc[0],
        "Lowest Scoring Game": summary_df.sort_values("total_score").iloc[0],
        "Biggest Domination": summary_df.sort_values(
            "winner_wp_avg",
            ascending=False,
        ).iloc[0],
        "Biggest Upset": upsets.sort_values("underdog_wp").iloc[0]
        if not upsets.empty
        else None,
        "Biggest Comeback": summary_df.loc[summary_df["winner"] != " Tie ", :]
        .sort_values("winner_wp_min")
        .iloc[0],
        "Latest Comeback": summary_df.loc[
            (summary_df["winner"] != " Tie ") & (summary_df["late_flip_time"].notna())
        ]
        .sort_values("late_flip_time", ascending=True)
        .iloc[0],
        "Most Volatile Game": summary_df.sort_values(
            "volatility",
            ascending=False,
        ).iloc[0],
        "Most Lead Changes": summary_df.sort_values(
            "lead_changes",
            ascending=False,
        ).iloc[0],
    }

    # Display Results
    for category, row in winners.items():
        if row is None:
            st.subheader(f"\n🏅   No {category.split(' ')[1].lower()} games this week")
            st.divider()
            continue
        st.subheader(f"\n🏅 {category}")
        st.write(f"   → Game: {row['home_team']} vs {row['away_team']}")
        st.write(
            f"   → Winner: {row['winner']} | Final Score: {row['home_score']} - {row['away_score']}",
        )
        cols = st.columns(2)
        with cols[0]:
            plot_win_probabilities(
                games_df.loc[games_df["game_id"] == row["game_id"], "time_left"],
                games_df.loc[games_df["game_id"] == row["game_id"], "home_wp"],
                teams.loc[teams["name"] == row["home_team"], "color"].to_numpy()[0],
                teams.loc[teams["name"] == row["away_team"], "color"].to_numpy()[0],
                row["home_team"],
                row["away_team"],
            )
        with cols[1]:
            plot_points(
                games_df.loc[games_df["game_id"] == row["game_id"], "time_left"],
                games_df.loc[games_df["game_id"] == row["game_id"], "home_score"],
                games_df.loc[games_df["game_id"] == row["game_id"], "away_score"],
                teams.loc[teams["name"] == row["home_team"], "color"].to_numpy()[0],
                teams.loc[teams["name"] == row["away_team"], "color"].to_numpy()[0],
                row["home_team"],
                row["away_team"],
            )
        st.divider()

    if st.session_state.get("roles", False) == "admin":  # noqa: SIM102
        if st.button("Generate Social Media Posts"):
            generate_top_games_posts(winners, season, week, games_df, teams)

st.session_state["update_schedule"] = False
