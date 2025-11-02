import math

import pandas as pd
from sources.sql import create_sql_engine, get_current_week, query_db
from sources.utils import display_table

import streamlit as st

sql_engine = create_sql_engine()
current_week, current_season, current_game_type = get_current_week()

st.title("NFL Standings", anchor=False)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load standings, divisions, and teams from the database."""
    standings_df = pd.DataFrame(
        query_db(
            sql_engine,
            "SELECT * FROM games WHERE season = :current_season AND game_type = 'regular-season' AND game_status = 3",
            current_season=current_season,
        ),
    )
    divisions_df = pd.DataFrame(query_db(sql_engine, "SELECT * FROM divisions"))
    teams_df = pd.DataFrame(
        query_db(
            sql_engine,
            "SELECT * FROM teams WHERE team_id NOT IN (-2, -1, 31, 32, 38);",
        ),
    )
    return standings_df, divisions_df, teams_df


def _init_empty_standings(
    teams_df: pd.DataFrame,
) -> pd.DataFrame:
    team_ids = teams_df["team_id"].tolist()
    data = {
        "team_id": team_ids,
        "Wins": [0] * len(team_ids),
        "Losses": [0] * len(team_ids),
        "Ties": [0] * len(team_ids),
        "Points_Scored": [0] * len(team_ids),
        "Points_Allowed": [0] * len(team_ids),
        "Conference_Wins": [0] * len(team_ids),
        "Conference_Losses": [0] * len(team_ids),
        "Conference_Ties": [0] * len(team_ids),
        "Division_Wins": [0] * len(team_ids),
        "Division_Losses": [0] * len(team_ids),
        "Division_Ties": [0] * len(team_ids),
        "Opponents": [[] for _ in team_ids],
        "Beaten_Opponents": [[] for _ in team_ids],
    }
    return pd.DataFrame(data).set_index("team_id")


def _process_game_results(
    stats_df: pd.DataFrame,
    games_df: pd.DataFrame,
) -> pd.DataFrame:
    games_df = games_df.copy()
    games_df["winner"] = games_df.apply(
        lambda g: g["home_team_id"]
        if g["home_team_score"] > g["away_team_score"]
        else g["away_team_id"]
        if g["away_team_score"] > g["home_team_score"]
        else None,
        axis=1,
    )
    games_df["loser"] = games_df.apply(
        lambda g: g["away_team_id"]
        if g["home_team_score"] > g["away_team_score"]
        else g["home_team_id"]
        if g["away_team_score"] > g["home_team_score"]
        else None,
        axis=1,
    )
    games_df["is_tie"] = games_df["winner"].isna()

    for _, g in games_df.iterrows():
        home, away = g["home_team_id"], g["away_team_id"]
        hs, as_ = g["home_team_score"], g["away_team_score"]

        for team, scored, allowed, opp in [
            (home, hs, as_, away),
            (away, as_, hs, home),
        ]:
            if team in stats_df.index:
                stats_df.loc[team, "Points_Scored"] += scored
                stats_df.loc[team, "Points_Allowed"] += allowed
                stats_df.loc[team, "Opponents"].append(opp)

        winner, loser = g["winner"], g["loser"]

        if not g["is_tie"]:
            if winner in stats_df.index:
                stats_df.loc[winner, "Wins"] += 1
                stats_df.loc[winner, "Beaten_Opponents"].append(loser)
            if loser in stats_df.index:
                stats_df.loc[loser, "Losses"] += 1
        else:
            for t in (home, away):
                if t in stats_df.index:
                    stats_df.loc[t, "Ties"] += 1

    return stats_df


def _apply_conf_div_stats(
    stats_df: pd.DataFrame,
    games_df: pd.DataFrame,
    divisions_df: pd.DataFrame,
) -> pd.DataFrame:
    def _update_record(
        team_id: int | str,
        team_games: pd.DataFrame,
        valid_opponents: list[int | str],
        prefix: str,
    ) -> None:
        for _, g in team_games.iterrows():
            opp_id = (
                g["away_team_id"] if g["home_team_id"] == team_id else g["home_team_id"]
            )
            if opp_id not in valid_opponents:
                continue

            home_win = g["home_team_score"] > g["away_team_score"]
            away_win = g["away_team_score"] > g["home_team_score"]
            tie = g["home_team_score"] == g["away_team_score"]

            if (home_win and g["home_team_id"] == team_id) or (
                away_win and g["away_team_id"] == team_id
            ):
                stats_df.loc[team_id, f"{prefix}_Wins"] += 1
            elif tie:
                stats_df.loc[team_id, f"{prefix}_Ties"] += 1
            else:
                stats_df.loc[team_id, f"{prefix}_Losses"] += 1

    for team_id in stats_df.index:
        team_info = divisions_df[divisions_df["team_id"] == team_id]
        if team_info.empty:
            continue

        team_conf = team_info["conference"].iloc[0]
        team_div = team_info["division"].iloc[0]

        team_games = games_df[
            (games_df["home_team_id"] == team_id)
            | (games_df["away_team_id"] == team_id)
        ]

        conf_team_ids = divisions_df.loc[
            divisions_df["conference"] == team_conf,
            "team_id",
        ].tolist()
        _update_record(team_id, team_games, conf_team_ids, "Conference")

        div_team_ids = divisions_df.loc[
            divisions_df["division"] == team_div,
            "team_id",
        ].tolist()
        _update_record(team_id, team_games, div_team_ids, "Division")

    return stats_df


def _merge_and_compute_basic_pct(
    stats_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    divisions_df: pd.DataFrame,
) -> pd.DataFrame:
    stats_df = stats_df.merge(divisions_df, on="team_id", how="left")
    stats_df = stats_df.merge(teams_df, on="team_id", how="left")
    stats_df["Total_Games"] = stats_df["Wins"] + stats_df["Losses"] + stats_df["Ties"]

    stats_df["overall_win_pct"] = (
        stats_df["Wins"] + 0.5 * stats_df["Ties"]
    ) / stats_df["Total_Games"]
    stats_df["division_win_pct"] = (
        stats_df["Division_Wins"] + 0.5 * stats_df["Division_Ties"]
    ) / (
        stats_df["Division_Wins"]
        + stats_df["Division_Losses"]
        + stats_df["Division_Ties"]
    )
    stats_df["conference_win_pct"] = (
        stats_df["Conference_Wins"] + 0.5 * stats_df["Conference_Ties"]
    ) / (
        stats_df["Conference_Wins"]
        + stats_df["Conference_Losses"]
        + stats_df["Conference_Ties"]
    )

    return stats_df


def _compute_sov_sos(stats_df: pd.DataFrame) -> pd.DataFrame:
    stats_df["SOV"] = 0.0
    stats_df["SOS"] = 0.0
    for team_id, row in stats_df.iterrows():
        beaten = row["Beaten_Opponents"]
        if beaten:
            sov_sum = stats_df.loc[stats_df.index.isin(beaten), "overall_win_pct"].sum()
            stats_df.loc[team_id, "SOV"] = sov_sum / len(beaten)
        opponents = row["Opponents"]
        if opponents:
            sos_sum = stats_df.loc[
                stats_df.index.isin(opponents),
                "overall_win_pct",
            ].sum()
            stats_df.loc[team_id, "SOS"] = sos_sum / len(opponents)

    return stats_df.replace([math.inf, -math.inf], 0)


def calculate_standings(
    games_df: pd.DataFrame,
    divisions_df: pd.DataFrame,
    teams_df: pd.DataFrame,
) -> pd.DataFrame:
    if games_df is None or games_df.empty:
        stats_df = _init_empty_standings(teams_df)
        stats_df.attrs["no_games"] = True
        return stats_df

    stats_df = _init_empty_standings(teams_df)
    stats_df = _process_game_results(stats_df, games_df)
    stats_df = _apply_conf_div_stats(stats_df, games_df, divisions_df)
    stats_df = _merge_and_compute_basic_pct(stats_df, teams_df, divisions_df)
    stats_df = _compute_sov_sos(stats_df)
    return stats_df.fillna(0)


def get_head_to_head_record(
    team_ids: list[int],
    games_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Returns a DataFrame with head-to-head win % for each team in team_ids
    against the other tied teams.
    """
    h2h_win_pct = dict.fromkeys(team_ids, 0.0)

    tied_games = games_df[
        (games_df["home_team_id"].isin(team_ids))
        & (games_df["away_team_id"].isin(team_ids))
    ]

    if tied_games.empty:
        return pd.DataFrame(
            {"team_id": team_ids, "head_to_head_pct": [0.0] * len(team_ids)},
        )

    for tid in team_ids:
        wins, losses, ties = 0, 0, 0
        team_games = tied_games[
            (tied_games["home_team_id"] == tid) | (tied_games["away_team_id"] == tid)
        ]
        for _, g in team_games.iterrows():
            if g["home_team_id"] == tid:
                if g["home_team_score"] > g["away_team_score"]:
                    wins += 1
                elif g["home_team_score"] < g["away_team_score"]:
                    losses += 1
                else:
                    ties += 1
            elif g["away_team_id"] == tid:
                if g["away_team_score"] > g["home_team_score"]:
                    wins += 1
                elif g["away_team_score"] < g["home_team_score"]:
                    losses += 1
                else:
                    ties += 1
        total = wins + losses + ties
        h2h_win_pct[tid] = (wins + 0.5 * ties) / total if total > 0 else 0.0

    return pd.DataFrame(
        {
            "team_id": list(h2h_win_pct.keys()),
            "head_to_head_pct": list(h2h_win_pct.values()),
        },
    )


