import streamlit as st
import requests
import pandas as pd

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Time, BigInteger, Text, text, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.types import Integer
from bs4 import BeautifulSoup

def create_sql_engine(noDB=False):
    if noDB:
        sql_engine = create_engine(f"mysql+pymysql://avnadmin:{st.secrets['aiven_pwd']}@mysql-nfl-mhoffmann-nfl.b.aivencloud.com:10448", pool_size=20, max_overflow=50)
    else:
        sql_engine = create_engine(f"mysql+pymysql://avnadmin:{st.secrets['aiven_pwd']}@mysql-nfl-mhoffmann-nfl.b.aivencloud.com:10448/nfl", pool_size=20, max_overflow=50)
    return sql_engine

def initialize_database(sql_engine):
    metadata = MetaData()

    users_table = Table(
        'users', metadata,
        Column('user_id', Integer, primary_key=True, autoincrement=True),
        Column('user_name', String(100), nullable=False),
        Column('first_name', String(100), nullable=True),
        Column('last_name', String(100), nullable=True),
        Column('email', String(255), nullable=False),
        Column('password', String(255), nullable=False),
        Column('roles', String(255), nullable=True)
    )

    # Table for the player data (index: player_id -> primary key)
    players_table = Table(
        'players', metadata,
        Column('player_id', Integer, primary_key=True),  # Set index as primary key
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

    # Table for the status data (index: status_id -> primary key)
    playerstatuses_table = Table(
        'playerstatuses', metadata,
        Column('status_id', Integer, primary_key=True),  # Set index as primary key
        Column('name', String(100))
    )

    # Table for the team info data (index: team_id -> primary key)
    teams_table = Table(
        'teams', metadata,
        Column('team_id', Integer, primary_key=True),  # Set index as primary key
        Column('abbreviation', String(10)),
        Column('name', String(255)),
        Column('location', String(255)),
        Column('color', String(50)),
        Column('logo', String(255)),
        Column('link', String(255))
    )

    # Table for the college data (index: college_id -> primary key)
    colleges_table = Table(
        'colleges', metadata,
        Column('college_id', Integer, primary_key=True),  # Set index as primary key
        Column('name', String(255)),
        Column('abbreviation', String(10), nullable=True),
        Column('logo', String(255), nullable=True),
        Column('mascot', String(255), nullable=True)
    )

    # Table for the position data (index: position_id -> primary key)
    positions_table = Table(
        'positions', metadata,
        Column('position_id', Integer, primary_key=True),  # Set index as primary key
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

def get_existing_ids(sql_engine, table, id_column):
    result = sql_engine.connect().execute(text(f"SELECT {id_column} FROM {table}"))
    df = pd.DataFrame(result.fetchall(), columns=[id_column])
    if df.empty:
        return set()  # Return an empty set if no rows are found
    return set(df[id_column].tolist())

def append_new_rows(dataframe, table, sql_engine, id_column):
    existing_ids_set = get_existing_ids(sql_engine, table, id_column)
    if not existing_ids_set:  # If there are no existing IDs in the SQL table
        dataframe.to_sql(table, con=sql_engine, if_exists='append', index=True, index_label=id_column)
    else:
        new_rows = dataframe[~dataframe.index.isin(existing_ids_set)]
        new_rows.to_sql(table, con=sql_engine, if_exists='append', index=True, index_label=id_column)

def query_db(sql_engine, query, **params):
    with sql_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

def load_game_data(events, sql_engine, asDataFrame=False, checkExistence=False):

    games_in_db =  list(get_existing_ids(sql_engine, 'games', 'game_id'))

    new_games = []

    for game_data in events:
        if (not checkExistence)or(not (int(game_data.get('id', None)) in games_in_db)):
            game = {}
            game['game_id'] = game_data.get('id', None)
            game['date'] = game_data.get('date', None)
            game['name'] = game_data.get('name', None)
            game['season'] = game_data.get('season', {}).get('year', None)
            game['game_type'] = game_data.get('season', {}).get('slug', None)
            game['week'] = game_data.get('week', {}).get('number', None)
            if game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('homeAway', None) == "home":
                game['home_team_id'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('team', {}).get('id', None)
                game['home_team_score'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('score', None)
                for i in range(3):
                    standing = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('records', [{},{},{}])[i].get('name', '')
                    if not standing=='':
                        game['standing_home_'+standing+'_win'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('records', [{},{},{}])[i].get('summary', [None])[0]
                        game['standing_home_'+standing+'_loss'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('records', [{},{},{}])[i].get('summary', [None])[-1]

                game['away_team_id'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('team', {}).get('id', None)
                game['away_team_score'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('score', None)
                for i in range(3):
                    standing = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('records', [{},{},{}])[i].get('name', '')
                    if not standing=='':
                        game['standing_away_'+standing+'_win'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('records', [{},{},{}])[i].get('summary', [None])[0]
                        game['standing_away_'+standing+'_loss'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('records', [{},{},{}])[i].get('summary', [None])[-1]

            else:
                game['home_team_id'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('team', {}).get('id', None)
                game['home_team_abr'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('team', {}).get('abbreviation', None)
                game['home_team_score'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('score', None)
                for i in range(3):
                    standing = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('records', [{},{},{}])[i].get('name', '')
                    if not standing=='':
                        game['standing_home_'+standing+'_win'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('records', [{},{},{}])[i].get('summary', [None])[0]
                        game['standing_home_'+standing+'_loss'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[1].get('records', [{},{},{}])[i].get('summary', [None])[-1]
                    
                game['away_team_id'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('team', {}).get('id', None)
                game['away_team_abr'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('team', {}).get('abbreviation', None)
                game['away_team_score'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('score', None)
                for i in range(3):
                    standing = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('records', [{},{},{}])[i].get('name', '')
                    if not standing=='':
                        game['standing_away_'+standing+'_win'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('records', [{},{},{}])[i].get('summary', [None])[0]
                        game['standing_away_'+standing+'_loss'] = game_data.get('competitions', [{}])[0].get('competitors', [{},{}])[0].get('records', [{},{},{}])[i].get('summary', [None])[-1]
            game['link'] = game_data.get('links', [{}])[0].get('href', None)
            game['game_status'] = game_data.get('status', {}).get('type', {}).get('id', None)
            new_games.append(game)

    if(asDataFrame):
        games_df = pd.DataFrame(new_games)
        games_df['game_id'] = games_df['game_id'].astype('Int64')
        games_df['home_team_id'] = games_df['home_team_id'].astype('Int64')
        games_df['home_team_score'] = games_df['home_team_score'].astype('Int64')
        games_df['away_team_id'] = games_df['away_team_id'].astype('Int64')
        games_df['away_team_score'] = games_df['away_team_score'].astype('Int64')
        games_df['date'] = pd.to_datetime(games_df['date'])
        games_df.set_index('game_id', inplace=True)
        return games_df
    else:
        return new_games

def get_games(sql_engine):
    years = [2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009]
    new_games = []
    weeks = {2: list(range(1,19)),
            3: [1,2,3,4,5]}
    for year in years:
        for seasontype in [2,3]:
            for week in weeks[seasontype]:
                url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={year}&seasontype={seasontype}&week={week}"
                games_response = requests.get(url)
                games_data = games_response.json()
                new_games = new_games + load_game_data(games_data['events'])
    if(len(new_games)>0):
        games_df = pd.DataFrame(new_games)
        games_df['game_id'] = games_df['game_id'].astype('Int64')
        games_df['home_team_id'] = games_df['home_team_id'].astype('Int64')
        games_df['home_team_score'] = games_df['home_team_score'].astype('Int64')
        games_df['away_team_id'] = games_df['away_team_id'].astype('Int64')
        games_df['away_team_score'] = games_df['away_team_score'].astype('Int64')
        games_df['date'] = pd.to_datetime(games_df['date'])
        games_df.set_index('game_id', inplace=True)
        append_new_rows(games_df, 'games', sql_engine, 'game_id')

def get_plays(game_ids, sql_engine):
    plays = []  
    playtypes = []
    for game_id in game_ids:
        plays_in_db = get_existing_ids(sql_engine, "plays", "play_id")
        url = f"https://cdn.espn.com/core/nfl/playbyplay?xhr=1&gameId={game_id}"
        try:
            game_response = requests.get(url)
            if game_response.status_code == 200:
                try:
                    game_data = game_response.json()

                    drives_data = game_data.get('gamepackageJSON', {}).get('drives',{}).get('previous', [])

                    game_from_sql = sql_engine.connect().execute(text(f"SELECT * FROM games where game_id = {game_id}"))
                    game_df = pd.DataFrame(game_from_sql.fetchall())
                    for drive_i in range(len(drives_data)):
                        drive_data = drives_data[drive_i]
                        plays_data = drive_data.get('plays',[])
                        for play_data in plays_data:
                            play_id = play_data.get('id', None)
                            if (not play_id == None)and(not int(play_id) in plays_in_db):
                                play = {}
                                play['play_id'] = play_data.get('id', None)
                                play['game_id'] = game_id
                                play['sequenceNumber'] = play_data.get('sequenceNumber', None)
                                play['homeScore'] = play_data.get('homeScore', None)
                                play['awayScore'] = play_data.get('awayScore', None)
                                play['quarter'] = play_data.get('period', {}).get('number', None)
                                play['clock'] = play_data.get('clock', {}).get('displayValue', None)

                                offense_team_id = play_data.get('start', {}).get('team', {}).get('id', None)

                                if offense_team_id == None:
                                    play['offenseAtHome'] = None
                                elif int(offense_team_id) == game_df['home_team_id'].values[0]:
                                    play['offenseAtHome'] = True
                                else:
                                    play['offenseAtHome'] = False

                                play['down'] = play_data.get('start', {}).get('down', None)
                                play['distance'] = play_data.get('start', {}).get('distance', None)
                                play['yardsToEndzone'] = play_data.get('start', {}).get('yardsToEndzone', None)
                                next_team_id = play_data.get('end', {}).get('team', {}).get('id', None)
                                if next_team_id == None:
                                    play['possessionChange'] = None
                                elif next_team_id== offense_team_id:
                                    play['possessionChange'] = False
                                else:
                                    play['possessionChange'] = False
                                play['next_down'] = play_data.get('end', {}).get('down', None)
                                play['next_distance'] = play_data.get('end', {}).get('distance', None)
                                play['next_yardsToEndzone'] = play_data.get('end', {}).get('yardsToEndzone', None)
                                play['playtype_id'] = play_data.get('type', {}).get('id', None)
                                play['description'] = play_data.get('text', None)
                                plays.append(play)
                                playtypes.append(play_data.get('type', {}))
                except Exception as e:
                    print("JSON error for game_id", game_id, e)
            else:
                print("No 200 response for game_id", game_id)
        except Exception as e:
            print("No response from Server for game_id", game_id)

    if len(plays)>0:
        playtypes_df = pd.DataFrame(playtypes)
        playtypes_df.drop_duplicates(inplace=True)
        playtypes_df['id'] = playtypes_df['id'].astype('Int64')
        playtypes_df.sort_values(by='id', inplace=True)
        playtypes_df.rename(columns={'id': 'playtype_id'}, inplace=True)
        playtypes_df.set_index('playtype_id', inplace=True)

        plays_df = pd.DataFrame(plays)
        plays_df['play_id'] = plays_df['play_id'].astype('Int64')
        plays_df['clock'] = '00:' + plays_df['clock']
        plays_df['playtype_id'] = plays_df['playtype_id'].astype('Int64')
        plays_df['sequenceNumber'] = plays_df['sequenceNumber'].astype('Int64')
        plays_df.set_index('play_id', inplace=True)

        return plays_df, playtypes_df
    else:
        return [], []

def append_new_probabilities(dataframe, table, sql_engine, id_column):
    existing_ids_set = get_existing_ids(sql_engine, table, id_column)
    if not existing_ids_set:  # If there are no existing IDs in the SQL table
        for index, row in dataframe.iterrows():
            try:
                row.to_frame().T.to_sql('probabilities', con=sql_engine, if_exists='append', index=True, index_label=id_column)
            except:
                pass
    else:
        new_rows = dataframe[~dataframe.index.isin(existing_ids_set)]
        for index, row in new_rows.iterrows():
            try:
                row.to_frame().T.to_sql('probabilities', con=sql_engine, if_exists='append', index=True, index_label=id_column)
            except Exception as e:
                pass

def get_probabilities(game_ids, sql_engine):
    percentages = []
    #games_in_db = [i[0] for i in sql_engine.connect().execute(text(f"SELECT DISTINCT game_id FROM probabilities")).fetchall()]
    for game_id in game_ids: #  list(set(game_ids) - set(games_in_db)):
        probas_in_db = [i[0] for i in sql_engine.connect().execute(text(f"SELECT proba_id FROM probabilities WHERE game_id={game_id};")).fetchall()]

        try:
            url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{game_id}/competitions/{game_id}/probabilities?limit=3000"
            response = requests.get(url)
            data = response.json()
            pages = data.get('pageCount', 0)
            for page in range(1,pages+1):
                url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{game_id}/competitions/{game_id}/probabilities?limit=3000&page={page}"
                response = requests.get(url)
                data = response.json()
                for item in data['items']:
                    proba_id = int(str(game_id)+str(item.get('sequenceNumber', None)))
                    if not proba_id in probas_in_db:
                        percentage_data = {}
                        percentage_data['proba_id'] = proba_id
                        percentage_data['game_id'] = game_id
                        percentage_data['sequenceNumber'] = item.get('sequenceNumber', None)
                        percentage_data['homeWinPercentage'] = item.get('homeWinPercentage', None)
                        percentage_data['awayWinPercentage'] = item.get('awayWinPercentage', None)
                        percentage_data['tiePercentage'] = item.get('tiePercentage', None)
                        percentages.append(percentage_data)
        except Exception as e:
            print(game_id, e)
    if(len(percentages)>0):
        percentages_df = pd.DataFrame(percentages)
        percentages_df['sequenceNumber'] = percentages_df['sequenceNumber'].astype('Int64')
        percentages_df.set_index('proba_id', inplace=True)
        return percentages_df
    else:
        return []

def get_current_week():
    url = f"https://cdn.espn.com/core/nfl/scoreboard?xhr=1&limit=50"
    response = requests.get(url)
    events = response.json().get('content', {}).get('sbData', {}).get('events', [])
    week = events[0]['week']['number']
    season = events[0]['season']['year']
    game_type = events[0]['season']['slug']
    return week, season, game_type

def update_game(game_id, game_df, sql_engine):
    set_clause = ", ".join([f"{col} = :{col}" for col in game_df.index])
    query = text(f"UPDATE games SET {set_clause} WHERE game_id = :game_id")

    params = game_df.to_dict()
    params["game_id"] = game_id

    with sql_engine.connect() as sql_connection:
        sql_connection.execute(query, params)
        sql_connection.commit()

def update_week(week, season, game_type, sql_engine):
    games_in_db = [i[0] for i in sql_engine.connect().execute(text(f"SELECT game_id FROM games WHERE week='{week}' AND season='{season}' AND game_type='{game_type}' ORDER BY game_id;")).fetchall()]
    game_statuses_in_db = [i[0] for i in sql_engine.connect().execute(text(f"SELECT game_status FROM games WHERE week='{week}' AND season='{season}' AND game_type='{game_type}' ORDER BY game_id;")).fetchall()]
    if(len(games_in_db)>0):
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype={2 if game_type == 'regular-season' else 3}&week={week}"
        response = requests.get(url)
        data = response.json()
        games_df = load_game_data(data['events'], sql_engine, asDataFrame=True, checkExistence=False)
        if(len(games_df)>0):
            for game_id, status in zip(games_in_db, game_statuses_in_db):
                update_game(game_id, games_df.loc[game_id, :], sql_engine)
                if(games_df.loc[game_id, 'game_status']>status):
                    print(f"status of game {game_id} changed.")
                    plays_df, _ = get_plays([game_id], sql_engine)
                    if(len(plays_df)>0):
                        append_new_rows(plays_df, 'plays', sql_engine, 'play_id')
                    percentages_df = get_probabilities([game_id], sql_engine)
                    if(len(percentages_df)>0):
                        append_new_probabilities(percentages_df, 'probabilities', sql_engine, 'proba_id')
                elif(games_df.loc[game_id, 'game_status']=='2'):
                    plays_df, _ = get_plays([game_id], sql_engine)
                    if(len(plays_df)>0):
                        append_new_rows(plays_df, 'plays', sql_engine, 'play_id')
                    percentages_df = get_probabilities([game_id], sql_engine)
                    if(len(percentages_df)>0):
                        append_new_probabilities(percentages_df, 'probabilities', sql_engine, 'proba_id')
    else:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype={2 if game_type == 'regular-season' else 3}&week={week}"
        response = requests.get(url)
        data = response.json()
        games_df = load_game_data(data['events'], sql_engine, asDataFrame=True)
        if(len(games_df)>0):
            append_new_rows(games_df, 'games', sql_engine, 'game_id')
        plays_df, _ = get_plays(list(games_df.index), sql_engine)
        if(len(plays_df)>0):
            append_new_rows(plays_df, 'plays', sql_engine, 'play_id')
        percentages_df = get_probabilities(list(games_df.index), sql_engine)
        if(len(percentages_df)>0):
            append_new_probabilities(percentages_df, 'probabilities', sql_engine, 'proba_id')

def update_running_game(game_id, sql_engine):
    plays_df, _ = get_plays([game_id], sql_engine)
    print(len(plays_df))
    if(len(plays_df)>0):
        append_new_rows(plays_df, 'plays', sql_engine, 'play_id')
        percentages_df = get_probabilities([game_id], sql_engine)
        print(len(percentages_df))
        if(len(percentages_df)>0):
            append_new_probabilities(percentages_df, 'probabilities', sql_engine, 'proba_id')

def get_news(sql_engine):
    print("getting news")
    urls = ["https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=150",
            "https://now.core.api.espn.com/v1/sports/news?limit=1000&sport=football",
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?team="]  # needs team_id
    existing_news = get_existing_ids(sql_engine, "news", "news_id")
    news = []
    article_links = set()
    news_response = requests.get(urls[0])
    news_data = news_response.json()
    articles_data = news_data.get('articles', [])
    for article_i in articles_data:
        article_link = article_i.get('links', {}).get('api', {}).get('news', {}).get('href', '')
        article_links.add(article_link)
        article_link = article_i.get('links', {}).get('api', {}).get('self', {}).get('href', '')
        article_links.add(article_link)
    #article_links.add(urls[1])
    for team_id in range(1,35):
        news_response = requests.get(urls[2]+str(team_id))
        news_data = news_response.json()
        articles_data = news_data.get('articles', [])
        for article_i in articles_data:
            article_link = article_i.get('links', {}).get('api', {}).get('news', {}).get('href', '')
            article_links.add(article_link)
            article_link = article_i.get('links', {}).get('api', {}).get('self', {}).get('href', '')
            article_links.add(article_link)
    cleaned_links = []
    for i in article_links:
        if ('sports/news' in i):
            cleaned_links.append(i)
    for article_link in cleaned_links:
        article_response = requests.get(article_link)
        article_data = article_response.json()
        headlines_data = article_data.get('headlines', [])
        for headline_i in headlines_data:
            headline_id = headline_i.get('id', None)
            if ( (not headline_id == None)and(not headline_id in existing_news) ):
                new_news = {}
                new_news['news_id'] = headline_id
                new_news['headline'] = headline_i.get('headline', None)
                new_news['description'] = headline_i.get('description', None)
                new_news['published'] = headline_i.get('published', None)
                story = headline_i.get('story', None)
                story_soup = BeautifulSoup(story, 'html.parser')
                story_plain = story_soup.get_text(separator=' ', strip=True)
                new_news['story'] = story_plain
                news.append(new_news)
    if len(news)>0:
        news_df = pd.DataFrame(news)
        news_df['news_id'] = news_df['news_id'].astype('Int64')
        news_df.set_index('news_id', inplace=True)
        news_df['published'] = pd.to_datetime(news_df['published'])
        news_df = news_df.loc[~news_df.index.duplicated()]
        append_new_rows(news_df, 'news', sql_engine, 'news_id')
        print(f"Added {len(news)} news")
    else:
        print("No new news yet.")
