import streamlit as st
import pandas as pd
import math

from sources.sql import create_sql_engine, get_current_week, query_db
sql_engine = create_sql_engine()
current_week, current_season, current_game_type = get_current_week()

st.title("NFL Standings", anchor=False)

# -----------------------------
# Data Loading
# -----------------------------
#@st.cache_data(ttl=600)  # cache for 10 minutes
def load_data():
    """Load standings, divisions, and teams from the database."""
    standings_df = pd.DataFrame(query_db(sql_engine, f"SELECT * FROM games WHERE season = {current_season} AND game_type = 'regular-season' AND game_status = 3"))
    divisions_df = pd.DataFrame(query_db(sql_engine, "SELECT * FROM divisions"))
    teams_df = pd.DataFrame(query_db(sql_engine, "SELECT * FROM teams WHERE team_id NOT IN (-2, -1, 31, 32, 38);"))
    return standings_df, divisions_df, teams_df

# -----------------------------
# Standings Calculation
# -----------------------------
def calculate_standings(games_df, divisions_df, teams_df):
    """Compute wins/losses/ties, conference/division stats, and head-to-head records."""
    if games_df is None or games_df.empty:
        st.info("No regular season games found. All team records are 0-0.")
        team_stats = teams_df.set_index('team_id').copy()
        team_stats['Wins'] = 0
        team_stats['Losses'] = 0
        team_stats['Ties'] = 0
        team_stats['overall_win_pct'] = 0.0
        return team_stats.merge(divisions_df, on='team_id', how='left')

    # Filter for regular season games and completed games
    if games_df.empty:
        st.info("No regular season games with game_status = 3 found. All team records are 0-0.")
        team_stats = teams_df.set_index('team_id').copy()
        team_stats['Wins'] = 0
        team_stats['Losses'] = 0
        team_stats['Ties'] = 0
        team_stats['overall_win_pct'] = 0.0
        return team_stats.merge(divisions_df, on='team_id', how='left')

    teams_list = teams_df['team_id'].tolist()
    team_stats = {
        'team_id': teams_list,
        'Wins': [0] * len(teams_list),
        'Losses': [0] * len(teams_list),
        'Ties': [0] * len(teams_list),
        'Points_Scored': [0] * len(teams_list),
        'Points_Allowed': [0] * len(teams_list),
        'Conference_Wins': [0] * len(teams_list),
        'Conference_Losses': [0] * len(teams_list),
        'Conference_Ties': [0] * len(teams_list),
        'Division_Wins': [0] * len(teams_list),
        'Division_Losses': [0] * len(teams_list),
        'Division_Ties': [0] * len(teams_list),
        'Opponents': [[] for _ in range(len(teams_list))],
        'Beaten_Opponents': [[] for _ in range(len(teams_list))]
    }
    stats_df = pd.DataFrame(team_stats).set_index('team_id')

    # Calculate overall wins/losses/ties
    for _, row in games_df.iterrows():
        home_id, away_id = row['home_team_id'], row['away_team_id']
        home_score, away_score = row['home_team_score'], row['away_team_score']

        if home_id in stats_df.index:
            stats_df.at[home_id, 'Points_Scored'] += home_score
            stats_df.at[home_id, 'Points_Allowed'] += away_score
            stats_df.at[home_id, 'Opponents'].append(away_id)
        if away_id in stats_df.index:
            stats_df.at[away_id, 'Points_Scored'] += away_score
            stats_df.at[away_id, 'Points_Allowed'] += home_score
            stats_df.at[away_id, 'Opponents'].append(home_id)

        if home_score > away_score:
            if home_id in stats_df.index:
                stats_df.at[home_id, 'Wins'] += 1
                stats_df.at[home_id, 'Beaten_Opponents'].append(away_id)
            if away_id in stats_df.index:
                stats_df.at[away_id, 'Losses'] += 1
        elif away_score > home_score:
            if away_id in stats_df.index:
                stats_df.at[away_id, 'Wins'] += 1
                stats_df.at[away_id, 'Beaten_Opponents'].append(home_id)
            if home_id in stats_df.index:
                stats_df.at[home_id, 'Losses'] += 1
        else:
            if home_id in stats_df.index:
                stats_df.at[home_id, 'Ties'] += 1
            if away_id in stats_df.index:
                stats_df.at[away_id, 'Ties'] += 1

    # Calculate conference and division records
    for team_id in stats_df.index:
        team_div_info = divisions_df[divisions_df['team_id'] == team_id]
        if team_div_info.empty:
            continue
        team_conference = team_div_info['conference'].iloc[0]
        team_division = team_div_info['division'].iloc[0]

        team_games = games_df[(games_df['home_team_id'] == team_id) | (games_df['away_team_id'] == team_id)].copy()
        
        # Conference record
        opponents_in_conf = divisions_df[divisions_df['conference'] == team_conference]['team_id'].tolist()
        for _, game in team_games.iterrows():
            opp_id = game['away_team_id'] if game['home_team_id'] == team_id else game['home_team_id']
            if opp_id in opponents_in_conf:
                if (game['home_team_score'] > game['away_team_score'] and game['home_team_id'] == team_id) or \
                   (game['away_team_score'] > game['home_team_score'] and game['away_team_id'] == team_id):
                    stats_df.at[team_id, 'Conference_Wins'] += 1
                elif game['home_team_score'] == game['away_team_score']:
                    stats_df.at[team_id, 'Conference_Ties'] += 1
                else:
                    stats_df.at[team_id, 'Conference_Losses'] += 1

        # Division record
        opponents_in_div = divisions_df[divisions_df['division'] == team_division]['team_id'].tolist()
        for _, game in team_games.iterrows():
            opp_id = game['away_team_id'] if game['home_team_id'] == team_id else game['home_team_id']
            if opp_id in opponents_in_div:
                if (game['home_team_score'] > game['away_team_score'] and game['home_team_id'] == team_id) or \
                   (game['away_team_score'] > game['home_team_score'] and game['away_team_id'] == team_id):
                    stats_df.at[team_id, 'Division_Wins'] += 1
                elif game['home_team_score'] == game['away_team_score']:
                    stats_df.at[team_id, 'Division_Ties'] += 1
                else:
                    stats_df.at[team_id, 'Division_Losses'] += 1

    stats_df = stats_df.merge(divisions_df, on='team_id', how='left')
    stats_df = stats_df.merge(teams_df, on='team_id', how='left')
    stats_df['Total_Games'] = stats_df['Wins'] + stats_df['Losses'] + stats_df['Ties']
    stats_df['overall_win_pct'] = (stats_df['Wins'] + 0.5 * stats_df['Ties']) / stats_df['Total_Games']
    stats_df['division_win_pct'] = (stats_df['Division_Wins'] + 0.5 * stats_df['Division_Ties']) / (stats_df['Division_Wins'] + stats_df['Division_Losses'] + stats_df['Division_Ties'])
    stats_df['conference_win_pct'] = (stats_df['Conference_Wins'] + 0.5 * stats_df['Conference_Ties']) / (stats_df['Conference_Wins'] + stats_df['Conference_Losses'] + stats_df['Conference_Ties'])
    
    # Calculate SOV and SOS
    stats_df['SOV'] = 0.0
    stats_df['SOS'] = 0.0
    for team_id, row in stats_df.iterrows():
        beaten_opponents = row['Beaten_Opponents']
        if beaten_opponents:
            sov_sum = stats_df[stats_df['team_id'].isin(beaten_opponents)]['overall_win_pct'].sum()
            stats_df.loc[team_id, 'SOV'] = sov_sum / len(beaten_opponents)
        
        all_opponents = row['Opponents']
        if all_opponents:
            sos_sum = stats_df[stats_df['team_id'].isin(all_opponents)]['overall_win_pct'].sum()
            stats_df.loc[team_id, 'SOS'] = sos_sum / len(all_opponents)

    stats_df.replace([math.inf, -math.inf], 0, inplace=True)
    stats_df.fillna(0, inplace=True)
    return stats_df

