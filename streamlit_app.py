import streamlit as st

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent / "streamlit"))

def main():
    st.set_page_config(layout="wide")
    st.set_option('client.showErrorDetails', False)

    st.markdown("""
        <style>
        div[data-testid="stSidebarCollapseButton"] { 
            display: none;
        }
        a[data-testid="stSidebarNavLink"] {
        background-color: rgba(255,255,255,0.1)  !important      
        }
        a[data-testid="stSidebarNavLink"][aria-current="page"] {
        background-color: #4CAF50;  /* Green color for active link */
        color: white;  /* White text */
        font-weight: bold;  /* Bold text */
    }
        </style>
        """, unsafe_allow_html=True)

    st.logo("streamlit/images/sidebar.png", size='large')

    page = st.navigation({
        "General pages": [
            st.Page("streamlit/start.py", title="Home Page", icon=":material/home:", default=True),
            st.Page("streamlit/schedule.py", title="Schedule", icon=":material/calendar_clock:"),
            st.Page("streamlit/standings.py", title="Standings", icon=":material/social_leaderboard:"),
            st.Page("streamlit/details.py", title="Teams", icon=":material/groups:")
        ],
        "ML/AI Tools": [
            st.Page("streamlit/prediction.py", title="PlayPredictor", icon=":material/sports_football:"),
            st.Page("streamlit/chatbot.py", title="ChatBot", icon=":material/chat:"),
            st.Page("streamlit/news.py", title="NewsBots", icon=":material/newspaper:"),
            st.Page("streamlit/drawing.py", title="LogoRecognizer", icon=":material/image_search:"),
            st.Page("streamlit/memes.py", title="MemeExplainer", icon=":material/school:"), 
        ],
        "Information": [
            st.Page("streamlit/data.py", title="Data Acquisition", icon=":material/storage:"),
            st.Page("streamlit/models.py", title="ML/AI models", icon=":material/dashboard:"),
            st.Page("streamlit/streamlit.py", title="Streamlit functionalities", icon=":material/chess_queen:"),
            st.Page("streamlit/wbs.py", title="WBS bootcamp", icon=":material/camping:")
        ],
        "More": [
            st.Page("streamlit/chat.py", title="Chat", icon=":material/forum:"),
            st.Page("streamlit/feedback.py", title="Provide Feedback", icon=":material/feedback:"),
            st.Page("streamlit/login.py", title="User Login", icon=":material/lock_open:"),
            st.Page("streamlit/games.py", title="Games", icon=":material/sports_esports:"),
        ]
    })

    page.run()

if __name__ == "__main__":
    main() 
    