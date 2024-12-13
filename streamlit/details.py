import streamlit as st
import string

from sources.sql import query_db, create_sql_engine
sql_engine = create_sql_engine()

def list_teams():
    st.markdown("""
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
""", unsafe_allow_html=True)
    teams = query_db(sql_engine, "SELECT team_id, name, logo FROM teams WHERE team_id NOT IN (-2, -1, 31, 32, 38)")
    team_i = 0
    for team in teams:
        if team_i%2 == 0:
            st.divider()
            cols = st.columns(2)

        with cols[team_i%2]:
            col1, col2 = st.columns([1, 3])  # Layout for logo and details
            with col1:
                st.markdown(
                    f"""
                    <div class="image-border">
                        <img src="{team['logo']}" alt="Team Logo" width="200">
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
        team_i += 1

def team_page(team_id):
    st.markdown("""
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
""", unsafe_allow_html=True)
    # Fetch team information
    team = query_db(sql_engine, "SELECT name, logo, color FROM teams WHERE team_id = :team_id", team_id=team_id)[0]
    
    # Display team header
    st.markdown(
        f"""
        <div style="background-color: {team['color']}; padding: 20px; text-align: center; color: white;">
            <h1>{team['name']}</h1>
            <img src="{team['logo']}" alt="Logo" style="height: 200px;">
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Fetch players on the team
    players = query_db(sql_engine, 
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

    # Display players in a grid
    columns = None
    player_i = 0
    for player in players:
        if player_i % 4 == 0:  # Start a new row every 4 players
            st.divider()  # Add a divider between rows
            col1, col2, col3, col4 = st.columns(4)  # Create a new set of columns
            columns = [col1, col2, col3, col4]

        with columns[player_i % len(columns)]:
            cola, colb = st.columns(2)
            with cola:
                st.image(player['picture'], width=150)
            with colb:
                if st.button(player['name'], key=f"player_{player['player_id']}"):
                    st.session_state["chosen_id"] = player['player_id']
                    st.session_state["chosen_tab"] = "Players"
                    st.rerun()
                if st.button(player['positions'], key=f"position_{player['position_id']}_player_{player['player_id']}"):
                    st.session_state["chosen_id"] = player['position_id']
                    st.session_state["chosen_tab"] = "Positions"
                    st.rerun()
        player_i += 1


def list_colleges():
    # Custom CSS for styling the buttons
    st.markdown("""
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
    """, unsafe_allow_html=True)

    st.title("Colleges")

    alphabet = list(string.ascii_uppercase)
    selected_letter = st.segmented_control("Filter by name (A-Z):", options=alphabet, default=None)

    if selected_letter == None:
        colleges = query_db(sql_engine, 
            "SELECT college_id, name FROM colleges ORDER BY name ASC"
        )
    else:
        colleges = query_db(sql_engine, 
            "SELECT college_id, name FROM colleges WHERE name LIKE :selected_letters ORDER BY name ASC", selected_letter=f"{selected_letter}%"
        )

    cols = st.columns(5)
    college_i = 0

    for college in colleges:
        with cols[college_i % 5]:
            if st.button(f"{college['name']}", key=f"college_{college['college_id']}"):
                st.session_state["chosen_id"] = college['college_id']
                st.session_state["chosen_tab"] = "Colleges"
                st.rerun()
        college_i += 1

def list_positions():
    # Custom CSS for styling the buttons
    st.markdown("""
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
    """, unsafe_allow_html=True)

    st.title("Positions")

    positions = query_db(sql_engine, 
        "SELECT position_id, name, abbreviation FROM positions ORDER BY name ASC"
    )

    for position in positions:
        if st.button(f"{position['name']} ({position['abbreviation']})", key=f"position_{position['position_id']}"):
            st.session_state["chosen_id"] = position['position_id']
            st.session_state["chosen_tab"] = "Positions"
            st.rerun()

def list_players():
    # Custom CSS for styling the buttons
    st.markdown("""
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
    """, unsafe_allow_html=True)

    # Query to get the position details
    st.title("Players")

    alphabet = list(string.ascii_uppercase)
    selected_letter = st.segmented_control("Filter by last name (A-Z):", options=alphabet, default=None)

    # Query to get players for this position
    if selected_letter == None:
        players = query_db(sql_engine, 
            "SELECT player_id, CONCAT(players.firstName, ' ', players.lastName) AS name FROM players ORDER BY players.lastName, players.firstName"
        )
    else:
        players = query_db(sql_engine, 
            "SELECT player_id, CONCAT(players.firstName, ' ', players.lastName) AS name FROM players WHERE players.lastName LIKE :selected_letter ORDER BY players.lastName, players.firstName", selected_letter=f"{selected_letter}%"
        )

    # Create 5 columns for displaying the players
    cols = st.columns(5)
    player_i = 0

    for player in players:
        with cols[player_i % 5]:
            # Display player name in a button, when clicked will show player page
            if st.button(f"{player['name']}", key=f"player_{player['player_id']}"):
                st.session_state["chosen_id"] = player['player_id']
                st.session_state["chosen_tab"] = "Players"
                st.rerun()
        player_i += 1


def position_page(position_id):
    # Custom CSS for styling the buttons
    st.markdown("""
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
    """, unsafe_allow_html=True)

    # Query to get the position details
    position = query_db(sql_engine, "SELECT name FROM positions WHERE position_id = :position_id", position_id=position_id)[0]
    st.title(position['name'])

    # Query to get players for this position
    players = query_db(sql_engine, 
        "SELECT player_id, CONCAT(players.firstName, ' ', players.lastName) AS name FROM players WHERE position_id = :position_id ORDER BY players.lastName, players.firstName", position_id=position_id
    )

    # Create 5 columns for displaying the players
    cols = st.columns(5)
    player_i = 0

    for player in players:
        with cols[player_i % 5]:
            # Display player name in a button, when clicked will show player page
            if st.button(f"{player['name']}", key=f"player_{player['player_id']}"):
                st.session_state["chosen_id"] = player['player_id']
                st.session_state["chosen_tab"] = "Players"
                st.rerun()
        player_i += 1


# Player page
def player_page(player_id):
    st.markdown("""
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
""", unsafe_allow_html=True)    
    player = query_db(sql_engine, 
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
        player_id=player_id
    )[0]

    # Set the page title to the player's full name
    st.title(player['full_name'])
    
    # Create two columns for the layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Display the player's picture
        st.image(player['picture'])
    
    with col2:
        st.write("")  
        st.write("")  
        cola, colb = st.columns([1,3])
        with cola:
            st.write("Team:")
        with colb:
            if st.button(f"{player['team_name']}", key=f"team_{player['team_id']}"):
                st.session_state["chosen_id"] = player['team_id']
                st.session_state["chosen_tab"] = "Teams"
                st.rerun()
        cola, colb = st.columns([1,3])
        with cola:
            st.write("Position:")
        with colb:
            if st.button(f"{player['position_name']}", key=f"position_{player['position_id']}"):
                st.session_state["chosen_id"] = player['position_id']
                st.session_state["chosen_tab"] = "Positions"
                st.rerun()
        cola, colb = st.columns([1,3])
        with cola:
            st.write(f"**Jersey Number**:")
        with colb:
            st.write(f"{player['jersey']}")
        cola, colb = st.columns([1,3])
        with cola:
            st.write(f"**Years in NFL**:")
        with colb:
            st.write(f"{player['experience']}")
        cola, colb = st.columns([1,3])
        with cola:
            st.write(f"**Status**:")
        with colb:
            st.write(f"{player['status']}")
        cola, colb = st.columns([1,3])
        with cola:
            st.write(f"**College**:")
        with colb:
            if st.button(f"{player['college_name']}", key=f"college_{player['college_id']}"):
                st.session_state["chosen_id"] = player['college_id']
                st.session_state["chosen_tab"] = "Colleges"
                st.rerun()




# College page
def college_page(college_id):
    st.markdown("""
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
""", unsafe_allow_html=True) 
    college = query_db(sql_engine, "SELECT name, logo, mascot FROM colleges WHERE college_id = :college_id", college_id=college_id)[0]
    
    col1, col2 = st.columns(2)
    with col1:
        st.title(college['name'])
        st.image(college['logo'], caption=college['mascot'])
    
    with col2:
        st.write("Current players in the NFL:")
        players = query_db(sql_engine, 
            "SELECT player_id, CONCAT(players.firstName, ' ', players.lastName) AS name FROM players WHERE college_id = :college_id ORDER BY players.lastName, players.firstName", 
            college_id=college_id
        )
        
        # Create a button for each player and set session state to navigate
        for player in players:
            if st.button(f"{player['name']}", key=f"player_{player['player_id']}"):
                st.session_state["chosen_id"] = player['player_id']
                st.session_state["chosen_tab"] = "Players"
                st.rerun()


# Initialize session state variables
if "chosen_tab" not in st.session_state:
    st.session_state["chosen_tab"] = "Teams"
if "chosen_id" not in st.session_state:
    st.session_state["chosen_id"] = None

# Navigation reset helper
def reset_navigation():
    st.session_state["chosen_id"] = None
    st.rerun()

# Tab selection
tab = st.segmented_control(
    options=["Teams", "Players", "Colleges", "Positions"],
    label="Select a category",
    default=st.session_state["chosen_tab"]
)
if not tab == st.session_state["chosen_tab"]:
    st.session_state["chosen_tab"] = tab
    st.session_state["chosen_id"] = None
    st.rerun()



# Tab-specific logic
if st.session_state["chosen_tab"] == "Teams":
    if st.session_state["chosen_id"] is None:
        list_teams()
    else:
        if st.button("Back to Teams List"):
            reset_navigation()
        team_page(st.session_state["chosen_id"])



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