# -----------------------------
# Tie-Breaking Logic
# -----------------------------
def get_head_to_head_record(team1_id, team2_id, games_df):
    """Calculates head-to-head record between two teams."""
    head_to_head_games = games_df[
        ((games_df['home_team_id'] == team1_id) & (games_df['away_team_id'] == team2_id)) |
        ((games_df['home_team_id'] == team2_id) & (games_df['away_team_id'] == team1_id))
    ]
    wins1, losses1, ties1 = 0, 0, 0
    if not head_to_head_games.empty:
        for _, game in head_to_head_games.iterrows():
            if game['home_team_id'] == team1_id:
                if game['home_team_score'] > game['away_team_score']: wins1 += 1
                elif game['home_team_score'] < game['away_team_score']: losses1 += 1
                else: ties1 += 1
            else:
                if game['away_team_score'] > game['home_team_score']: wins1 += 1
                elif game['away_team_score'] < game['home_team_score']: losses1 += 1
                else: ties1 += 1
    return wins1, losses1, ties1

def get_common_games(team_ids, games_df):
    """Finds common opponents for a list of teams."""
    all_games = games_df[
        (games_df['home_team_id'].isin(team_ids)) | (games_df['away_team_id'].isin(team_ids))
    ]
    
    games_by_team = {team_id: set() for team_id in team_ids}
    for _, game in all_games.iterrows():
        home, away = game['home_team_id'], game['away_team_id']
        if home in games_by_team and away in games_by_team:
            continue
        if home in games_by_team: games_by_team[home].add(away)
        if away in games_by_team: games_by_team[away].add(home)
    
    if len(team_ids) < 2:
        return []
    
    common_opponents = games_by_team[team_ids[0]]
    for i in range(1, len(team_ids)):
        common_opponents = common_opponents.intersection(games_by_team[team_ids[i]])

    return list(common_opponents)

