import streamlit as st
import streamlit_nested_layout as stnl

st.title("Model descriptions", anchor=False)

st.write("On this page you can find a brief summary of the chosen approaches for each tool on this app.")

with st.expander("PlayAnalyzer (play type)"):
    st.write("Data from almost all tables is used for the analysis. Furthermore, the data is transformed such that the (home-team, away-team) combination is mapped to the respective (offense-team, defense-team) one for each single play. Toggle to display queries:")
    if st.toggle("Show SQL queries"):
        st.code("""WITH play_stats AS (
        SELECT
            p.play_id,
            p.game_id,
            p.sequenceNumber,
            p.quarter,
            TIME_TO_SEC(p.clock) AS clock_seconds,
            p.offenseAtHome,
            p.down,
            p.distance,
            p.yardsToEndzone,
            p.playtype_id,
            g.season,
            g.game_type,
            g.week,
            CASE 
                WHEN p.offenseAtHome = TRUE THEN p.homeScore
                ELSE p.awayScore
            END AS offenseScore,
            CASE 
                WHEN p.offenseAtHome = FALSE THEN p.homeScore
                ELSE p.awayScore
            END AS defenseScore,
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
            t1.abbreviation AS offenseAbr,
            t2.abbreviation AS defenseAbr,
            CASE 
                WHEN p.offenseAtHome = TRUE THEN (p.homeScore - p.awayScore)
                ELSE (p.awayScore - p.homeScore)
            END AS scoreDiff,
            (TIME_TO_SEC(p.clock) + (4 - p.quarter) * 15 * 60) AS totalTimeLeft
        FROM
            nfl.plays p
        LEFT JOIN nfl.games g ON p.game_id = g.game_id
        LEFT JOIN nfl.teams t1 ON 
            (p.offenseAtHome = TRUE AND g.home_team_id = t1.team_id) OR
            (p.offenseAtHome = FALSE AND g.away_team_id = t1.team_id)
        LEFT JOIN nfl.teams t2 ON 
            (p.offenseAtHome = TRUE AND g.away_team_id = t2.team_id) OR
            (p.offenseAtHome = FALSE AND g.home_team_id = t2.team_id)
        WHERE
            g.season IN {years}
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
            WHERE g.season IN {years}
        )
        SELECT ps.*, pa.completionRate, pa.passToRushRatio
        FROM play_stats ps
        JOIN play_aggregates pa ON ps.play_id = pa.play_id;""")

with st.expander("PlayAnalyzer (win probability)"):
    st.write("Under construction...")

with st.expander("ChatBot"):
        st.markdown("""A langchain model is used for conversation. The model is trained on three different kinds of input:""")
                
        st.markdown(""" - "Rule Book": the official rule set obtained from nfl.com for the current season.
                    
- "Glossary": A collection of NFL related terms and their explanation from various places online.

- "News": All news published on ESPN.com during the last 7 days.
                                    
The stored information is then used in a retrievel chain including a memory, i.e., the ChatBot will remember the previous messages and can include them in his further replies.
                                """)

with st.expander("NewsBots"):
    with st.expander("NewsBot (summarization)"):
        st.write("News from the last 10 days can be chosen. The underlying llm model is")
        st.code("""llm = ChatGroq(groq_api_key={GROQ_TOKEN},
                    model_name="mixtral-8x7b-32768")""", language="python")
        st.write("An llm-chain is then used in combination with a prompt template to instruct the llm how do respond.")
        st.code("LLMChain(llm=llm, prompt={prompt})", language="python")
    with st.expander("NewsBot (podcast)"):
        st.write("Under construction...")


with st.expander("LogoRecognizer"):
    st.write("A convolutional neural network (CNN) is used to classify the drawn logos into one of the 32 NFL teams. The model is trained on a dataset of about XXX images containing logos of all teams. The images are augmented during training using random transformations such as rotation, zoom, and horizontal flip to improve the model's generalization ability.")
