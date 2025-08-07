def query_plays(game_id):
    query = f""" 
            WITH play_stats AS (
                SELECT
                    p.play_id,
                    p.game_id,
                    p.sequenceNumber,
                    p.quarter,
                    TIME_TO_SEC(p.clock) AS clock_seconds,
                    p.playtype_id,
                    p.offenseAtHome,
                    p.possessionChange,
                    p.down,
                    p.distance,
                    p.yardsToEndzone,
                    p.next_down,
                    p.next_distance,
                    p.next_yardsToEndzone,
                    g.season,
                    g.game_type,
                    g.week,
                    p.homeScore,
                    p.awayScore,
                    CASE
                        WHEN p.offenseAtHome = TRUE THEN p.homeScore
                        ELSE p.awayScore
                    END AS offenseScore,
                    CASE
                        WHEN p.offenseAtHome = FALSE THEN p.homeScore
                        ELSE p.awayScore
                    END AS defenseScore,
                    g.standing_home_overall_win,
                    g.standing_home_home_win,
                    g.standing_home_road_win,
                    g.standing_home_overall_loss,
                    g.standing_home_home_loss,
                    g.standing_home_road_loss,
                    g.standing_away_overall_win,
                    g.standing_away_home_win,
                    g.standing_away_road_win,
                    g.standing_away_overall_loss,
                    g.standing_away_home_loss,
                    g.standing_away_road_loss,
                    CASE 
                        WHEN p.offenseAtHome = TRUE THEN g.standing_home_overall_win
                        ELSE g.standing_away_overall_win
                    END AS standing_offense_overall_win,
                    CASE 
                        WHEN p.offenseAtHome = TRUE THEN g.standing_home_home_win
                        ELSE g.standing_away_home_win
                    END AS standing_offense_home_win,
                    CASE 
                        WHEN p.offenseAtHome = TRUE THEN g.standing_home_road_win
                        ELSE g.standing_away_road_win
                    END AS standing_offense_road_win,
                    CASE 
                        WHEN p.offenseAtHome = TRUE THEN g.standing_home_overall_loss
                        ELSE g.standing_away_overall_loss
                    END AS standing_offense_overall_loss,
                    CASE 
                        WHEN p.offenseAtHome = TRUE THEN g.standing_home_home_loss
                        ELSE g.standing_away_home_loss
                    END AS standing_offense_home_loss,
                    CASE 
                        WHEN p.offenseAtHome = TRUE THEN g.standing_home_road_loss
                        ELSE g.standing_away_road_loss
                    END AS standing_offense_road_loss,
                    CASE 
                        WHEN p.offenseAtHome = FALSE THEN g.standing_home_overall_win
                        ELSE g.standing_away_overall_win
                    END AS standing_defense_overall_win,
                    CASE 
                        WHEN p.offenseAtHome = FALSE THEN g.standing_home_home_win
                        ELSE g.standing_away_home_win
                    END AS standing_defense_home_win,
                    CASE 
                        WHEN p.offenseAtHome = FALSE THEN g.standing_home_road_win
                        ELSE g.standing_away_road_win
                    END AS standing_defense_road_win,
                    CASE 
                        WHEN p.offenseAtHome = FALSE THEN g.standing_home_overall_loss
                        ELSE g.standing_away_overall_loss
                    END AS standing_defense_overall_loss,
                    CASE 
                        WHEN p.offenseAtHome = FALSE THEN g.standing_home_home_loss
                        ELSE g.standing_away_home_loss
                    END AS standing_defense_home_loss,
                    CASE 
                        WHEN p.offenseAtHome = FALSE THEN g.standing_home_road_loss
                        ELSE g.standing_away_road_loss
                    END AS standing_defense_road_loss,
                    t1.abbreviation AS homeAbr,
                    t1.name AS homeName,
                    t1.color AS homeColor,
                    t2.abbreviation AS awayAbr,
                    t2.name AS awayName,
                    t2.color AS awayColor,
                    CASE
                        WHEN p.offenseAtHome = TRUE THEN t1.abbreviation
                        ELSE t2.abbreviation
                    END AS offenseAbr,
                    CASE
                        WHEN p.offenseAtHome = FALSE THEN t1.abbreviation
                        ELSE t2.abbreviation
                    END AS defenseAbr,
                    (TIME_TO_SEC(p.clock) + (4 - p.quarter) * 15 * 60) AS totalTimeLeft,
                    (p.homeScore - p.awayScore) AS scoreDiff
                FROM
                    nfl.plays p
                LEFT JOIN nfl.games g ON p.game_id = g.game_id
                LEFT JOIN nfl.teams t1 ON 
                    g.home_team_id = t1.team_id
                LEFT JOIN nfl.teams t2 ON 
                    g.away_team_id = t2.team_id
                WHERE
                    g.game_id = {game_id} AND p.playtype_id IN (3, 5, 6, 17, 18, 24, 26, 30, 34, 36, 37, 38, 40, 41, 51, 52, 59, 60, 67, 68)
            ),
            play_aggregates AS (
                SELECT
                    p1.game_id,
                    p1.play_id,
                    p1.sequenceNumber,
                    -- Completion Rate Calculation
                    (
                        SELECT 
                            COUNT(*) * 1.0 / NULLIF(
                                (SELECT COUNT(*) 
                                FROM nfl.plays p2 
                                WHERE p2.game_id = p1.game_id 
                                AND p2.sequenceNumber < p1.sequenceNumber 
                                AND p2.playtype_id IN (67, 51, 24, 3, 6, 26, 36)), 0
                            )
                        FROM nfl.plays p2
                        WHERE p2.game_id = p1.game_id 
                        AND p2.sequenceNumber < p1.sequenceNumber 
                        AND (p2.playtype_id IN (67, 24)
                            OR (p2.playtype_id = 51 AND p2.description NOT LIKE '%incomplete%')
                        )
                    ) AS completionRate,
                    -- Pass to Rush Ratio Calculation
                    (
                        SELECT 
                            COUNT(*) * 1.0 / NULLIF(
                                (SELECT COUNT(*) 
                                FROM nfl.plays p2 
                                WHERE p2.game_id = p1.game_id 
                                AND p2.sequenceNumber < p1.sequenceNumber 
                                AND p2.playtype_id IN (5, 68)), 0
                            )
                        FROM nfl.plays p2
                        WHERE p2.game_id = p1.game_id 
                        AND p2.sequenceNumber < p1.sequenceNumber 
                        AND p2.playtype_id IN (67, 51, 24, 3, 6, 26, 36)
                    ) AS passToRushRatio
                FROM nfl.plays p1
                LEFT JOIN nfl.games g ON p1.game_id = g.game_id
                WHERE 
                    g.game_id = {game_id}
            )
            SELECT ps.*, pa.completionRate, pa.passToRushRatio
            FROM play_stats ps
            JOIN play_aggregates pa ON ps.play_id = pa.play_id
            ORDER BY 
                ps.play_id ASC
            """
    return query

def query_week(week, season, game_type):
    query = f"""
            SELECT 
                g.game_id, p.play_id, th.name as home_team, p.homeScore as home_score, p.awayScore as away_score, ta.name as away_team, pb.homeWinPercentage as home_wp, pb.awayWinPercentage as away_wp, TIME_TO_SEC(p.clock) +  (4-p.quarter ) * 15 * 60 as time_left
            FROM
                probabilities pb
                    JOIN
                games g USING (game_id)
                    JOIN
                teams th ON th.team_id = g.home_team_id
                    JOIN
                teams ta ON ta.team_id = g.away_team_id
                    JOIN 
                plays p ON p.sequenceNumber = pb.sequenceNumber AND p.game_id = pb.game_id
            WHERE
                season = {season} AND week = {week} AND game_type = '{game_type}'
            ORDER BY
                g.game_id, p.play_id;
            """
    return query