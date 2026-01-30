import builtins
import contextlib
import logging
from collections.abc import Mapping
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup
from profanity_check import predict
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.engine import Engine

import streamlit as st

logger = logging.getLogger(__name__)


def create_sql_engine(*, no_db: bool = False) -> Engine:
    if no_db:
        sql_engine = create_engine(
            f"mysql+pymysql://avnadmin:{st.secrets['aiven_pwd']}@mysql-nfl-mhoffmann-nfl.b.aivencloud.com:10448",
            pool_size=20,
            max_overflow=50,
        )
    else:
        sql_engine = create_engine(
            f"mysql+pymysql://avnadmin:{st.secrets['aiven_pwd']}@mysql-nfl-mhoffmann-nfl.b.aivencloud.com:10448/nfl",
            pool_size=20,
            max_overflow=50,
        )
    return sql_engine


def initialize_database(sql_engine: Engine) -> None:
    metadata = MetaData()

    Table(
        "users",
        metadata,
        Column("user_id", Integer, primary_key=True, autoincrement=True),
        Column("user_name", String(100), nullable=False),
        Column("first_name", String(100), nullable=True),
        Column("last_name", String(100), nullable=True),
        Column("email", String(255), nullable=False),
        Column("password", String(255), nullable=False),
        Column("roles", String(255), nullable=True),
    )

    Table(
        "players",
        metadata,
        Column("player_id", Integer, primary_key=True),  # Set index as primary key
        Column("team_id", Integer, ForeignKey("teams.team_id")),
        Column("firstName", String(100)),
        Column("lastName", String(100)),
        Column("weight", Float),
        Column("height", Float),
        Column("age", Integer, nullable=True),
        Column("link", String(255)),
        Column("country", String(100), nullable=True),
        Column("picture", String(255), nullable=True),
        Column("jersey", Integer, nullable=True),
        Column("position_id", Integer, ForeignKey("positions.position_id")),
        Column("experience", Integer),
        Column("active", Boolean),
        Column("status_id", Integer, ForeignKey("playerstatuses.status_id")),
        Column("college_id", Integer, ForeignKey("colleges.college_id")),
    )

    Table(
        "playerstatuses",
        metadata,
        Column("status_id", Integer, primary_key=True),  # Set index as primary key
        Column("name", String(100)),
    )

    Table(
        "teams",
        metadata,
        Column("team_id", Integer, primary_key=True),  # Set index as primary key
        Column("abbreviation", String(10)),
        Column("name", String(255)),
        Column("location", String(255)),
        Column("color", String(50)),
        Column("logo", String(255)),
        Column("link", String(255)),
    )

    Table(
        "colleges",
        metadata,
        Column("college_id", Integer, primary_key=True),  # Set index as primary key
        Column("name", String(255)),
        Column("abbreviation", String(10), nullable=True),
        Column("logo", String(255), nullable=True),
        Column("mascot", String(255), nullable=True),
    )

    Table(
        "positions",
        metadata,
        Column("position_id", Integer, primary_key=True),  # Set index as primary key
        Column("name", String(100)),
        Column("abbreviation", String(10)),
        Column(
            "parent",
            Integer,
            nullable=True,
        ),  # Nullable in case parent position is not specified
    )

    Table(
        "games",
        metadata,
        Column("game_id", Integer, primary_key=True),
        Column("date", DateTime(timezone=True)),
        Column("name", String(255)),
        Column("season", Integer),
        Column("game_type", String(100)),
        Column("week", Integer),
        Column("home_team_id", Integer, ForeignKey("teams.team_id")),
        Column("home_team_score", Integer),
        Column("away_team_id", Integer, ForeignKey("teams.team_id")),
        Column("away_team_score", Integer),
        Column("standing_home_overall_win", Integer),
        Column("standing_home_Home_win", Integer),
        Column("standing_home_Road_win", Integer),
        Column("standing_home_overall_loss", Integer),
        Column("standing_home_Home_loss", Integer),
        Column("standing_home_Road_loss", Integer),
        Column("standing_away_overall_win", Integer),
        Column("standing_away_Home_win", Integer),
        Column("standing_away_Road_win", Integer),
        Column("standing_away_overall_loss", Integer),
        Column("standing_away_Home_loss", Integer),
        Column("standing_away_Road_loss", Integer),
        Column("link", String(255)),
        Column("game_status", String(100)),
    )

    Table(
        "playtypes",
        metadata,
        Column("playtype_id", Integer, primary_key=True),
        Column("text", String(255)),
        Column("abbreviation", String(10), nullable=True),
    )

    Table(
        "plays",
        metadata,
        Column("play_id", BigInteger, primary_key=True),
        Column("game_id", Integer, ForeignKey("games.game_id")),
        Column("sequenceNumber", Integer),
        Column("homeScore", Integer),
        Column("awayScore", Integer),
        Column("quarter", Integer),
        Column("clock", Time),
        Column("offenseAtHome", Boolean),
        Column("down", Integer),
        Column("distance", Integer),
        Column("yardsToEndzone", Integer),
        Column("possessionChange", Boolean),
        Column("next_down", Integer),
        Column("next_distance", Integer),
        Column("next_yardsToEndzone", Integer),
        Column("playtype_id", Integer, ForeignKey("playtypes.playtype_id")),
        Column("description", Text),
        UniqueConstraint("game_id", "sequenceNumber", name="uq_plays_game_sequence"),
    )

    Table(
        "probabilities",
        metadata,
        Column("proba_id", BigInteger, primary_key=True),
        Column("game_id", Integer, nullable=False),
        Column("sequenceNumber", Integer, nullable=False),
        Column("homeWinPercentage", Float, nullable=False),
        Column("awayWinPercentage", Float, nullable=False),
        Column("tiePercentage", Float, nullable=False),
        ForeignKeyConstraint(
            ["game_id", "sequenceNumber"],
            ["plays.game_id", "plays.sequenceNumber"],
            name="fk_probabilities_plays",
        ),
    )

    Table(
        "news",
        metadata,
        Column("news_id", Integer, primary_key=True),
        Column("headline", String(255), nullable=False),
        Column("description", String(1000), nullable=False),
        Column("published", DateTime(timezone=True), nullable=False),
        Column("story", Text, nullable=False),
    )

    metadata.create_all(sql_engine)


