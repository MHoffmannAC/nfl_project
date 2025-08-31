import streamlit as st
from streamlit.components.v1 import iframe
import sources.hangman as hangman
import sources.pixellogo as pixellogo
import sources.ttt as ttt

st.title("Collection of NFL-themed Games", anchor=False)

game = st.segmented_control("Select a game", ["Tic-Tac-Toe (1 vs. 1)", "Hangman (Singleplayer)", "Sudoku (Singleplayer)", "PixelLogos (Multiplayer)"],  default=None)

if game == "Sudoku (Singleplayer)":
    st.header("2025", anchor=False)
    iframe("https://sudokupad.app/dje7invdvu", height=800)
    st.write("")
    st.header("2024", anchor=False)
    iframe("https://sudokupad.app/xsk7whp4qz", height=800)
elif game == "Hangman (Singleplayer)":
    hangman.run_game()      
elif game == "PixelLogos (Multiplayer)":
    pixellogo.initialize_game()
    pixellogo.display_game()
elif game=="Tic-Tac-Toe (1 vs. 1)":
    ttt.run_game()
else:
    st.header("Please select a game from the choices above")
    st.write("""**Available games**:
 
 - **`Tic-Tac-Toe`**: Be the first to get three in a row (1 vs. 1)
             
 - **`Hangman`**: The typical hangman game. Guess a hidden word and avoid making mistakes. (Singleplayer)
 
 - **`Sudoku`**: Solve some NFL-themed Sudokus. (Singleplayer)
 
 - **`PixelLogo`**: Guess quicker than your opponents which logo is displayed. (Multiplayer)
""")
    