def get_common_game_record(team_id, common_opponents, games_df):
    """Calculates a team's record against a list of common opponents."""
    wins, losses, ties = 0, 0, 0
    games = games_df[
        ((games_df['home_team_id'] == team_id) & (games_df['away_team_id'].isin(common_opponents))) |
        ((games_df['away_team_id'] == team_id) & (games_df['home_team_id'].isin(common_opponents)))
    ]
    for _, game in games.iterrows():
        if game['home_team_id'] == team_id:
            if game['home_team_score'] > game['away_team_score']: wins += 1
            elif game['home_team_score'] < game['away_team_score']: losses += 1
            else: ties += 1
        else:
            if game['away_team_score'] > game['home_team_score']: wins += 1
            elif game['away_team_score'] < game['home_team_score']: losses += 1
            else: ties += 1
    
    total_games = wins + losses + ties
    if total_games == 0:
        return 0
    return (wins + 0.5 * ties) / total_games

def apply_tie_breakers(tied_df, full_standings_df, games_df, tie_type):
    """Applies NFL tie-breaking procedures to a DataFrame of tied teams."""
    if len(tied_df) <= 1:
        return tied_df

    # Division Tiebreakers
    if tie_type == 'Division':
        # 1. Head-to-head (if only two clubs)
        if len(tied_df) == 2:
            team1, team2 = tied_df.iloc[0]['team_id'], tied_df.iloc[1]['team_id']
            wins1, _, _ = get_head_to_head_record(team1, team2, games_df)
            wins2, _, _ = get_head_to_head_record(team2, team1, games_df)
            if wins1 > wins2:
                return pd.concat([tied_df.iloc[0:1], apply_tie_breakers(tied_df.iloc[1:2], full_standings_df, games_df, tie_type)])
            elif wins2 > wins1:
                return pd.concat([tied_df.iloc[1:2], apply_tie_breakers(tied_df.iloc[0:1], full_standings_df, games_df, tie_type)])
        
        # 2. Best won-lost-tied percentage in games played within the division.
        division_sorted = tied_df.sort_values(by='division_win_pct', ascending=False)
        if len(division_sorted) > 1 and division_sorted.iloc[0]['division_win_pct'] > division_sorted.iloc[1]['division_win_pct']:
            winner = division_sorted.iloc[0:1]
            remaining = division_sorted.iloc[1:]
            return pd.concat([winner, apply_tie_breakers(remaining, full_standings_df, games_df, tie_type)])

        # 3. Best won-lost-tied percentage in common games.
        common_opponents = get_common_games(tied_df['team_id'].tolist(), games_df)
        if len(common_opponents) > 0:
            for team_id in tied_df['team_id']:
                tied_df.loc[tied_df['team_id'] == team_id, 'common_win_pct'] = get_common_game_record(team_id, common_opponents, games_df)
            common_games_sorted = tied_df.sort_values(by='common_win_pct', ascending=False)
            if len(common_games_sorted) > 1 and common_games_sorted.iloc[0]['common_win_pct'] > common_games_sorted.iloc[1]['common_win_pct']:
                winner = common_games_sorted.iloc[0:1]
                remaining = common_games_sorted.iloc[1:]
                return pd.concat([winner, apply_tie_breakers(remaining, full_standings_df, games_df, tie_type)])

        # 4. Best won-lost-tied percentage in games played within the conference.
        conference_sorted = tied_df.sort_values(by='conference_win_pct', ascending=False)
        if len(conference_sorted) > 1 and conference_sorted.iloc[0]['conference_win_pct'] > conference_sorted.iloc[1]['conference_win_pct']:
            winner = conference_sorted.iloc[0:1]
            remaining = conference_sorted.iloc[1:]
            return pd.concat([winner, apply_tie_breakers(remaining, full_standings_df, games_df, tie_type)])

        # 5. Strength of victory in all games.
        sov_sorted = tied_df.sort_values(by='SOV', ascending=False)
        if len(sov_sorted) > 1 and sov_sorted.iloc[0]['SOV'] > sov_sorted.iloc[1]['SOV']:
            winner = sov_sorted.iloc[0:1]
            remaining = sov_sorted.iloc[1:]
            return pd.concat([winner, apply_tie_breakers(remaining, full_standings_df, games_df, tie_type)])

        # 6. Strength of schedule in all games.
        sos_sorted = tied_df.sort_values(by='SOS', ascending=False)
        if len(sos_sorted) > 1 and sos_sorted.iloc[0]['SOS'] > sos_sorted.iloc[1]['SOS']:
            winner = sos_sorted.iloc[0:1]
            remaining = sos_sorted.iloc[1:]
            return pd.concat([winner, apply_tie_breakers(remaining, full_standings_df, games_df, tie_type)])

    # Conference Tiebreakers
    elif tie_type == 'Conference':
        # 1. Head-to-head (if only two teams)
        if len(tied_df) == 2:
            team1, team2 = tied_df.iloc[0]['team_id'], tied_df.iloc[1]['team_id']
            wins1, _, _ = get_head_to_head_record(team1, team2, games_df)
            wins2, _, _ = get_head_to_head_record(team2, team1, games_df)
            if wins1 > wins2:
                return pd.concat([tied_df.iloc[0:1], apply_tie_breakers(tied_df.iloc[1:2], full_standings_df, games_df, tie_type)])
            elif wins2 > wins1:
                return pd.concat([tied_df.iloc[1:2], apply_tie_breakers(tied_df.iloc[0:1], full_standings_df, games_df, tie_type)])

        # 2. Best won-lost-tied percentage in games played within the conference.
        conference_sorted = tied_df.sort_values(by='conference_win_pct', ascending=False)
        if len(conference_sorted) > 1 and conference_sorted.iloc[0]['conference_win_pct'] > conference_sorted.iloc[1]['conference_win_pct']:
            winner = conference_sorted.iloc[0:1]
            remaining = conference_sorted.iloc[1:]
            return pd.concat([winner, apply_tie_breakers(remaining, full_standings_df, games_df, tie_type)])

        # 3. Best won-lost-tied percentage in common games (minimum of four).
        common_opponents = get_common_games(tied_df['team_id'].tolist(), games_df)
        if len(common_opponents) >= 4:
            for team_id in tied_df['team_id']:
                tied_df.loc[tied_df['team_id'] == team_id, 'common_win_pct'] = get_common_game_record(team_id, common_opponents, games_df)
            common_games_sorted = tied_df.sort_values(by='common_win_pct', ascending=False)
            if len(common_games_sorted) > 1 and common_games_sorted.iloc[0]['common_win_pct'] > common_games_sorted.iloc[1]['common_win_pct']:
                winner = common_games_sorted.iloc[0:1]
                remaining = common_games_sorted.iloc[1:]
                return pd.concat([winner, apply_tie_breakers(remaining, full_standings_df, games_df, tie_type)])
        
        # 4. Strength of victory in all games.
        sov_sorted = tied_df.sort_values(by='SOV', ascending=False)
        if len(sov_sorted) > 1 and sov_sorted.iloc[0]['SOV'] > sov_sorted.iloc[1]['SOV']:
            winner = sov_sorted.iloc[0:1]
            remaining = sov_sorted.iloc[1:]
            return pd.concat([winner, apply_tie_breakers(remaining, full_standings_df, games_df, tie_type)])

        # 5. Strength of schedule in all games.
        sos_sorted = tied_df.sort_values(by='SOS', ascending=False)
        if len(sos_sorted) > 1 and sos_sorted.iloc[0]['SOS'] > sos_sorted.iloc[1]['SOS']:
            winner = sos_sorted.iloc[0:1]
            remaining = sos_sorted.iloc[1:]
            return pd.concat([winner, apply_tie_breakers(remaining, full_standings_df, games_df, tie_type)])
    
    return tied_df.sort_values(by='overall_win_pct', ascending=False)

