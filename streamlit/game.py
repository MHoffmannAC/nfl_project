import streamlit as st
from streamlit.components.v1 import iframe
import sources.hangman as hangman
import sources.pixellogo as pixellogo

st.title("Collection of NFL-themed Games")

game = st.segmented_control("Select a game", ["Hangman (Singleplayer)", "Sudoku (Singleplayer)", "PixelLogos (Multiplayer)"], default=None)

if game == "Sudoku (Singleplayer)":
    st.header("2025")
    iframe("https://sudokupad.app/dje7invdvu", height=800)
    st.write("")
    st.header("2024")
    iframe("https://sudokupad.app/xsk7whp4qz", height=800)
elif game == "Hangman (Singleplayer)":
    hangman.initial_setup()       
    if "solution" not in st.session_state:
         hangman.settings_display()        
    else:
        if st.session_state["remaining_guesses"] == 0 or st.session_state["letters_to_guess"] == 0:
            hangman.final_display()
        else:
            hangman.game_display()         
elif game == "PixelLogos (Multiplayer)":
    pixellogo.initialize_game()
    pixellogo.display_game()
else:
    st.header("Please select a game from the choices above")
    st.write("""**Available games**:
             
 - **`Hangman`**: The typical hangman game. Guess a hidden word and avoid making mistakes. (Singleplayer)
 
 - **`Sudoku`**: Solve some NFL-themed Sudokus. (Singleplayer)
 
 - **`PixelLogo`**: Guess quicker than your opponents which logo is displayed. (Multiplayer)
""")
    