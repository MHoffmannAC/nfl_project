import streamlit as st

st.header("Models")

st.segmented_control("Choose a model you like to get more information about", ["PlayAnalyzer (play type)", "PlayAnalyzer (win probability)", "NFLBot", "NewsBot", "LogoRecognizer"], default=None, selection_mode="single")

st.error("Under construction...")