def get_common_games(team_ids: list[int], games_df: pd.DataFrame) -> list[int]:
    """Finds common opponents for a list of teams."""
    games_by_team = {tid: set() for tid in team_ids}
    all_games = games_df[
        (games_df["home_team_id"].isin(team_ids))
        | (games_df["away_team_id"].isin(team_ids))
    ]

    for _, g in all_games.iterrows():
        home, away = g["home_team_id"], g["away_team_id"]
        if home in games_by_team:
            games_by_team[home].add(away)
        if away in games_by_team:
            games_by_team[away].add(home)

    common_opponents = set.intersection(*(games_by_team[tid] for tid in team_ids))
    return list(common_opponents)


def get_common_game_record(
    team_id: int,
    common_opponents: list[int],
    games_df: pd.DataFrame,
) -> float:
    """Calculates a team's record against a list of common opponents."""
    wins, losses, ties = 0, 0, 0
    games = games_df[
        (
            (games_df["home_team_id"] == team_id)
            & (games_df["away_team_id"].isin(common_opponents))
        )
        | (
            (games_df["away_team_id"] == team_id)
            & (games_df["home_team_id"].isin(common_opponents))
        )
    ]
    for _, game in games.iterrows():
        if game["home_team_id"] == team_id:
            if game["home_team_score"] > game["away_team_score"]:
                wins += 1
            elif game["home_team_score"] < game["away_team_score"]:
                losses += 1
            else:
                ties += 1
        elif game["away_team_score"] > game["home_team_score"]:
            wins += 1
        elif game["away_team_score"] < game["home_team_score"]:
            losses += 1
        else:
            ties += 1

    total_games = wins + losses + ties
    if total_games == 0:
        return 0
    return (wins + 0.5 * ties) / total_games


