import streamlit as st
import numpy as np
import random

if st.session_state.get("admin_logged_in", False):


    # Constants
    FIELD_WIDTH = 10
    FIELD_HEIGHT = 6
    NUM_DEFENDERS = 3
    GOAL_LINE = FIELD_WIDTH - 1
    STARTING_POS = (0, FIELD_HEIGHT // 2)  # Start from the left side, middle row

    # AI movement options
    MOVES = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Right, Left, Down, Up

    # Game state variables
    player_pos = list(STARTING_POS)
    defender_positions = [(random.randint(1, FIELD_WIDTH - 2), random.randint(0, FIELD_HEIGHT - 1)) for _ in range(NUM_DEFENDERS)]
    score = 0
    game_over = False

    # Function to move player
    def move_player(direction):
        global player_pos
        if direction == 'UP':
            if player_pos[1] > 0:
                player_pos[1] -= 1
        elif direction == 'DOWN':
            if player_pos[1] < FIELD_HEIGHT - 1:
                player_pos[1] += 1
        elif direction == 'LEFT':
            if player_pos[0] > 0:
                player_pos[0] -= 1
        elif direction == 'RIGHT':
            if player_pos[0] < FIELD_WIDTH - 1:
                player_pos[0] += 1

    # Function to move defenders (AI logic)
    def move_defenders():
        global defender_positions
        for i in range(len(defender_positions)):
            dx, dy = random.choice(MOVES)  # Randomly pick a direction
            new_x = max(0, min(FIELD_WIDTH - 1, defender_positions[i][0] + dx))
            new_y = max(0, min(FIELD_HEIGHT - 1, defender_positions[i][1] + dy))
            defender_positions[i] = (new_x, new_y)

    # Check for collisions with defenders
    def check_collision():
        global game_over
        if tuple(player_pos) in defender_positions:
            game_over = True

    # Check if the player reached the end zone
    def check_end_zone():
        global score, game_over
        if player_pos[0] == GOAL_LINE:
            score += 1
            game_over = True

    # Render the game field
    def render_game():
        field = np.full((FIELD_HEIGHT, FIELD_WIDTH), '&nbsp;')  # Create empty field
        
        # Place the player and defenders
        field[player_pos[1], player_pos[0]] = 'P'
        for defender in defender_positions:
            field[defender[1], defender[0]] = 'D'
            print(defender[1], defender[0])
        
        # Render the field as text (for simplicity)
        field_html = "<div style='font-family: monospace; line-height: 1.5;'>"
        field_html += "--"*(FIELD_WIDTH) + "-<br>"
        for row in field:
            field_html += "|" + " ".join([f"{cell}" for i,cell in enumerate(row)]) + "|<br>"
        field_html += "--"*(FIELD_WIDTH) + "-<br>"
        field_html += "</div>"

        st.markdown(field_html, unsafe_allow_html=True)
        
        st.text(f"Score: {score}")
        if game_over:
            st.text("Game Over! Press 'r' to restart.")

    # Main game loop
    def game():
        global game_over, player_pos, defender_positions, score

        # Instructions
        st.title("Touchdown Challenge!")
        st.text("Move the player with arrow keys to reach the end zone while avoiding defenders.")
        
        # Input for player movement
        if not game_over:
            direction = st.radio("Move", ['UP', 'DOWN', 'LEFT', 'RIGHT'], key="direction", horizontal=True)
            move_player(direction)
            move_defenders()
            check_collision()
            check_end_zone()
        
        render_game()

        # Restart the game if game over
        if game_over:
            restart = st.button("Restart")
            if restart:
                game_over = False
                player_pos = list(STARTING_POS)
                defender_positions = [(random.randint(1, FIELD_WIDTH - 2), random.randint(0, FIELD_HEIGHT - 1)) for _ in range(NUM_DEFENDERS)]
                score = 0

    game()

else:
    st.warning("Under Construction!")