def get_existing_ids(sql_engine: Engine, table: str, id_column: str) -> set[int]:
    result = sql_engine.connect().execute(
        text(f"SELECT {id_column} FROM {table}"),  # noqa: S608
    )  # TODO: Check safer option
    df = pd.DataFrame(result.fetchall(), columns=[id_column])
    if df.empty:
        return set()
    return set(df[id_column].tolist())


def append_new_rows(
    dataframe: pd.DataFrame,
    table: str,
    sql_engine: Engine,
    id_column: str,
) -> None:
    existing_ids_set = {int(x) for x in get_existing_ids(sql_engine, table, id_column)}
    dataframe.index = dataframe.index.astype("int64")
    if not existing_ids_set:
        dataframe.to_sql(
            table,
            con=sql_engine,
            if_exists="append",
            index=True,
            index_label=id_column,
        )
    else:
        new_rows = dataframe[~dataframe.index.isin(existing_ids_set)]
        new_rows.to_sql(
            table,
            con=sql_engine,
            if_exists="append",
            index=True,
            index_label=id_column,
        )


def append_or_update_rows(
    dataframe: pd.DataFrame,
    table: str,
    sql_engine: Engine,
    id_column: str,
) -> None:
    existing_ids_set = {int(x) for x in get_existing_ids(sql_engine, table, id_column)}
    dataframe.index = dataframe.index.astype("int64")

    if not existing_ids_set:
        dataframe.to_sql(
            table,
            con=sql_engine,
            if_exists="append",
            index=True,
            index_label=id_column,
        )
    else:
        new_rows = dataframe[~dataframe.index.isin(existing_ids_set)]
        existing_rows = dataframe[dataframe.index.isin(existing_ids_set)]
        if not new_rows.empty:
            new_rows.to_sql(
                table,
                con=sql_engine,
                if_exists="append",
                index=True,
                index_label=id_column,
            )
        for idx, row in existing_rows.iterrows():
            update_dict = row.to_dict()
            set_clause = ", ".join([f"{col} = :{col}" for col in update_dict])
            query = f"UPDATE {table} SET {set_clause} WHERE {id_column} = :id"  # TODO: Check safer option  #noqa: S608
            query_db(sql_engine, query, **update_dict, id=int(idx))