def apply_tie_breakers(
    tied_df: pd.DataFrame,
    games_df: pd.DataFrame,
    tie_type: str,
) -> pd.DataFrame:
    """
    Applies NFL tie-breaking for tied teams (multi-team supported) safely.
    """
    if len(tied_df) <= 1:
        return tied_df.sort_values(by="overall_win_pct", ascending=False)

    team_ids = tied_df["team_id"].tolist()

    h2h_df = get_head_to_head_record(team_ids, games_df)
    tied_df = tied_df.merge(h2h_df, on="team_id", how="left")

    sort_cols = ["head_to_head_pct"]
    if tie_type == "Division":
        sort_cols.append("division_win_pct")
    else:
        sort_cols.append("conference_win_pct")
    sort_cols += ["SOV", "SOS"]

    tied_df = tied_df.sort_values(by=sort_cols, ascending=False)

    return tied_df.drop(columns=["head_to_head_pct"], errors="ignore")


def display_standings(df: pd.DataFrame, group_col: str, tie_type: str) -> None:
    """Display standings grouped by a specified column with proper tie-breakers applied."""
    unique_groups = sorted(df[group_col].unique())

    for group in unique_groups:
        st.subheader(f"{group}", anchor=False)
        group_df = df[df[group_col] == group].copy()

        group_df["rank"] = group_df["overall_win_pct"].rank(
            method="dense",
            ascending=False,
        )
        final_sorted_list = []

        for _, tied_group in group_df.groupby("rank"):
            if len(tied_group) > 1:
                sorted_group = apply_tie_breakers(tied_group, games_data, tie_type)
                final_sorted_list.append(sorted_group)
            else:
                final_sorted_list.append(tied_group)

        final_sorted_df = pd.concat(final_sorted_list).reset_index(drop=True)

        display_df = final_sorted_df[
            ["name", "Wins", "Losses", "Ties", "overall_win_pct"]
        ].rename(columns={"name": "Team", "overall_win_pct": "Win %"})
        display_df.index = range(1, len(display_df) + 1)
        display_df.index.name = "Rank"

        display_table(display_df, highlight=1, column_widths=[60, 200, 70, 70, 70, 90])


