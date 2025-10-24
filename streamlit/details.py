import string

import pandas as pd
import pydeck as pdk
from sources.sql import create_sql_engine, get_players, query_db

import streamlit as st

sql_engine = create_sql_engine()


def list_teams() -> None:
    st.markdown(
        """
    <style>
    .stButton > button {
        width: 250px;
        height: 50px;
        background-color: #b0bcff;
        color: #00093a;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: white;
        color: #00093a
    }
    </style>
    <style>
    .image-border {
        display: inline-block;
        border: 5px solid #b0bcff;
        border-radius: 2px;
        padding: 0px;
    }
    </style>
""",
        unsafe_allow_html=True,
    )

    if "display_map" not in st.session_state:
        st.session_state["display_map"] = False
    if st.toggle("Display Map", value=st.session_state["display_map"]):
        st.session_state["display_map"] = True
        map_page()

    teams = query_db(
        sql_engine,
        "SELECT team_id, name, logo FROM teams WHERE team_id NOT IN (-2, -1, 31, 32, 38)",
    )
    for team_i, team in enumerate(teams):
        if team_i % 2 == 0:
            st.divider()
            cols = st.columns(2)

        with cols[team_i % 2]:
            col1, col2 = st.columns([1, 3])  # Layout for logo and details
            with col1:
                st.markdown(
                    f"""
                    <div class="image-border">
                        <img src="{team["logo"]}" alt="Team Logo" width="200">
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                st.write("")
                st.write("")
                st.write("")
                if st.button(f"{team['name']}", key=f"team_{team['team_id']}"):
                    st.session_state["chosen_id"] = team["team_id"]
                    st.rerun()


def team_page(team_id: int) -> None:
    st.markdown(
        """
    <style>
    .stButton > button {
        width: 150px;
        height: 50px;
        background-color: #b0bcff;
        color: #00093a;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: white;
        color: #00093a
    }
    </style>
""",
        unsafe_allow_html=True,
    )
    team = query_db(
        sql_engine,
        "SELECT name, logo, color FROM teams WHERE team_id = :team_id",
        team_id=team_id,
    )[0]

    st.markdown(
        f"""
        <div style="background-color: {team["color"]}; padding: 20px; text-align: center; color: white;">
            <h1>{team["name"]}</h1>
            <img src="{team["logo"]}" alt="Logo" style="height: 200px;">
        </div>
        """,
        unsafe_allow_html=True,
    )

    players = query_db(
        sql_engine,
        """
        SELECT players.player_id, CONCAT(players.firstName, ' ', players.lastName) AS name,
               positions.position_id, positions.name AS positions, players.picture
        FROM players
        JOIN positions ON players.position_id = positions.position_id
        WHERE players.team_id = :team_id
        ORDER BY players.lastName, players.firstName
        """,
        team_id=team_id,
    )

    columns = None
    for player_i, player in enumerate(players):
        if player_i % 4 == 0:
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            columns = [col1, col2, col3, col4]

        with columns[player_i % len(columns)]:
            cola, colb = st.columns(2)
            with cola:
                try:
                    st.image(player["picture"], width=150)
                except (TypeError, ValueError, OSError):
                    st.image(team["logo"], width=150)
            with colb:
                if st.button(player["name"], key=f"player_{player['player_id']}"):
                    st.session_state["chosen_id"] = player["player_id"]
                    st.session_state["chosen_tab"] = "Players"
                    st.rerun()
                if st.button(
                    player["positions"],
                    key=f"position_{player['position_id']}_player_{player['player_id']}",
                ):
                    st.session_state["chosen_id"] = player["position_id"]
                    st.session_state["chosen_tab"] = "Positions"
                    st.rerun()


def list_colleges() -> None:
    st.markdown(
        """
    <style>
    .stButton > button {
        width: 150px;
        height: 50px;
        background-color: #b0bcff;
        color: #00093a;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: white;
        color: #00093a
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("Colleges", anchor=False)

    alphabet = list(string.ascii_uppercase)
    selected_letter = st.segmented_control(
        "Filter by name (A-Z):",
        options=alphabet,
        default=None,
    )

    if selected_letter is None:
        colleges = query_db(
            sql_engine,
            "SELECT college_id, name FROM colleges ORDER BY name ASC",
        )
    else:
        colleges = query_db(
            sql_engine,
            "SELECT college_id, name FROM colleges WHERE name LIKE :selected_letters ORDER BY name ASC",
            selected_letter=f"{selected_letter}%",
        )

    cols = st.columns(5)

    for college_i, college in enumerate(colleges):
        with cols[college_i % 5]:
            if st.button(f"{college['name']}", key=f"college_{college['college_id']}"):
                st.session_state["chosen_id"] = college["college_id"]
                st.session_state["chosen_tab"] = "Colleges"
                st.rerun()


def list_positions() -> None:
    st.markdown(
        """
    <style>
    .stButton > button {
        width: 250px;
        height: 50px;
        background-color: #b0bcff;
        color: #00093a;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: white;
        color: #00093a
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("Positions", anchor=False)

    positions = query_db(
        sql_engine,
        "SELECT position_id, name, abbreviation FROM positions ORDER BY name ASC",
    )

    for position in positions:
        if st.button(
            f"{position['name']} ({position['abbreviation']})",
            key=f"position_{position['position_id']}",
        ):
            st.session_state["chosen_id"] = position["position_id"]
            st.session_state["chosen_tab"] = "Positions"
            st.rerun()


def list_players() -> None:
    st.markdown(
        """
    <style>
    .stButton > button {
        width: 150px;
        height: 50px;
        background-color: #b0bcff;
        color: #00093a;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: white;
        color: #00093a
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("Players", anchor=False)

    alphabet = list(string.ascii_uppercase)
    selected_letter = st.segmented_control(
        "Filter by last name (A-Z):",
        options=alphabet,
        default=None,
    )

    if selected_letter is None:
        players = query_db(
            sql_engine,
            """SELECT player_id, CONCAT(players.firstName, ' ', players.lastName) AS name
               FROM players
               WHERE team_id IS NOT NULL
               ORDER BY players.lastName, players.firstName""",
        )
    else:
        players = query_db(
            sql_engine,
            """SELECT player_id, CONCAT(players.firstName, ' ', players.lastName) AS name
               FROM players
               WHERE players.lastName LIKE :selected_letter
               AND team_id IS NOT NULL
               ORDER BY players.lastName, players.firstName""",
            selected_letter=f"{selected_letter}%",
        )

    cols = st.columns(5)

    for player_i, player in enumerate(players):
        with cols[player_i % 5]:
            if st.button(f"{player['name']}", key=f"player_{player['player_id']}"):
                st.session_state["chosen_id"] = player["player_id"]
                st.session_state["chosen_tab"] = "Players"
                st.rerun()


def position_page(position_id: int) -> None:
    st.markdown(
        """
    <style>
    .stButton > button {
        width: 150px;
        height: 50px;
        background-color: #b0bcff;
        color: #00093a;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: white;
        color: #00093a
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    position = query_db(
        sql_engine,
        "SELECT name FROM positions WHERE position_id = :position_id",
        position_id=position_id,
    )[0]
    st.title(position["name"], anchor=False)

    players = query_db(
        sql_engine,
        """SELECT player_id, CONCAT(players.firstName, ' ', players.lastName) AS name
           FROM players 
           WHERE position_id = :position_id
           AND team_id IS NOT NULL
           ORDER BY players.lastName, players.firstName""",
        position_id=position_id,
    )

    cols = st.columns(5)
    player_i = 0

    for player_i, player in enumerate(players):
        with cols[player_i % 5]:
            if st.button(f"{player['name']}", key=f"player_{player['player_id']}"):
                st.session_state["chosen_id"] = player["player_id"]
                st.session_state["chosen_tab"] = "Players"
                st.rerun()


# Player page
def player_page(player_id: int) -> None:
    st.markdown(
        """
    <style>
    .stButton > button {
        width: 200px;
        height: 50px;
        background-color: #b0bcff;
        color: #00093a;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: white;
        color: #00093a
    }
    </style>
""",
        unsafe_allow_html=True,
    )
    try:
        player = query_db(
            sql_engine,
            """
            SELECT CONCAT(players.firstName, ' ', players.lastName) AS full_name,
                teams.team_id, teams.name AS team_name,
                positions.position_id, positions.name AS position_name,
                players.jersey, players.experience, playerstatuses.name AS status,
                players.picture, colleges.college_id, colleges.name AS college_name
            FROM players
            JOIN teams ON players.team_id = teams.team_id
            JOIN positions ON players.position_id = positions.position_id
            JOIN playerstatuses ON players.status_id = playerstatuses.status_id
            JOIN colleges ON players.college_id = colleges.college_id
            WHERE players.player_id = :player_id
            """,
            player_id=player_id,
        )[0]
    except IndexError:
        st.error(f"Player {player_id} not found.")
        return

    st.title(player["full_name"], anchor=False)

    col1, col2 = st.columns(2)

    with col1:
        st.image(player["picture"])

    with col2:

        def render_label(label: str, value: str) -> None:
            cola, colb = st.columns([1, 3])
            with cola:
                st.write(label)
            with colb:
                st.write(value)

        def render_button(
            label: str,
            value: str,
            key: str,
            tab: str,
            id_val: int,
        ) -> None:
            cola, colb = st.columns([1, 3])
            with cola:
                st.write(label)
            with colb:
                if st.button(value, key=key):
                    st.session_state["chosen_id"] = id_val
                    st.session_state["chosen_tab"] = tab
                    st.rerun()

        st.write("")
        st.write("")
        render_button(
            "Team:",
            player["team_name"],
            f"team_{player['team_id']}",
            "Teams",
            player["team_id"],
        )
        render_button(
            "Position:",
            player["position_name"],
            f"position_{player['position_id']}",
            "Positions",
            player["position_id"],
        )
        render_label("**Jersey Number**:", str(player["jersey"]))
        render_label("**Years in NFL**:", str(player["experience"]))
        render_label("**Status**:", player["status"])
        render_button(
            "**College**:",
            player["college_name"],
            f"college_{player['college_id']}",
            "Colleges",
            player["college_id"],
        )


# College page
def college_page(college_id: int) -> None:
    st.markdown(
        """
    <style>
    .stButton > button {
        width: 200px;
        height: 50px;
        background-color: #b0bcff;
        color: #00093a;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: white;
        color: #00093a
    }
    </style>
""",
        unsafe_allow_html=True,
    )
    college = query_db(
        sql_engine,
        "SELECT name, logo, mascot FROM colleges WHERE college_id = :college_id",
        college_id=college_id,
    )[0]

    col1, col2 = st.columns(2)
    with col1:
        st.title(college["name"], anchor=False)
        st.image(college["logo"], caption=college["mascot"])

    with col2:
        st.write("Current players in the NFL:")
        players = query_db(
            sql_engine,
            """SELECT player_id, CONCAT(players.firstName, ' ', players.lastName) AS name
               FROM players
               WHERE college_id = :college_id
               AND team_id IS NOT NULL
               ORDER BY players.lastName, players.firstName""",
            college_id=college_id,
        )

        for player in players:
            if st.button(f"{player['name']}", key=f"player_{player['player_id']}"):
                st.session_state["chosen_id"] = player["player_id"]
                st.session_state["chosen_tab"] = "Players"
                st.rerun()


def map_page() -> None:
    teams = pd.DataFrame(
        query_db(
            sql_engine,
            "SELECT * FROM teams WHERE team_id NOT IN (-2, -1, 31, 32, 38)",
        ),
    )
    teams["lat"] = pd.to_numeric(teams["lat"], errors="coerce")
    teams["lon"] = pd.to_numeric(teams["lon"], errors="coerce")

    teams["icon_data"] = teams["logo"].apply(
        lambda url: {
            "url": url,
            "width": 128,
            "height": 128,
            "anchorY": 128,
        },
    )

    icon_layer = pdk.Layer(
        type="IconLayer",
        data=teams,
        get_icon="icon_data",
        get_position="[lon, lat]",
        size_scale=30,
        pickable=True,
        id="nfl-icons",
    )

    view_state = pdk.ViewState(
        latitude=teams["lat"].mean(),
        longitude=teams["lon"].mean(),
        zoom=3,
    )

    selection = st.pydeck_chart(
        pdk.Deck(
            # map_style="mapbox://styles/mapbox/dark-v11", # noqa: ERA001
            initial_view_state=view_state,
            layers=[icon_layer],
            tooltip={"text": "{name}"},
        ),
        on_select="rerun",
        key="nfl_icon_map",
    )

    if (
        isinstance(selection, dict)
        and "objects" in selection["selection"]
        and selection["selection"]["objects"]
    ):
        st.session_state["chosen_id"] = selection["selection"]["objects"]["nfl-icons"][
            0
        ]["team_id"]
        st.rerun()


if "chosen_tab" not in st.session_state:
    st.session_state["chosen_tab"] = "Teams"
if "chosen_id" not in st.session_state:
    st.session_state["chosen_id"] = None


def reset_navigation() -> None:
    st.session_state["chosen_id"] = None
    st.rerun()


tab = st.segmented_control(
    options=["Teams", "Players", "Colleges", "Positions"],
    label="Select a category",
    default=st.session_state["chosen_tab"],
)
if tab != st.session_state["chosen_tab"]:
    st.session_state["chosen_tab"] = tab
    st.session_state["chosen_id"] = None
    st.rerun()


if st.session_state["chosen_tab"] == "Teams":
    if st.session_state["chosen_id"] is None:
        list_teams()
    else:
        if st.button("Back to Teams List"):
            reset_navigation()
        team_page(st.session_state["chosen_id"])
        if st.session_state.get("roles", False) == "admin":
            st.divider()
            st.header("Admin settings", anchor=False)
            if st.button("Update all rosters"):
                with st.spinner("Updating rosters"):
                    get_players()
            if st.button("Update current roster"):
                with st.spinner("Updating roster"):
                    get_players(team_id=st.session_state["chosen_id"])


elif st.session_state["chosen_tab"] == "Players":
    if st.session_state["chosen_id"] is None:
        list_players()
    else:
        if st.button("Back to Players List"):
            reset_navigation()
        player_page(st.session_state["chosen_id"])

elif st.session_state["chosen_tab"] == "Positions":
    if st.session_state["chosen_id"] is None:
        list_positions()
    else:
        position_page(st.session_state["chosen_id"])
        if st.button("Back to Positions List"):
            reset_navigation()

elif st.session_state["chosen_tab"] == "Colleges":
    if st.session_state["chosen_id"] is None:
        list_colleges()
    else:
        if st.button("Back to Colleges List"):
            reset_navigation()
        college_page(st.session_state["chosen_id"])
