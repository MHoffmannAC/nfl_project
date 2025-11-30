import numpy as np
import pandas as pd
import pytz
from client_timezone import client_timezone
from PIL import Image
from time import sleep
from streamlit_image_comparison import image_comparison

from sources.sql import (
    create_sql_engine,
    get_current_week,
    get_news,
    get_players,
    query_db,
    update_full_schedule,
    update_week,
)

import streamlit as st

sql_engine = create_sql_engine()
week, season, game_type = get_current_week()
if "user_timezone" not in st.session_state:
    st.session_state["user_timezone"] = client_timezone()
    st.session_state["user_timezone_rerun"] = True
elif st.session_state.get("user_timezone_rerun", False):
    st.session_state["user_timezone"] = client_timezone()
    st.session_state["user_timezone_rerun"] = False


@st.fragment
def games_tile():
    st.header("Schedule")
    games = query_db(
        sql_engine,
        "SELECT name, date, game_status FROM games WHERE season=:season AND week=:week AND game_type=:game_type ORDER BY date;",
        season=int(season),
        week=int(week),
        game_type=str(game_type),
    )
    games_df = pd.DataFrame(games)
    games_df["date"] = (
        games_df["date"]
        .dt.tz_localize('UTC')
        .dt.tz_convert(st.session_state["user_timezone"])
        .dt.strftime("%Y-%m-%d %H:%M")
    )
    st.dataframe(games_df, hide_index=True)
    cola, colb, colc = st.columns([1,1.3,0.8])
    with cola:
        st.button("Update current week", on_click=update_week, args=(week, season, game_type, sql_engine))
    with colb:
        if st.button("Update current week (repeated)"):
            st.error("Auto-update running!")
            while True:
                update_week(week, season, game_type, sql_engine)
                sleep(60)
    with colc:
        st.button("Update full schedule", on_click=update_full_schedule, args=(season, sql_engine))


@st.fragment
def news_tile():
    st.header("News")
    news = query_db(
        sql_engine,
        "SELECT headline, published FROM news WHERE published >= NOW() - INTERVAL 7 DAY ORDER BY published DESC LIMIT 20;",
    )
    st.dataframe(
        pd.DataFrame(news),
        hide_index=True,
    )
    st.button("Fetch latest news", on_click=get_news, args=(sql_engine,))
    
@st.fragment
def chat_tile():
    st.header("Chat")
    chat = query_db(
        sql_engine,
        "SELECT timestamp AS time, room_name AS room, username AS user, message_text AS text FROM chat ORDER BY timestamp DESC LIMIT 20;",
    )
    st.dataframe(
        pd.DataFrame(chat),
        hide_index=True,
    )

@st.cache_resource(show_spinner=False)
def _download_logos(num_images) -> list[dict]:
    return query_db(
        sql_engine,
        "SELECT logo_id, image, team_id FROM logos ORDER BY logo_id DESC LIMIT :num_images;",
        num_images=num_images,
    )

@st.fragment
def logos_tile(num_images: int = 8):
    st.header("Logos")
    logos = _download_logos(num_images)
    teams_db = query_db(sql_engine, "SELECT team_id, name, logo FROM teams;")
    teams_dict = {
        team["team_id"]: {"name": team["name"], "logo": team["logo"]}
        for team in teams_db
    }
    cols = st.columns(4)
    for idx, logo in enumerate(logos):
        with cols[idx % 4]:
            array = np.fromstring(
                logo["image"].replace("[", "").replace("]", ""),
                sep=" ",
            ).reshape(400, 400, 3)
            array = (array * 255).astype(np.uint8)
            image_comparison(
                img1=Image.fromarray(array, "RGB"),
                img2=teams_dict[logo["team_id"]]["logo"],
                width=250,
                show_labels=False,
            )

@st.fragment
def feedback_tile():
    st.header("Feedback")
    feedback = query_db(
        sql_engine,
        "SELECT * FROM feedbacks ORDER BY feedback_id DESC LIMIT 20;",
    )
    st.dataframe(
        pd.DataFrame(feedback),
        hide_index=True,
    )
    
@st.fragment
def user_tile():
    st.header("Users")
    user = query_db(
        sql_engine,
        "SELECT * FROM users ORDER BY user_id DESC LIMIT 20;",
    )
    st.dataframe(
        pd.DataFrame(user),
        hide_index=True,
    )

st.title("Admin Board", anchor=False)
st.divider()

col1, _, col2 = st.columns([1,0.2,1], gap = "large")
with col1:            
    games_tile()
with col2:
    news_tile()

st.divider()

col1, _, col2 = st.columns([1,0.2,1], gap = "large")
with col1:
    chat_tile()
with col2:
    logos_tile(8)

st.divider()

col1, col2 = st.columns(2, gap = "large")
with col1:
    feedback_tile()
with col2:
    user_tile()

st.divider()

if st.button("Update all rosters"):
    with st.spinner("Updating rosters"):
        get_players()