games_data, divisions_data, teams_data = load_data()
if (
    games_data is not None
    and divisions_data is not None
    and teams_data is not None
    and not games_data.empty
):
    full_standings_df = calculate_standings(games_data, divisions_data, teams_data)
    st.markdown(
        "Select an option below to view either the conference or division standings.",
    )
    view_mode = st.radio(
        "Select View Mode",
        ["Division Standings", "Conference Standings"],
    )

    if view_mode == "Conference Standings":
        st.divider()
        st.header("Conference Standings", anchor=False)
        st.divider()
        cols = st.columns(2)
        col_i = 0
        for conf in ["AFC", "NFC"]:
            with cols[col_i]:
                st.subheader(f"{conf} Conference", anchor=False)

                conf_df = full_standings_df[
                    full_standings_df["conference"] == conf
                ].copy()

                division_winners = pd.DataFrame()
                for div in conf_df["division"].unique():
                    division_df = conf_df[conf_df["division"] == div].copy()
                    division_df["rank"] = division_df["overall_win_pct"].rank(
                        method="min",
                        ascending=False,
                    )
                    first_place = division_df[division_df["rank"] == 1]
                    if len(first_place) > 1:
                        first_place = apply_tie_breakers(
                            first_place,
                            games_data,
                            "Division",
                        ).head(1)
                    division_winners = pd.concat([division_winners, first_place])

                    division_winners["rank"] = division_winners["overall_win_pct"].rank(
                        method="dense",
                        ascending=False,
                    )
                    final_sorted_list = []
                    for _, tied_group in division_winners.groupby("rank"):
                        if len(tied_group) > 1:
                            sorted_group = apply_tie_breakers(
                                tied_group,
                                games_data,
                                "Division",
                            )
                            final_sorted_list.append(sorted_group)
                        else:
                            final_sorted_list.append(tied_group)

                    division_winners = pd.concat(final_sorted_list).reset_index(
                        drop=True,
                    )

                remaining_teams = conf_df[
                    ~conf_df["team_id"].isin(division_winners["team_id"])
                ].copy()
                remaining_teams["rank"] = remaining_teams["overall_win_pct"].rank(
                    method="dense",
                    ascending=False,
                )
                sorted_wc_list = []

                for _, tied_group in remaining_teams.groupby("rank"):
                    if len(tied_group) > 1:
                        sorted_wc_list.append(
                            apply_tie_breakers(
                                tied_group,
                                games_data,
                                "Conference",
                            ),
                        )
                    else:
                        sorted_wc_list.append(tied_group)

                sorted_wild_card_teams = pd.concat(sorted_wc_list).reset_index(
                    drop=True,
                )

                final_conf_standings = pd.concat(
                    [division_winners, sorted_wild_card_teams],
                ).reset_index(drop=True)

                display_df = final_conf_standings[
                    ["name", "Wins", "Losses", "Ties", "overall_win_pct"]
                ].rename(columns={"name": "Team", "overall_win_pct": "Win %"})
                display_df.index = range(1, len(display_df) + 1)
                display_df.index.name = "Rank"
                display_table(
                    display_df,
                    highlight=4,
                    highlight2=7,
                    column_widths=[60, 200, 70, 70, 70, 90],
                )
                col_i += 1

    else:
        st.divider()
        st.header("Division Standings", anchor=False)
        st.divider()
        cols = st.columns(2)
        col_i = 0
        for conf in ["AFC", "NFC"]:
            with cols[col_i]:
                st.subheader(f"{conf} Conference", anchor=False)
                conf_df = full_standings_df[
                    full_standings_df["conference"] == conf
                ].copy()
                display_standings(conf_df, "division", "Division")
                col_i += 1
else:
    st.error("No games were played yet. Let's wait til the season starts.")
