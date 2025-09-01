import streamlit as st

st.title("Date acquisition", anchor=False)

st.write("All tools with the exception of the LogoRecognizer rely mainly on the database from ESPN. For a brief explanation of the images used for training the LogoRecognizer, please refer to its tab in the 'ML/AI models' section.")

st.header("Data Source: ESPN", anchor=False)
st.write("The homepage of ESPN provides a wealth of historical sports data, especially for American football. Most of the data visible on their homepage is accessible through API calls. While using those calls is free for everyone, it is entirely undocumented. Therefore we had to rely on call urls collected by other users to perform our requests.")

st.subheader("Example API Calls", anchor=False)
st.write("Below are examples of API calls we used to gather specific data. Use the segmented control below to explore different API endpoints.")


# Example API Calls
api_calls = {
    "games": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={year}&seasontype={seasontype}&week={week}",
    "plays": "https://cdn.espn.com/core/nfl/playbyplay?xhr=1&gameId={game_id}",
    "probabilities": "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{game_id}/competitions/{game_id}/probabilities?limit=1000&page={page}",
    "teams": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}",
    "players": "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2024/teams/{team_id}/athletes?limit=200",
    "colleges": "http://sports.core.api.espn.com/v2/colleges/{college_id}?lang=en&region=us",
    "news": """https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=150
https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?team={team_id}""",
}

selected_endpoint = st.segmented_control(
    "Select an API category:",
    list(api_calls.keys()),
    default="games"
)
if selected_endpoint == None:
    pass
else:
    st.code(api_calls[selected_endpoint], language="python")

st.header("MySQL: Data Storage and Organization", anchor=False)
st.text("""Once the data was collected, it was stored in a MySQL database. The tables were carefully connected using primary and foreign keys to maintain relational integrity. This approach allowed us to efficiently query and analyze the data.

Below is a representation of the database schema we used:""")

# Placeholder for the database schema image
st.image("streamlit/images/sql.png", caption="Database Schema")

if st.toggle("Toggle python code for SQL database creation"):
    st.code("""
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Time, BigInteger, Text, text, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.types import Integer
            
sql_engine = create_engine(f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}"

metadata = MetaData()

players_table = Table(
    'players', metadata,
    Column('player_id', Integer, primary_key=True), 
    Column('team_id', Integer, ForeignKey('teams.team_id')),
    Column('firstName', String(100)),
    Column('lastName', String(100)),
    Column('weight', Float),
    Column('height', Float),
    Column('age', Integer, nullable=True),
    Column('link', String(255)),
    Column('country', String(100), nullable=True),
    Column('picture', String(255), nullable=True),
    Column('jersey', Integer, nullable=True),
    Column('position_id', Integer, ForeignKey('positions.position_id')),
    Column('experience', Integer),
    Column('active', Boolean),
    Column('status_id', Integer, ForeignKey('playerstatuses.status_id')),
    Column('college_id', Integer, ForeignKey('colleges.college_id'))
)

playerstatuses_table = Table(
    'playerstatuses', metadata,
    Column('status_id', Integer, primary_key=True),  
    Column('name', String(100))
)

teams_table = Table(
    'teams', metadata,
    Column('team_id', Integer, primary_key=True),  
    Column('abbreviation', String(10)),
    Column('name', String(255)),
    Column('location', String(255)),
    Column('color', String(50)),
    Column('logo', String(255)),
    Column('link', String(255))
)

colleges_table = Table(
    'colleges', metadata,
    Column('college_id', Integer, primary_key=True),  
    Column('name', String(255)),
    Column('abbreviation', String(10), nullable=True),
    Column('logo', String(255), nullable=True),
    Column('mascot', String(255), nullable=True)
)

positions_table = Table(
    'positions', metadata,
    Column('position_id', Integer, primary_key=True),  
    Column('name', String(100)),
    Column('abbreviation', String(10)),
    Column('parent', Integer, nullable=True),  # Nullable in case parent position is not specified
)

games_table = Table(
    'games', metadata,
    Column('game_id', Integer, primary_key=True),
    Column('date', DateTime(timezone=True)),
    Column('name', String(255)),
    Column('season', Integer),
    Column('game_type', String(100)),
    Column('week', Integer),
    Column('home_team_id', Integer, ForeignKey('teams.team_id')),
    Column('home_team_score', Integer),
    Column('away_team_id', Integer, ForeignKey('teams.team_id')),
    Column('away_team_score', Integer),
    Column('standing_home_overall_win', Integer),
    Column('standing_home_Home_win', Integer),
    Column('standing_home_Road_win', Integer),
    Column('standing_home_overall_loss', Integer),
    Column('standing_home_Home_loss', Integer),
    Column('standing_home_Road_loss', Integer),
    Column('standing_away_overall_win', Integer),
    Column('standing_away_Home_win', Integer),
    Column('standing_away_Road_win', Integer),
    Column('standing_away_overall_loss', Integer),
    Column('standing_away_Home_loss', Integer),
    Column('standing_away_Road_loss', Integer),
    Column('link', String(255)),
    Column('game_status', String(100)),
)

playtypes_table = Table(
    'playtypes', metadata,
    Column('playtype_id', Integer, primary_key=True),  
    Column('text', String(255)),  
    Column('abbreviation', String(10), nullable=True)
)

plays_table = Table(
    'plays', metadata,
    Column('play_id', BigInteger, primary_key=True),  
    Column('game_id', Integer, ForeignKey('games.game_id')),  
    Column('sequenceNumber', Integer),
    Column('homeScore', Integer),
    Column('awayScore', Integer),
    Column('quarter', Integer),
    Column('clock', Time),
    Column('offenseAtHome', Boolean),
    Column('down', Integer),
    Column('distance', Integer),
    Column('yardsToEndzone', Integer),
    Column('possessionChange', Boolean),
    Column('next_down', Integer),
    Column('next_distance', Integer),
    Column('next_yardsToEndzone', Integer),
    Column('playtype_id', Integer, ForeignKey('playtypes.playtype_id')),
    Column('description', Text),
    UniqueConstraint('game_id', 'sequenceNumber', name='uq_plays_game_sequence')
)

probabilities_table = Table(
    'probabilities', metadata,
    Column('proba_id', BigInteger, primary_key=True),  # Unique identifier
    Column('game_id', Integer, nullable=False),  # Game identifier
    Column('sequenceNumber', Integer, nullable=False),  # Sequence number
    Column('homeWinPercentage', Float, nullable=False),  # Probability of home win
    Column('awayWinPercentage', Float, nullable=False),  # Probability of away win
    Column('tiePercentage', Float, nullable=False),  # Probability of tie
    ForeignKeyConstraint(
        ['game_id', 'sequenceNumber'],  # Composite FK in probabilities
        ['plays.game_id', 'plays.sequenceNumber'],  # Composite key in plays
        name='fk_probabilities_plays'
    )
)

news_table = Table(
    'news', metadata,
    Column('news_id', Integer, primary_key=True),  # Index column as primary key
    Column('headline', String(255), nullable=False),
    Column('description', String(1000), nullable=False),
    Column('published', DateTime(timezone=True), nullable=False),
    Column('story', Text, nullable=False)
)

metadata.create_all(sql_engine)
            """)