def query_db(
    sql_engine: Engine,
    query: str,
    **params: Mapping[str, Any],
) -> list[dict[str, Any]] | None:
    with sql_engine.connect() as conn:
        result = conn.execute(text(query), params)
        if result.returns_rows:
            return [dict(row) for row in result.mappings()]
        conn.commit()
    return None


def _extract_team_info(comp: dict, side: str) -> dict:
    team = {}
    team[f"{side}_team_id"] = comp.get("team", {}).get("id")
    team[f"{side}_team_score"] = comp.get("score")

    for record in comp.get("records", []):
        name = record.get("name")
        if not name:
            continue
        summary = record.get("summary", [])
        team[f"standing_{side}_{name}_win"] = summary[0] if len(summary) > 0 else None
        team[f"standing_{side}_{name}_loss"] = summary[-1] if len(summary) > 0 else None
    return team


def _build_game_dict(game_data: dict) -> dict:
    game = {}
    game["game_id"] = game_data.get("id")
    game["date"] = game_data.get("date")
    game["name"] = game_data.get("name")
    game["season"] = game_data.get("season", {}).get("year")
    game["game_type"] = game_data.get("season", {}).get("slug")
    game["week"] = game_data.get("week", {}).get("number")
    game["link"] = game_data.get("links", [{}])[0].get("href")
    game["game_status"] = game_data.get("status", {}).get("type", {}).get("id")

    competitions = game_data.get("competitions", [{}])[0]
    competitors = competitions.get("competitors", [{}, {}])

    if competitors[0].get("homeAway") == "home":
        home_comp = competitors[0]
        away_comp = competitors[1]
    else:
        home_comp = competitors[1]
        away_comp = competitors[0]

    game.update(_extract_team_info(home_comp, "home"))
    game.update(_extract_team_info(away_comp, "away"))

    return game


def load_game_data(
    events: list[dict[str, Any]],
    sql_engine: Engine,
    *,
    as_dataframe: bool = False,
    check_existence: bool = False,
) -> pd.DataFrame | list[dict[str, Any]]:
    games_in_db = set(get_existing_ids(sql_engine, "games", "game_id"))

    new_games = []

    for game_data in events:
        try:
            game_id = game_data.get("id")
            if game_id is None:
                continue
            if check_existence and int(game_id) in games_in_db:
                continue
            game = _build_game_dict(game_data)
            new_games.append(game)
        except:
            pass

    if as_dataframe:
        games_df = pd.DataFrame(new_games)
        int_cols = [
            "game_id",
            "home_team_id",
            "home_team_score",
            "away_team_id",
            "away_team_score",
        ]
        for col in int_cols:
            if col in games_df.columns:
                games_df[col] = games_df[col].astype("Int64")
        if "date" in games_df.columns:
            games_df["date"] = pd.to_datetime(games_df["date"])
        return games_df.set_index("game_id")

    return new_games


def get_games(sql_engine: Engine) -> None:
    years = [
        2024,
        2023,
        2022,
        2021,
        2020,
        2019,
        2018,
        2017,
        2016,
        2015,
        2014,
        2013,
        2012,
        2011,
        2010,
        2009,
    ]
    new_games = []
    weeks = {2: list(range(1, 19)), 3: [1, 2, 3, 4, 5]}
    for year in years:
        for seasontype in [2, 3]:
            for week in weeks[seasontype]:
                url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={year}&seasontype={seasontype}&week={week}"
                games_response = requests.get(url, timeout=10)
                games_data = games_response.json()
                new_games = new_games + load_game_data(games_data["events"], sql_engine)
    if len(new_games) > 0:
        games_df = pd.DataFrame(new_games)
        games_df["game_id"] = games_df["game_id"].astype("Int64")
        games_df["home_team_id"] = games_df["home_team_id"].astype("Int64")
        games_df["home_team_score"] = games_df["home_team_score"].astype("Int64")
        games_df["away_team_id"] = games_df["away_team_id"].astype("Int64")
        games_df["away_team_score"] = games_df["away_team_score"].astype("Int64")
        games_df["date"] = pd.to_datetime(games_df["date"])
        games_df = games_df.set_index("game_id")
        append_new_rows(games_df, "games", sql_engine, "game_id")


