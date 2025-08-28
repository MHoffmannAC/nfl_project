import streamlit as st
st.image("streamlit/images/header.png")
st.title("Welcome to the NFL Game Analysis App!")

st.markdown("Use the sidebar or the list below to navigate to different sections of the app:")


bulletpoint = "•&nbsp;&nbsp;&nbsp;"

st.divider()
st.write("General Pages:")

st.markdown("&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;"+"**Home Page**: come back to this page.")
st.page_link("streamlit/schedule.py", label=bulletpoint+"**Schedule**: Check the Schedule of the NFL.")
st.page_link("streamlit/details.py", label=bulletpoint+"**Teams**: Analyze teams and their rosters.")

st.divider()
st.write("ML/AI Tools:")
             
st.page_link("streamlit/prediction.py", label=bulletpoint+"**PlayAnalyzer**: Perform Live Analysis of running games.")
st.page_link("streamlit/chatbot.py", label=bulletpoint+"**ChatBot**: Discuss the latest NFL news, glossary, and rules with the well informed NFLBot.")
st.page_link("streamlit/news.py", label=bulletpoint+"**NewsBot**: Get summaries of recent news.")
st.page_link("streamlit/drawing.py", label=bulletpoint+"**LogoRecognizer**: Test your drawing skills and let an AI guess your favorite team.")
st.page_link("streamlit/memes.py", label=bulletpoint+"**MemeExplainer**: AI explained memes.")

st.divider()
st.write("Information:")
             
st.page_link("streamlit/data.py", label=bulletpoint+"**DataAquisition**: Learn more about the underlying data and its origins.")
st.page_link("streamlit/models.py", label=bulletpoint+"**ML/AI models**: Explanation of the different machine learning models and generative AIs.")
st.page_link("streamlit/wbs.py", label=bulletpoint+"**WBS bootcamp**: Brief explanation about the origins of this project.")

st.divider()
st.write("More:")
             
st.page_link("streamlit/chat.py", label=bulletpoint+"**Chat**: Chat with other users.")
st.page_link("streamlit/feedback.py", label=bulletpoint+"**Provide Feedback**: Let me know what could be done to improve the app or report bugs.")
st.page_link("streamlit/login.py", label=bulletpoint+"**User Login**: Login to get user or admin rights.")
st.page_link("streamlit/game.py", label=bulletpoint+"**Games**: Some NFL-themed games (Hangman, Sudokus, PixelLogos, NFL-Idler).")
