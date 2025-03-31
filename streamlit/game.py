import streamlit as st
from streamlit.components.v1 import iframe
import hangman
from pyfiglet import Figlet

st.title("Collection of NFL-themed Games")

game = st.segmented_control("Select a game", ["Hangman", "Sudoku"])

if game == "Sudoku":
    st.header("2025")
    iframe("https://sudokupad.app/dje7invdvu", height=800)
    st.write("")
    st.header("2024")
    iframe("https://sudokupad.app/xsk7whp4qz", height=800)

if game == "Hangman":

    hangman.initial_setup()   
    
    if "solution" not in st.session_state:
         hangman.settings_display()
        
    else:
        if st.session_state["remaining_guesses"] == 0:
            hangman.final_display()
        else:
            hangman.game_display()