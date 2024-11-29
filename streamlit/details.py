import streamlit as st

from sources.sql import query_db, create_sql_engine
sql_engine = create_sql_engine()

def list_teams():
    st.title("Teams List")
    teams = query_db(sql_engine, "SELECT team_id, name, location, logo FROM teams WHERE team_id NOT IN (-2, -1, 31, 32, 38)")
    for team in teams:
        st.markdown(
            f"""
            <a href="?page=Team&team_id={team['team_id']}" target="_self">
                <div style="display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #ccc;">
                    <img src="{team['logo']}" alt="Logo" style="height: 50px; margin-right: 20px;">
                    <div>
                        <b>{team['name']}</b><br>{team['location']}
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

# Team page
def team_page(team_id):
    team = query_db(sql_engine, "SELECT name, logo, color FROM teams WHERE team_id = :team_id", team_id=team_id)[0]
    st.markdown(
        f"""
        <div style="background-color: {team['color']}; padding: 20px; text-align: center; color: white;">
            <h1>{team['name']}</h1>
            <img src="{team['logo']}" alt="Logo" style="height: 100px;">
        </div>
        """,
        unsafe_allow_html=True,
    )
    players = query_db(sql_engine, 
        """
        SELECT players.player_id, CONCAT(players.firstName, ' ', players.lastName) AS 'name', positions.position_id, positions.abbreviation as 'positions', players.picture
        FROM players
        JOIN positions ON players.position_id = positions.position_id
        WHERE players.team_id = :team_id
        ORDER BY players.lastName
        """,
        team_id=team_id,
    )
    #st.write(players)
    col1, col2, col3, col4 = st.columns(4)
    columns = [col1, col2, col3, col4]
    player_i = 0
    for player in players:
        with columns[player_i%len(columns)]:
            st.markdown(
                f"""
                <a href="?page=Player&player_id={player['player_id']}" target="_self">
                    <div style="display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #ccc;">
                        <img src="{player['picture']}" alt="Player Picture" style="height: 100px; margin-right: 50px;">
                        <b>{player['name']}</b>
                    </div>
                </a>
                <a href="?page=Position&position_id={player['position_id']}" style="margin-left: 20px; color: white;" target="_self">{player['positions']}</a>
                """,
                unsafe_allow_html=True,
            )
        player_i += 1

# Position page
def position_page(position_id):
    position = query_db(sql_engine, "SELECT name FROM positions WHERE position_id = :position_id", position_id=position_id)[0]
    st.title(position['name'])
    players = query_db(sql_engine, 
        "SELECT player_id, CONCAT(players.firstName, ' ', players.lastName) AS name FROM players WHERE position_id = :position_id ORDER BY players.lastName", position_id=position_id
    )
    for player in players:
        st.markdown(
            f"""
            <a href="?page=Player&player_id={player['player_id']}" target="_self">
                <div>{player['name']}</div>
            </a>
            """,
            unsafe_allow_html=True,
        )

# Player page
def player_page(player_id):
    player = query_db(sql_engine, 
        f"""
        SELECT CONCAT(players.firstName, ' ', players.lastName) AS full_name, teams.team_id, teams.name AS team_name, positions.position_id, positions.name AS position_name,
               players.jersey, players.experience, playerstatuses.name AS status, players.picture, colleges.college_id, colleges.name AS college_name
        FROM players
        JOIN teams ON players.team_id = teams.team_id
        JOIN positions ON players.position_id = positions.position_id
        JOIN playerstatuses ON players.status_id = playerstatuses.status_id
        JOIN colleges ON players.college_id = colleges.college_id
        WHERE players.player_id = {player_id}
        """
    )[0]

        
    st.title(player['full_name'])
    col1, col2 = st.columns(2)
    with col1:
        st.image(player['picture'])
    with col2:
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")        
        st.write("")
        st.write("")
        st.write("")
        st.markdown(f"""Team: <a href="?page=Team&team_id={player['team_id']}" target="_self">{player['team_name']}</a>""", unsafe_allow_html=True)
        st.markdown(f"""Position: <a href="?page=Position&position_id={player['position_id']}" target="_self">{player['position_name']}</a>""", unsafe_allow_html=True)
        st.write(f"Jersey Number: {player['jersey']}")
        st.write(f"Years in NFL: {player['experience']}")
        st.write(f"Status: {player['status']}")
        st.markdown(f"""College: <a href="?page=College&college_id={player['college_id']}" target="_self">{player['college_name']}</a>""", unsafe_allow_html=True)

# College page
def college_page(college_id):
    college = query_db(sql_engine, "SELECT name, logo, mascot FROM colleges WHERE college_id = :college_id", college_id=college_id)[0]
    col1, col2 = st.columns(2)
    with col1:
        st.title(college['name'])
        st.image(college['logo'], caption=college['mascot'])
    with col2:
        st.write("Current players in the NFL:")
        players = query_db(sql_engine, "SELECT player_id, CONCAT(players.firstName, ' ', players.lastName) AS name FROM players WHERE college_id = :college_id ORDER BY players.lastName", college_id=college_id)
        for player in players:
            st.markdown(
                f"""
                <a href="?page=Player&player_id={player['player_id']}" target="_self">{player['name']}</a>
                """,
                unsafe_allow_html=True,
            )

# Routing based on URL parameters
if 'team_id' in st.query_params:
    team_page(st.query_params['team_id'])
elif 'position_id' in st.query_params:
    position_page(st.query_params['position_id'])
elif 'player_id' in st.query_params:
    player_page(st.query_params['player_id'])
elif 'college_id' in st.query_params:
    college_page(st.query_params['college_id'])
else:
    list_teams()
