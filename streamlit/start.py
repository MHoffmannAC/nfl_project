import streamlit as st
st.image("streamlit/images/header.png")
st.title("Welcome to the NFL Game Analysis App!")

st.markdown("""
Use the sidebar to navigate to different sections of the app:
- **Home Page**: come back to this page.
- **Schedule**: Check the Schedule of the NFL.
- **Teams**: Analyze teams and their rosters.
""")
st.markdown("""
- **PlayAnalyzer**: Perform Live Analysis of running games.
- **ChatBot**: Discuss the latest NFL news, glossary, and rules with the well informed NFLBot.
- **NewsBOT**: Get summaries of recent news.
- **LogoRecognizer**: Test your drawing skills and let an AI guess your favorite team.
""")
st.markdown("""
- **DataAquisition**: Learn more about the underlying data and its origins.
- **ML/AI models**: Explanation of the different machine learning models and generative AIs.
- **Provide Feedback**: Let me know what could be done to improve the app or report bugs.
""")