def _fetch_game_data(game_id: int) -> dict | None:
    url = f"https://cdn.espn.com/core/nfl/playbyplay?xhr=1&gameId={game_id}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        logger.exception(
            "Failed to fetch or parse play-by-play for game_id %s",
            game_id,
        )
        return None


def _fetch_game_from_db(sql_engine: Engine, game_id: int) -> pd.DataFrame:
    rows = query_db(
        sql_engine,
        "SELECT * FROM games WHERE game_id = :game_id",
        game_id=game_id,
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _process_plays_for_drive(
    drive_data: dict,
    game_id: int,
    game_df: pd.DataFrame,
    plays_in_db: set[int],
) -> tuple[list[dict], list[dict]]:
    plays = []
    playtypes = []

    for play_data in drive_data.get("plays", []):
        play_id = play_data.get("id")
        if play_id is None or int(play_id) in plays_in_db:
            continue

        play = {
            "play_id": play_id,
            "game_id": game_id,
            "sequenceNumber": play_data.get("sequenceNumber"),
            "homeScore": play_data.get("homeScore"),
            "awayScore": play_data.get("awayScore"),
            "quarter": play_data.get("period", {}).get("number"),
            "clock": play_data.get("clock", {}).get("displayValue"),
            "down": play_data.get("start", {}).get("down"),
            "distance": play_data.get("start", {}).get("distance"),
            "yardsToEndzone": play_data.get("start", {}).get("yardsToEndzone"),
            "next_down": play_data.get("end", {}).get("down"),
            "next_distance": play_data.get("end", {}).get("distance"),
            "next_yardsToEndzone": play_data.get("end", {}).get("yardsToEndzone"),
            "playtype_id": play_data.get("type", {}).get("id"),
            "description": play_data.get("text"),
        }

        offense_team_id = play_data.get("start", {}).get("team", {}).get("id")
        if offense_team_id is None:
            play["offenseAtHome"] = None
        elif (
            not game_df.empty
            and int(offense_team_id) == game_df["home_team_id"].to_numpy()[0]
        ):
            play["offenseAtHome"] = True
        else:
            play["offenseAtHome"] = False

        next_team_id = play_data.get("end", {}).get("team", {}).get("id")
        if next_team_id is None:
            play["possessionChange"] = None
        else:
            play["possessionChange"] = next_team_id != offense_team_id

        plays.append(play)
        playtypes.append(play_data.get("type", {}))

    return plays, playtypes


def _build_playtypes_df(playtypes: list[dict]) -> pd.DataFrame:
    if not playtypes:
        return pd.DataFrame(columns=["playtype_id", "text", "abbreviation"]).set_index(
            "playtype_id",
        )

    df = pd.DataFrame(playtypes).drop_duplicates()
    df["id"] = df["id"].astype("Int64")
    return (
        df.sort_values(by="id")
        .rename(columns={"id": "playtype_id"})
        .set_index("playtype_id")
    )


def _build_plays_df(plays: list[dict]) -> pd.DataFrame:
    if not plays:
        return pd.DataFrame(
            columns=[
                "play_id",
                "game_id",
                "sequenceNumber",
                "homeScore",
                "awayScore",
                "quarter",
                "clock",
                "offenseAtHome",
                "down",
                "distance",
                "yardsToEndzone",
                "possessionChange",
                "next_down",
                "next_distance",
                "next_yardsToEndzone",
                "playtype_id",
                "description",
            ],
        ).set_index("play_id")

    df = pd.DataFrame(plays)
    df["play_id"] = df["play_id"].astype("Int64")
    df["playtype_id"] = df["playtype_id"].astype("Int64")
    df["sequenceNumber"] = df["sequenceNumber"].astype("Int64")
    df["clock"] = "00:" + df["clock"]
    return df.set_index("play_id")


def get_plays(
    game_ids: list[int],
    sql_engine: Engine,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_plays = []
    all_playtypes = []

    for game_id in game_ids:
        game_data = _fetch_game_data(game_id)
        if not game_data:
            continue

        game_df = _fetch_game_from_db(sql_engine, game_id)
        plays_in_db = get_existing_ids(sql_engine, "plays", "play_id")

        drives = (
            game_data.get("gamepackageJSON", {}).get("drives", {}).get("previous", [])
        )
        for drive in drives:
            plays, playtypes = _process_plays_for_drive(
                drive,
                game_id,
                game_df,
                plays_in_db,
            )
            all_plays.extend(plays)
            all_playtypes.extend(playtypes)

    return _build_plays_df(all_plays), _build_playtypes_df(all_playtypes)


def append_new_probabilities(
    dataframe: pd.DataFrame,
    table: str,
    sql_engine: Engine,
    id_column: str,
) -> None:
    existing_ids_set = get_existing_ids(sql_engine, table, id_column)
    if not existing_ids_set:
        for _index, row in dataframe.iterrows():
            with contextlib.suppress(builtins.BaseException):
                row.to_frame().T.to_sql(
                    "probabilities",
                    con=sql_engine,
                    if_exists="append",
                    index=True,
                    index_label=id_column,
                )
    else:
        new_rows = dataframe[~dataframe.index.isin(existing_ids_set)]
        for _index, row in new_rows.iterrows():
            with contextlib.suppress(Exception):
                row.to_frame().T.to_sql(
                    "probabilities",
                    con=sql_engine,
                    if_exists="append",
                    index=True,
                    index_label=id_column,
                )


def get_probabilities(
    game_ids: list[int],
    sql_engine: Engine,
) -> pd.DataFrame:
    percentages = []
    for game_id in game_ids:
        rows = query_db(
            sql_engine,
            "SELECT proba_id FROM probabilities WHERE game_id = :game_id",
            game_id=game_id,
        )

        probas_in_db = [row["proba_id"] for row in rows] if rows else []

        try:
            url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{game_id}/competitions/{game_id}/probabilities?limit=3000"
            response = requests.get(url, timeout=10)
            data = response.json()
            pages = data.get("pageCount", 0)
            for page in range(1, pages + 1):
                url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{game_id}/competitions/{game_id}/probabilities?limit=3000&page={page}"
                response = requests.get(url, timeout=10)
                data = response.json()
                for item in data["items"]:
                    proba_id = int(str(game_id) + str(item.get("sequenceNumber", None)))
                    if proba_id not in probas_in_db:
                        percentage_data = {}
                        percentage_data["proba_id"] = proba_id
                        percentage_data["game_id"] = game_id
                        percentage_data["sequenceNumber"] = item.get(
                            "sequenceNumber",
                            None,
                        )
                        percentage_data["homeWinPercentage"] = item.get(
                            "homeWinPercentage",
                            None,
                        )
                        percentage_data["awayWinPercentage"] = item.get(
                            "awayWinPercentage",
                            None,
                        )
                        percentage_data["tiePercentage"] = item.get(
                            "tiePercentage",
                            None,
                        )
                        percentages.append(percentage_data)
        except Exception:
            logger.exception(
                "Failed to fetch or process probabilities for game_id %s",
                game_id,
            )
    if len(percentages) > 0:
        percentages_df = pd.DataFrame(percentages)
        percentages_df["sequenceNumber"] = percentages_df["sequenceNumber"].astype(
            "Int64",
        )
        return percentages_df.set_index("proba_id")
    return pd.DataFrame(
        columns=[
            "proba_id",
            "game_id",
            "sequenceNumber",
            "homeWinPercentage",
            "awayWinPercentage",
            "tiePercentage",
        ],
    ).set_index("proba_id")


def get_current_week() -> tuple[int, int, str]:
    url = "https://cdn.espn.com/core/nfl/scoreboard?xhr=1&limit=50"
    response = requests.get(url, timeout=10)
    events = response.json().get("content", {}).get("sbData", {}).get("events", [])
    week = events[0]["week"]["number"]
    season = events[0]["season"]["year"]
    game_type = events[0]["season"]["slug"]
    if game_type == "post-season" and week == 4:
        week = 5  # skip Pro Bowl and show Super Bowl instead
    return week, season, game_type


def update_game(
    game_id: int,
    game_df: pd.Series,
    sql_engine: Engine,
) -> None:
    set_clause = ", ".join([f"{col} = :{col}" for col in game_df.index])
    query = f"UPDATE games SET {set_clause} WHERE game_id = :game_id"  # noqa: S608  # TODO: Check safer option
    params = game_df.to_dict()
    params["game_id"] = game_id
    query_db(sql_engine, query, **params)


def _add_new_games(games_df: pd.DataFrame, sql_engine: Engine) -> None:
    if len(games_df) > 0:
        append_new_rows(games_df, "games", sql_engine, "game_id")
        plays_df, _ = get_plays(list(games_df.index), sql_engine)
        if len(plays_df) > 0:
            append_new_rows(plays_df, "plays", sql_engine, "play_id")
        percentages_df = get_probabilities(list(games_df.index), sql_engine)
        if len(percentages_df) > 0:
            append_new_probabilities(
                percentages_df,
                "probabilities",
                sql_engine,
                "proba_id",
            )


def update_week(
    week: int,
    season: int,
    game_type: str,
    sql_engine: Engine,
) -> None:
    def update_game_in_db(
        game_id: int | str,
        status: str,
        games_df: pd.DataFrame,
        sql_engine: Engine,
    ) -> None:
        update_game(game_id, games_df.loc[game_id, :], sql_engine)
        if (games_df.loc[game_id, "game_status"] != status) or (
            games_df.loc[game_id, "game_status"] == "2"
        ):
            plays_df, _ = get_plays([game_id], sql_engine)
            if len(plays_df) > 0:
                append_new_rows(plays_df, "plays", sql_engine, "play_id")
            percentages_df = get_probabilities([game_id], sql_engine)
            if len(percentages_df) > 0:
                append_new_probabilities(
                    percentages_df,
                    "probabilities",
                    sql_engine,
                    "proba_id",
                )

    rows = query_db(
        sql_engine,
        """
        SELECT game_id
        FROM games
        WHERE week = :week AND season = :season AND game_type = :game_type
        ORDER BY game_id;
        """,
        week=week,
        season=season,
        game_type=game_type,
    )

    games_in_db = [row["game_id"] for row in rows] if rows else []

    rows = query_db(
        sql_engine,
        """
        SELECT game_status
        FROM games
        WHERE week = :week AND season = :season AND game_type = :game_type
        ORDER BY game_id;
        """,
        week=week,
        season=season,
        game_type=game_type,
    )

    game_statuses_in_db = [row["game_status"] for row in rows] if rows else []

    if len(games_in_db) > 0:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype={2 if game_type == 'regular-season' else 3}&week={week}"
        response = requests.get(url, timeout=10)
        data = response.json()
        games_df = load_game_data(
            data["events"],
            sql_engine,
            as_dataframe=True,
            check_existence=False,
        )
        if len(games_df) > 0:
            # loop over already existing games and update
            for game_id, status in zip(games_in_db, game_statuses_in_db, strict=False):
                update_game_in_db(game_id, status, games_df, sql_engine)
            # add new games
            new_games_df = games_df[~games_df.index.isin(games_in_db)]
            if len(new_games_df) > 0:
                _add_new_games(new_games_df, sql_engine)
    else:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype={2 if game_type == 'regular-season' else 3}&week={week}"
        response = requests.get(url, timeout=10)
        data = response.json()
        games_df = load_game_data(data["events"], sql_engine, as_dataframe=True)
        _add_new_games(games_df, sql_engine)


def update_full_schedule(
    season: int,
    sql_engine: Engine,
) -> None:
    for week in range(1, 19):
        update_week(week, season, "regular-season", sql_engine)
    for week in [1, 2, 3, 5]:
        update_week(week, season, "post-season", sql_engine)


def update_running_game(
    game_id: int,
    sql_engine: Engine,
    *,
    update_status: bool = False,
) -> None:
    plays_df, _ = get_plays([game_id], sql_engine)
    if len(plays_df) > 0:
        append_new_rows(plays_df, "plays", sql_engine, "play_id")
        percentages_df = get_probabilities([game_id], sql_engine)
        if len(percentages_df) > 0:
            append_new_probabilities(
                percentages_df,
                "probabilities",
                sql_engine,
                "proba_id",
            )
    if update_status:
        game_info = query_db(
            sql_engine,
            "SELECT season, week, game_type FROM games WHERE game_id=:game_id;",
            game_id=game_id,
        )[0]
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={game_info['season']}&seasontype={2 if game_info['game_type'] == 'regular-season' else 3}&week={game_info['week']}"
        response = requests.get(url, timeout=10)
        data = response.json()
        games_df = load_game_data(
            data["events"],
            sql_engine,
            as_dataframe=True,
            check_existence=False,
        )
        if (len(games_df) > 0) and (game_id in games_df.index):
            update_game(game_id, games_df.loc[game_id, :], sql_engine)


def get_news(sql_engine: Engine) -> None:
    urls = [
        "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=150",
        "https://now.core.api.espn.com/v1/sports/news?limit=1000&sport=football",
        "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?team=",
    ]  # needs team_id
    existing_news = get_existing_ids(sql_engine, "news", "news_id")
    news = []
    article_links = set()
    news_response = requests.get(urls[0], timeout=10)
    news_data = news_response.json()
    articles_data = news_data.get("articles", [])
    for article_i in articles_data:
        article_link = (
            article_i.get("links", {}).get("api", {}).get("news", {}).get("href", "")
        )
        article_links.add(article_link)
        article_link = (
            article_i.get("links", {}).get("api", {}).get("self", {}).get("href", "")
        )
        article_links.add(article_link)
    # article_links.add(urls[1])  # noqa: ERA001
    for team_id in range(1, 35):
        news_response = requests.get(urls[2] + str(team_id), timeout=10)
        news_data = news_response.json()
        articles_data = news_data.get("articles", [])
        for article_i in articles_data:
            article_link = (
                article_i.get("links", {})
                .get("api", {})
                .get("news", {})
                .get("href", "")
            )
            article_links.add(article_link)
            article_link = (
                article_i.get("links", {})
                .get("api", {})
                .get("self", {})
                .get("href", "")
            )
            article_links.add(article_link)
    cleaned_links = [i for i in article_links if "sports/news" in i]
    for article_link in cleaned_links:
        article_response = requests.get(article_link, timeout=10)
        article_data = article_response.json()
        headlines_data = article_data.get("headlines", [])
        for headline_i in headlines_data:
            headline_id = headline_i.get("id", None)
            if (headline_id is not None) and (headline_id not in existing_news):
                new_news = {}
                new_news["news_id"] = headline_id
                new_news["headline"] = headline_i.get("headline", None)
                new_news["description"] = headline_i.get("description", None)
                new_news["published"] = headline_i.get("published", None)
                story = headline_i.get("story", None)
                story_soup = BeautifulSoup(story, "html.parser")
                story_plain = story_soup.get_text(separator=" ", strip=True)
                new_news["story"] = story_plain
                news.append(new_news)
    if len(news) > 0:
        news_df = pd.DataFrame(news)
        news_df["news_id"] = news_df["news_id"].astype("Int64")
        news_df = news_df.set_index("news_id")
        news_df["published"] = pd.to_datetime(news_df["published"])
        news_df = news_df.loc[~news_df.index.duplicated()]
        append_new_rows(news_df, "news", sql_engine, "news_id")


def validate_username(username: str) -> bool:
    sql_engine = create_sql_engine()
    return (
        username.lower()
        not in [
            i["user_name"].lower()
            for i in query_db(sql_engine, "SELECT user_name FROM users")
        ]
    ) and (predict([username]) == 0)


def _fetch_team_roster(team_id: int, season: int) -> list[dict]:
    url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/teams/{team_id}/athletes?limit=200"
    response = requests.get(url, timeout=10)
    data = response.json()
    return data.get("items", [])


def _process_player(player_data: dict, team_id: int) -> tuple[dict, str, dict]:
    player = {
        "player_id": player_data.get("id"),
        "team_id": team_id,
        "firstName": player_data.get("firstName"),
        "lastName": player_data.get("lastName"),
        "weight": player_data.get("weight"),
        "height": player_data.get("height"),
        "age": player_data.get("age"),
        "link": player_data.get("links", [{}])[0].get("href"),
        "country": player_data.get("birthPlace", {}).get("country"),
        "picture": player_data.get("headshot", {}).get("href"),
        "jersey": player_data.get("jersey"),
        "position_id": player_data.get("position", {}).get("id"),
        "experience": player_data.get("experience", {}).get("years"),
        "active": player_data.get("active"),
        "status_id": player_data.get("status", {}).get("id"),
        "college_id": None,
    }

    college_ref = player_data.get("college", {}).get("$ref", "unknown")
    college_id = college_ref.split("/")[-1].split("?")[0]
    if college_id != "unknown":
        player["college_id"] = college_id

    status_name = player_data.get("status", {}).get("name")

    return player, player["college_id"], {player["status_id"]: status_name}


def _build_players_df(players: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(players)
    for col in ["player_id", "status_id", "college_id"]:
        if col in df.columns:
            df[col] = df[col].astype("Int64")
    df = df.sort_values("player_id").set_index("player_id")
    return df.astype(object).where(pd.notna(df), None)


def _build_status_df(status_data: dict) -> pd.DataFrame:
    df = pd.DataFrame(list(status_data.items()), columns=["status_id", "name"])
    df["status_id"] = df["status_id"].astype("Int64")
    df = df.sort_values("status_id").set_index("status_id")
    return df.astype(object).where(pd.notna(df), None)


def get_players(team_id: int | None = None) -> None:
    sql_engine = create_sql_engine()
    _, season, _ = get_current_week()

    if team_id is not None:
        team_ids = [team_id]
    else:
        team_ids = [
            i["team_id"]
            for i in query_db(
                sql_engine,
                "SELECT team_id FROM teams WHERE team_id NOT IN (-2, -1, 31, 32, 38)",
            )
        ]

    all_players = []
    all_statuses = {}
    colleges = set()

    for team_i in team_ids:
        query_db(
            sql_engine,
            "UPDATE players SET active=0, status_id=999, team_id=NULL WHERE player_id>0 AND team_id=:team_id",
            team_id=team_i,
        )
        roster = _fetch_team_roster(team_i, season)
        st.write("Processing team", team_i, "with", len(roster), "players")
        for item in roster:
            player_data = requests.get(item["$ref"], timeout=10).json()
            player, college_id, status = _process_player(player_data, team_i)
            all_players.append(player)
            if college_id:
                colleges.add(college_id)
            all_statuses.update(status)

    players_df = _build_players_df(all_players)
    status_df = _build_status_df(all_statuses)
    colleges_df = get_colleges(colleges)

    append_new_rows(colleges_df, "colleges", sql_engine, "college_id")
    append_new_rows(status_df, "playerstatuses", sql_engine, "status_id")
    append_or_update_rows(players_df, "players", sql_engine, "player_id")

    st.rerun()


def get_colleges(college_ids: set[int]) -> pd.DataFrame:
    colleges = []
    for college_id in list(college_ids):
        url = f"http://sports.core.api.espn.com/v2/colleges/{college_id}?lang=en&region=us"
        college_response = requests.get(url, timeout=10)
        college_data = college_response.json()
        college = {}
        college["college_id"] = college_id
        college["name"] = college_data.get("name", None)
        college["abbreviation"] = college_data.get("abbrev", None)
        college["logo"] = college_data.get("logos", [{}])[0].get("href", None)
        college["mascot"] = college_data.get("mascot", None)
        colleges.append(college)
    colleges_df = pd.DataFrame(colleges)
    colleges_df["college_id"] = colleges_df["college_id"].astype("Int64")
    return colleges_df.set_index("college_id")
