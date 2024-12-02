import streamlit as st

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent / "streamlit"))
sys.path.append(str(Path(__file__).resolve().parent / "streamlit/sources"))
import sql

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# Streamlit App with Navigation
def main():
    st.set_page_config(layout="wide")

    st.markdown("""
        <style>
        div[data-testid="stSidebarCollapseButton"] { 
            display: none;
        }
        a[data-testid="stSidebarNavLink"] {
        background-color: rgba(255,255,255,0.1)  !important      
        }
        </style>
        """, unsafe_allow_html=True)

    st.logo("streamlit/images/sidebar.png", size='large')
    page = st.navigation({"General pages": [st.Page("streamlit/start.py", title="Home Page", default=True), st.Page("streamlit/schedule.py", title="Schedule"), st.Page("streamlit/details.py", title="Teams")], "Analyzing Tools": [st.Page("streamlit/prediction.py", title="PlayAnalyzer"), st.Page("streamlit/chatbot.py", title="NFLBot"), st.Page("streamlit/news.py", title="NewsBot"), st.Page("streamlit/drawing.py", title="LogoRecognizer")], "More Information":[st.Page("streamlit/data.py", title="Data Aquisition"), st.Page("streamlit/models.py", title="ML/AI models")]})

    page.run()

if __name__ == "__main__":
    main() 
    