# -----------------------------
# Display Logic
# -----------------------------
def display_standings(df, group_col, tie_type):
    """Display standings grouped by a specified column."""
    unique_groups = sorted(df[group_col].unique())
    
    for group in unique_groups:
        st.subheader(f"{group}", anchor=False)
        group_df = df[df[group_col] == group].copy()
        
        # Group by win percentage to find ties
        group_df['rank'] = group_df['overall_win_pct'].rank(method='dense', ascending=False)
        tied_groups = group_df.groupby('rank')

        sorted_df_list = []
        for _, group in tied_groups:
            if len(group) > 1:
                sorted_group = apply_tie_breakers(group, df, games_data, tie_type)
                sorted_df_list.append(sorted_group)
            else:
                sorted_df_list.append(group)
        
        final_sorted_df = pd.concat(sorted_df_list)
        final_sorted_df = final_sorted_df.sort_values(by='overall_win_pct', ascending=False)

        # Re-assign ranks after tie-breaking
        final_sorted_df['final_rank'] = final_sorted_df['overall_win_pct'].rank(method='min', ascending=False).astype(int)
        display_df = final_sorted_df[['name', 'Wins', 'Losses', 'Ties', 'overall_win_pct']].rename(columns={'name': 'Team', 'overall_win_pct': 'Win %'})
        display_df.index = display_df['Win %'].rank(method='min', ascending=False).astype(int)
        display_df.index.name = 'Rank'

        st.table(display_df.drop('Win %', axis=1))


