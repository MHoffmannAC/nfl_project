import streamlit as st
st.image("streamlit/images/new_header.png", width=1000)
st.header("Welcome to the NFL Gameday Analysis App!", anchor=False)

st.markdown("Use the sidebar or the list below to navigate to different sections of the app:")

st.markdown(
    """
    <style>
    .st-emotion-cache-1jly7o7 {
        background-color: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.divider()
st.subheader("General Pages:")

st.page_link("streamlit/start.py", label="**Home Page**: Come back to this page.", icon=":material/home:")
st.page_link("streamlit/schedule.py", label="**Game Schedule**: Check the Schedule of the NFL.", icon=":material/calendar_clock:")
st.page_link("streamlit/standings.py", label="**League Standings**: Check out the latest division and conference standings", icon=":material/social_leaderboard:")
st.page_link("streamlit/details.py", label="**Teams**: Analyze teams and their rosters.", icon=":material/groups:")

st.divider()
st.subheader("ML/AI Tools:")
             
st.page_link("streamlit/prediction.py", label="**PlayPredictor**: Perform Live analysis of running games and predict the next play type.", icon=":material/sports_football:")
st.page_link("streamlit/chatbot.py", label="**ChatBot**: Discuss the latest NFL news, glossary, and rules with the well informed NFLBot.", icon=":material/chat:")
st.page_link("streamlit/news.py", label="**NewsBots**: Get summaries of recent news or listen to AI generated podcasts.", icon=":material/newspaper:")
st.page_link("streamlit/drawing.py", label="**LogoRecognizer**: Test your drawing skills and let an AI guess your favorite team.", icon=":material/image_search:")
st.page_link("streamlit/memes.py", label="**MemeExplainer**: Check how an AI struggles to explain memes.", icon=":material/school:")

st.divider()
st.subheader("Information:")
             
st.page_link("streamlit/data.py", label="**DataAquisition**: Learn more about the underlying data and its origins.", icon=":material/storage:")
st.page_link("streamlit/models.py", label="**ML/AI models**: Explanation of the different machine learning models and generative AIs.", icon=":material/dashboard:")
st.page_link("streamlit/streamlit.py", label="**Streamlit**: Get an overview of in-built streamlit functionalities as well as external libraries used", icon=":material/chess_queen:")
st.page_link("streamlit/wbs.py", label="**Data Science**: Brief explanation about the origins of this project.", icon=":material/camping:")

st.divider()
st.subheader("More:")
             
st.page_link("streamlit/chat.py", label="**Chat**: Chat with other users.", icon=":material/forum:")
st.page_link("streamlit/feedback.py", label="**Provide Feedback**: Let me know what could be done to improve the app or report bugs.", icon=":material/feedback:")
st.page_link("streamlit/login.py", label="**User Login**: Login to get user or admin rights.", icon=":material/lock_open:")
st.page_link("streamlit/games.py", label="**Games**: Some NFL-themed games (Tic-Tac-Toe, Hangman, Sudokus, PixelLogos).", icon=":material/sports_esports:")

st.divider()