# -----------------------------
# Main App Logic
# -----------------------------
games_data, divisions_data, teams_data = load_data()
if games_data is not None and divisions_data is not None and teams_data is not None and  not games_data.empty:
    full_standings_df = calculate_standings(games_data, divisions_data, teams_data)
    st.markdown("Select an option below to view either the conference or division standings.")
    view_mode = st.radio("Select View Mode", ["Conference Standings", "Division Standings"])

    if view_mode == "Conference Standings":
        st.header("Conference Standings", anchor=False)
        for conf in ["AFC", "NFC"]:
            st.divider()
            st.subheader(f"{conf} Conference", anchor=False)
            
            conf_df = full_standings_df[full_standings_df['conference'] == conf].copy()
            
            # 1. Find the division winners for each conference
            division_winners = pd.DataFrame()
            for div in conf_df['division'].unique():
                division_df = conf_df[conf_df['division'] == div].copy()
                division_df['rank'] = division_df['overall_win_pct'].rank(method='min', ascending=False).astype(int)
                winner = division_df[division_df['rank'] == 1]
                
                # Apply tie-breakers if more than one team is tied for first
                if len(winner) > 1:
                    winner = apply_tie_breakers(winner, conf_df, games_data, 'Division').head(1)
                
                division_winners = pd.concat([division_winners, winner])
            
            # 2. Get the remaining teams (non-division winners)
            remaining_teams = conf_df[~conf_df['team_id'].isin(division_winners['team_id'])].copy()
            
            # 3. Sort the division winners for seeds 1-4
            division_winners = division_winners.sort_values(by='overall_win_pct', ascending=False)
            division_winners = apply_tie_breakers(division_winners, conf_df, games_data, 'Conference')
            
            # 4. Sort the remaining teams for seeds 5-7 (Wild Card)
            remaining_teams = remaining_teams.sort_values(by='overall_win_pct', ascending=False)
            remaining_teams['rank'] = remaining_teams['overall_win_pct'].rank(method='dense', ascending=False)
            tied_wc_groups = remaining_teams.groupby('rank')

            sorted_wc_list = []
            for _, group in tied_wc_groups:
                sorted_wc_list.append(apply_tie_breakers(group, conf_df, games_data, 'Conference'))
            
            sorted_wild_card_teams = pd.concat(sorted_wc_list).sort_values(by='overall_win_pct', ascending=False)
            
            # 5. Combine and display the full conference standings
            final_conf_standings = pd.concat([division_winners, sorted_wild_card_teams])
            
            display_df = final_conf_standings[['name', 'Wins', 'Losses', 'Ties', 'overall_win_pct']].rename(
                columns={'name': 'Team', 'overall_win_pct': 'Win %'}
            )
            display_df.index = range(1, len(display_df) + 1)
            display_df.index.name = 'Rank'
            st.table(display_df)

    else:
        st.header("Division Standings", anchor=False)
        for conf in ["AFC", "NFC"]:
            st.divider()
            st.subheader(f"{conf} Conference", anchor=False)
            conf_df = full_standings_df[full_standings_df['conference'] == conf].copy()
            display_standings(conf_df, 'division', 'Division')
else:
    st.error("No games were played yet. Let's wait til the season starts.")