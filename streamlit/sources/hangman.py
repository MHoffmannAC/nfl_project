import random

from pyfiglet import Figlet
from sources.sql import create_sql_engine, query_db

import streamlit as st

NUM_HINTS = 2
MIN_GUESSES_FOR_HINT = 2
MIN_LETTERS_FOR_HINT = 3

sql_engine = create_sql_engine()

figures = {
    "hangman": [
        """
    +---+
    |   |
        |
        |
        |
        |
    =========""",
        """
    +---+
    |   |
    O   |
        |
        |
        |
    =========""",
        """
    +---+
    |   |
    O   |
    |   |
        |
        |
    =========""",
        """
    +---+
    |   |
    O   |
   /|   |
        |
        |
    =========""",
        r"""
    +---+
    |   |
    O   |
   /|\  |
        |
        |
    =========""",
        r"""
    +---+
    |   |
    O   |
   /|\  |
   /    |
        |
    =========""",
        r"""
    +------+
       |   |
       O   |
      /|\  |
      / \  |
           |
    =========""",
    ],
    "flowers": [
        r"""
          wWWWw               wWWWw
    vVVVv (___) wWWWw         (___)  vVVVv
    (___)  ~Y~  (___)  vVVVv   ~Y~   (___)
     ~Y~   \|    ~Y~   (___)    |/    ~Y~
     \|   \ |/   \| /  \~Y~/   \|    \ |/
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^""",
        r"""
          wWWWw
    vVVVv (___) wWWWw                vVVVv
    (___)  ~Y~  (___)  vVVVv         (___)
     ~Y~   \|    ~Y~   (___)    |     ~Y~
     \|   \ |/   \| /  \~Y~/    |    \ |/
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^""",
        r"""
          wWWWw
          (___) wWWWw                vVVVv
           ~Y~  (___)  vVVVv         (___)
           \|    ~Y~   (___)    |     ~Y~
      |   \ |/   \| /  \~Y~/    |    \ |/
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^""",
        r"""
          wWWWw
          (___) wWWWw                vVVVv
           ~Y~  (___)                (___)
           \|    ~Y~            |     ~Y~
      |   \ |/   \| /           |    \ |/
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^""",
        r"""

                wWWWw                vVVVv
                (___)                (___)
            |    ~Y~            |     ~Y~
      |     |    \| /           |    \ |/
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^""",
        r"""

                wWWWw
                (___)
            |    ~Y~            |
      |     |    \| /           |      |
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^""",
        r"""



            |                   |
      |     |     |             |      |
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^""",
    ],
    "chase": [
        r"""

      ____□_
    -/|_||_\`.__---------------------------- __o ----
    ( POLICE _  \ _    ___    ___    ___   _ \<_   __
    =`-(_)--(_)-'                         (_)/(_)
    -------------------------------------------------
    """,
        r"""

           ____□_
    ------/|_||_\`.__----------------------- __o ----
    ___  ( POLICE _  \ ___    ___    ___   _ \<_   __
         =`-(_)--(_)-'                    (_)/(_)
    -------------------------------------------------
    """,
        r"""

                ____□_
    -----------/|_||_\`.__------------------ __o ----
    ___    ___( POLICE _  \   ___    ___   _ \<_   __
              =`-(_)--(_)-'               (_)/(_)
    -------------------------------------------------
    """,
        r"""

                     ____□_
    ----------------/|_||_\`.__------------- __o ----
    ___    ___    _( POLICE _  \_    ___   _ \<_   __
                   =`-(_)--(_)-'          (_)/(_)
    -------------------------------------------------
    """,
        r"""

                          ____□_
    ---------------------/|_||_\`.__-------- __o ----
    ___    ___    ___   ( POLICE _  \___   _ \<_   __
                        =`-(_)--(_)-'     (_)/(_)
    -------------------------------------------------
    """,
        r"""

                               ____□_
    --------------------------/|_||_\`.__--- __o ----
    ___    ___    ___    ___ ( POLICE _  \ _ \<_   __
                             =`-(_)--(_)-'(_)/(_)
    -------------------------------------------------
    """,
        r"""_____________________________
     ||   ||     ||   ||
     ||   ||, , ,||   ||
     ||  (||/|/(\||/  ||
     ||  ||| _'_`|||  ||
     ||   || o o ||   ||
     ||  (||  - `||)  ||
     ||   ||  =  ||   ||
     ||   ||\___/||   ||
     ||___||) , (||___||
    /||---||-\_/-||---||\
   / ||--_||_____||_--|| \
  (_(||)-| S123-45 |-(||)_)
    """,
    ],
}

figures_lines = {}
for figure, lines in figures.items():
    figures_lines[figure] = []
    for line in lines:
        figures_lines[figure].append(line.split("\n"))

lang_dict = {
    "en": {
        "msg_welcome": 'Welcome to a new round of hangman. Please select your game settings. To start a game, press "Start Game"',
        "lang_full": "english",
        "button_start": "Start Game",
        "button_guess": "Submit Guess",
        "button_hint1": "Use first hint (-1 life)",
        "button_hint2": "Use second hint (-1 life)",
        "msg_avail_diff": "Available difficulties:",
        "msg_set_hints": "Hint settings:",
        "msg_toggle_hints": "Allow hints",
        "difficulties": {
            "Team names (Very Easy)": (
                "SELECT name FROM teams WHERE `name` NOT IN ('Afc', 'Nfc', 'TBD');",
                "name",
            ),
            "Team locations (Easy)": (
                "SELECT location FROM teams WHERE `name` NOT IN ('Afc', 'Nfc', 'TBD');",
                "location",
            ),
            "Player positions (medium)": ("SELECT name FROM positions;", "name"),
            "College mascots (hard)": ("SELECT mascot FROM colleges;", "mascot"),
            "Player names (very hard)": (
                "SELECT CONCAT(firstName, ' ', lastName) AS player_name FROM players;",
                "player_name",
            ),
        },
        "msg_inp_diff": "Enter difficulty to start a new game\nor choose different language or illustration\n",
        "msg_avail_lett": "Available letters:",
        "msg_avail_lang": "Available languages:",
        "msg_avail_figs": "Available illustrations:",
        "msg_guesses_left": [
            "You have one life left",
            "You have {num_guesses} lives left",
        ],
        "msg_choose_lett": "Please choose a letter or guess the solution   ",
        "msg_allowed_input": "Please enter a single letter or the full solution",
        "msg_repeat": "You already guessed this letter",
        "msg_not_solution": "Sorry, {user_guess} is not the solution",
        "msg_correct_lett": "Congratulations, {user_guess} is in the solution",
        "msg_wrong_lett": "Sorry, {user_guess} is not in the solution",
        "msg_success": "You successfully guessed the solution {solution}",
        "msg_reveal": "The correct solution was {solution}",
        "msg_restart_quit": "Choose 'r' to restart the game or 'q' to quit the game    ",
        "msg_hints_letters_left": "You almost got the solution already. You will be able to guess it without a hint!",
        "msg_hints_lives_left": "Revealing a hint costs one life. Unfortunately, you have only one left. Use it to guess a letter or the solution instead. No hint revealed.",
        "msg_hint_revealed": "You used a hint. Revealed letter:",
        "header_win": "YOU WIN",
        "header_lost": "GAME OVER",
        "fig_texts": {
            "hangman": "Classical hangman figure",
            "flowers": "Field of flowers",
            "chase": "  Police chase",
        },
    },
    "de": {
        "msg_welcome": 'Willkommen zu einer neuen Runde Hangman. Bitte wähle deine Einstellungen. Presse "Starte Spiel", um das Spiel zu beginnen.',
        "lang_full": "deutsch",
        "button_start": "Starte Spiel",
        "button_guess": "Schicke Vermutung ab",
        "button_hint1": "Nutze ersten Hinweis (-1 Leben)",
        "button_hint2": "Nutze zweiten Hinweis (-1 Leben)",
        "msg_avail_diff": "Verfügbare Schwierigkeitsgrade:",
        "msg_set_hints": "Hinweis-Einstellungen:",
        "msg_toggle_hints": "Hinweise zulassen",
        "difficulties": {
            "Teamnamen (Sehr einfach)": (
                "SELECT name FROM teams WHERE `name` NOT IN ('Afc', 'Nfc', 'TBD');",
                "name",
            ),
            "Teamorte (einfach)": (
                "SELECT location FROM teams WHERE `name` NOT IN ('Afc', 'Nfc', 'TBD');",
                "location",
            ),
            "Spielpositionen (mittel)": ("SELECT name FROM positions;", "name"),
            "Collegemaskotchen (schwer)": ("SELECT mascot FROM colleges;", "mascot"),
            "Spielernamen (sehr schwer)": (
                "SELECT CONCAT(firstName, ' ', lastName) AS player_name FROM players;",
                "player_name",
            ),
        },
        "msg_inp_diff": "Wähle Schwierigkeitsgrad um ein neues Spiel zu beginnen,\noder ändere die Sprache oder Illustration\n",
        "msg_avail_lett": "Mögliche Buchstaben:",
        "msg_avail_lang": "Mögliche Sprachen:",
        "msg_avail_figs": "Mögliche Illustrationen:",
        "msg_guesses_left": [
            "Du hast noch ein Leben",
            "Du hast noch {num_guesses} Leben über",
        ],
        "msg_choose_lett": "Bitte wähle einen Buchstaben oder rate die Lösung  ",
        "msg_allowed_input": "Bitte gib einen einzelnen Buchstaben oder die komplette Lösung ein",
        "msg_repeat": "Dieser Buchstabe wurde bereits zuvor geraten",
        "msg_not_solution": "{user_guess} ist leider nicht die Lösung",
        "msg_correct_lett": "Glückwunsch, {user_guess} kommt in der Lösung vor",
        "msg_wrong_lett": "{user_guess} kommt leider nicht in der Lösung vor",
        "msg_success": "Du hast erfolgreich die Lösung {solution} erraten",
        "msg_reveal": "Die korrekte Lösung wäre {solution} gewesen",
        "msg_restart_quit": "Wähle 'r' zum Neustarten oder 'q' zum Beenden des Spiels    ",
        "msg_hints_letters_left": "Du hast schon fast die Lösung gefunden. Du schaffst es ohne einen Hinweis!",
        "msg_hints_lives_left": "Ein Hinweis kostet dich ein Leben. Leider hast du nur noch ein Leben übrig. Nutze dieses lieber, um einen Buchstaben oder die Lösung zu raten. Es wurde kein Hinweis zugelassen.",
        "msg_hint_revealed": "Du hast einen Hinweis verwendet. Folgender Buchstabe wurde aufgedeckt:",
        "header_win": "GEWONNEN",
        "header_lost": "VERLOREN",
        "fig_texts": {
            "hangman": "Klassisches Galgenmännchen",
            "flowers": "Blumenfeld",
            "chase": "  Verfolgungsjagd mit Polizei",
        },
    },
    # here, new languages can be added. make sure to define ALL dict entries (i.e., copy from an existing one and replace accordingly)
}


def initial_setup() -> None:
    if "hangman" not in st.session_state:
        st.session_state["hangman"] = {}
    if "language" not in st.session_state["hangman"]:
        st.session_state["hangman"]["language"] = "en"
    if "difficulty" not in st.session_state["hangman"] or st.session_state["hangman"][
        "difficulty"
    ] not in list(
        lang_dict[st.session_state["hangman"]["language"]]["difficulties"].keys(),
    ):
        st.session_state["hangman"]["difficulty"] = next(
            iter(
                lang_dict[st.session_state["hangman"]["language"]][
                    "difficulties"
                ].keys(),
            ),
        )
    if "figure" not in st.session_state["hangman"]:
        st.session_state["hangman"]["figure"] = "hangman"
    if "figlet" not in st.session_state["hangman"]:
        st.session_state["hangman"]["figlet"] = "ansi_regular"
    if "input_feedback" not in st.session_state["hangman"]:
        st.session_state["hangman"]["input_feedback"] = ""
    if "input_text" not in st.session_state:
        st.session_state["input_text"] = ""
    if "allow_hints" not in st.session_state["hangman"]:
        st.session_state["hangman"]["allow_hints"] = False


def cleaned_solution(solution: str) -> str:
    return (
        solution.replace("Ö", "OE")
        .replace("Ü", "UE")
        .replace("Ä", "AE")
        .replace(",", "")
        .replace(".", "")
        .replace("!", "")
        .replace("?", "")
        .replace(":", "")
        .replace(";", "")
        .replace("-", "")
        .replace("_", " ")
        .replace('"', "")
        .replace(")", "")
        .replace("(", "")
        .replace("\n", "")
        .strip()
    )


def refresh() -> None:
    del st.session_state["hangman"]["solution"]
    del st.session_state["hangman"]["remaining_guesses"]
    del st.session_state["hangman"]["guessed_word_so_far"]
    del st.session_state["hangman"]["possible_guesses"]
    del st.session_state["hangman"]["wrong_guesses"]
    del st.session_state["hangman"]["correct_guesses"]
    del st.session_state["hangman"]["letters_to_guess"]
    del st.session_state["hangman"]["input_feedback"]
    del st.session_state["input_text"]
    del st.session_state["hangman"]["reset_flag"]


def settings_display() -> None:
    st.code(
        Figlet(font=st.session_state["hangman"]["figlet"])
        .renderText("HANGMAN")
        .rstrip(),
    )
    st.write("")
    st.write(lang_dict[st.session_state["hangman"]["language"]]["msg_welcome"])

    st.write("")

    st.subheader(
        lang_dict[st.session_state["hangman"]["language"]]["msg_avail_diff"],
        anchor=False,
    )
    difficulties = list(
        lang_dict[st.session_state["hangman"]["language"]]["difficulties"].keys(),
    )
    st.session_state["hangman"]["difficulty"] = st.radio(
        lang_dict[st.session_state["hangman"]["language"]]["msg_avail_diff"],
        difficulties,
        index=difficulties.index(st.session_state["hangman"]["difficulty"]),
        label_visibility="collapsed",
    )

    st.write("")

    st.subheader(
        lang_dict[st.session_state["hangman"]["language"]]["msg_avail_lang"],
        anchor=False,
    )
    languages = [lang_dict[language]["lang_full"] for language in lang_dict]
    language = st.radio(
        lang_dict[st.session_state["hangman"]["language"]]["msg_avail_lang"],
        languages,
        index=languages.index(
            lang_dict[st.session_state["hangman"]["language"]]["lang_full"],
        ),
        label_visibility="collapsed",
    )

    lang_short = next(
        (key for key, value in lang_dict.items() if value.get("lang_full") == language),
        None,
    )
    if lang_short != st.session_state["hangman"]["language"]:
        st.session_state["hangman"]["language"] = lang_short
        st.rerun()

    st.write("")

    st.subheader(
        lang_dict[st.session_state["hangman"]["language"]]["msg_avail_figs"],
        anchor=False,
    )
    all_figures = list(figures.keys())
    chosen_figure = st.radio(
        lang_dict[st.session_state["hangman"]["language"]]["msg_avail_figs"],
        all_figures,
        index=all_figures.index(st.session_state["hangman"]["figure"]),
        label_visibility="collapsed",
    )
    if chosen_figure != st.session_state["hangman"]["figure"]:
        st.session_state["hangman"]["figure"] = chosen_figure
        st.rerun()

    st.write("")

    st.subheader(
        lang_dict[st.session_state["hangman"]["language"]]["msg_set_hints"],
        anchor=False,
    )

    hint_toggle = st.toggle(
        lang_dict[st.session_state["hangman"]["language"]]["msg_toggle_hints"],
        value=st.session_state["hangman"]["allow_hints"],
    )
    if hint_toggle != st.session_state["hangman"].get("allow_hints", None):
        st.session_state["hangman"]["allow_hints"] = hint_toggle
        st.rerun()

    st.write("")

    if st.button(lang_dict[st.session_state["hangman"]["language"]]["button_start"]):
        initialize_game()


def initialize_game() -> None:
    query_string, column_name = lang_dict[st.session_state["hangman"]["language"]][
        "difficulties"
    ][st.session_state["hangman"]["difficulty"]]
    dirty_solution = random.SystemRandom().choice(query_db(sql_engine, query_string))[
        column_name
    ]
    st.session_state["hangman"]["solution"] = cleaned_solution(dirty_solution.upper())
    st.session_state["hangman"]["remaining_guesses"] = 6
    st.session_state["hangman"]["guessed_word_so_far"] = "_ " * len(
        st.session_state["hangman"]["solution"],
    )
    st.session_state["hangman"]["possible_guesses"] = [
        "A B C D E F G H I",
        "J K L M N O P Q R",
        "S T U V W X Y Z",
    ]
    st.session_state["hangman"]["wrong_guesses"] = []
    st.session_state["hangman"]["correct_guesses"] = []
    st.session_state["hangman"]["letters_to_guess"] = st.session_state["hangman"][
        "guessed_word_so_far"
    ].count("_")
    if st.session_state["hangman"]["allow_hints"]:
        st.session_state["hangman"]["remaining_hints"] = 2
    if " " in st.session_state["hangman"]["solution"]:
        for i in range(len(st.session_state["hangman"]["solution"])):
            if st.session_state["hangman"]["solution"][i] == " ":
                st.session_state["hangman"]["guessed_word_so_far"] = (
                    st.session_state["hangman"]["guessed_word_so_far"][: 2 * i]
                    + " "
                    + st.session_state["hangman"]["guessed_word_so_far"][2 * i + 1 :]
                )
    st.rerun()


def game_display() -> None:
    st.title("Hangman")
    space_needed = max(
        len(
            lang_dict[st.session_state["hangman"]["language"]]["msg_guesses_left"][
                1
            ].format(num_guesses=st.session_state["hangman"]["remaining_guesses"]),
        )
        + 10,
        len(st.session_state["hangman"]["guessed_word_so_far"]) + 5,
    )
    st.write("")

    current_figure = figures_lines[st.session_state["hangman"]["figure"]][
        6 - st.session_state["hangman"]["remaining_guesses"]
    ]

    game_display = "\n".join(
        [
            " " * space_needed + current_figure[0],
            st.session_state["hangman"]["guessed_word_so_far"].ljust(space_needed)
            + current_figure[1],
            " " * space_needed + current_figure[2],
            lang_dict[st.session_state["hangman"]["language"]]["msg_avail_lett"].ljust(
                space_needed,
            )
            + current_figure[3],
            st.session_state["hangman"]["possible_guesses"][0].ljust(space_needed)
            + current_figure[4],
            st.session_state["hangman"]["possible_guesses"][1].ljust(space_needed)
            + current_figure[5],
            st.session_state["hangman"]["possible_guesses"][2].ljust(space_needed)
            + current_figure[6],
            " " * space_needed + current_figure[7],
            lang_dict[st.session_state["hangman"]["language"]]["msg_guesses_left"][
                1
            ].format(num_guesses=st.session_state["hangman"]["remaining_guesses"])
            if st.session_state["hangman"]["remaining_guesses"] > 1
            else lang_dict[st.session_state["hangman"]["language"]]["msg_guesses_left"][
                0
            ],
            "",
        ],
    )

    st.code(game_display, language=None)

    if "input_text" not in st.session_state:
        st.session_state["input_text"] = ""
    if "reset_flag" not in st.session_state["hangman"]:
        st.session_state["hangman"]["reset_flag"] = False
    if st.session_state["hangman"]["reset_flag"]:
        st.session_state["input_text"] = ""
        st.session_state["hangman"]["reset_flag"] = False

    st.text_input(
        lang_dict[st.session_state["hangman"]["language"]]["msg_choose_lett"],
        key="input_text",
    )
    cols = st.columns([5, 1, 1])
    if cols[0].button(
        lang_dict[st.session_state["hangman"]["language"]]["button_guess"],
    ):
        evaluate_guess(st.session_state["input_text"])
        st.rerun()
    if (
        st.session_state["hangman"]["allow_hints"]
        and st.session_state["hangman"]["remaining_hints"] > 0
    ):
        if st.session_state["hangman"]["remaining_hints"] == NUM_HINTS:
            button_msg = lang_dict[st.session_state["hangman"]["language"]][
                "button_hint1"
            ]
        else:
            button_msg = lang_dict[st.session_state["hangman"]["language"]][
                "button_hint2"
            ]
        if cols[1].button(button_msg):
            get_hint()
            st.rerun()
    if cols[2].button("Restart"):
        refresh()
        initial_setup()
        st.rerun()
    st.write(st.session_state["hangman"]["input_feedback"])


def get_hint() -> None:
    remaining_letters_to_guess = list(
        set(st.session_state["hangman"]["solution"])
        .difference(set(st.session_state["hangman"]["guessed_word_so_far"]))
        .difference(set(" ")),
    )
    if len(remaining_letters_to_guess) < MIN_LETTERS_FOR_HINT:
        st.session_state["hangman"]["input_feedback"] = lang_dict[
            st.session_state["hangman"]["language"]
        ]["msg_hints_letters_left"]
        st.session_state["hangman"]["remaining_hints"] = 0
    elif st.session_state["hangman"]["remaining_guesses"] < MIN_GUESSES_FOR_HINT:
        st.session_state["hangman"]["input_feedback"] = lang_dict[
            st.session_state["hangman"]["language"]
        ]["msg_hints_lives_left"]
        st.session_state["hangman"]["remaining_hints"] = 0
    else:
        revealed_letter = random.SystemRandom().choice(remaining_letters_to_guess)
        st.session_state["hangman"]["remaining_hints"] -= 1
        st.session_state["hangman"]["remaining_guesses"] -= 1
        evaluate_guess(revealed_letter)
        st.session_state["hangman"]["input_feedback"] = (
            lang_dict[st.session_state["hangman"]["language"]]["msg_hint_revealed"]
            + " "
            + revealed_letter
        )
        st.rerun()


def evaluate_guess(user_guess: str) -> None:
    st.session_state["hangman"]["reset_flag"] = True
    user_guess = user_guess.upper()
    if user_guess == "RESTART":
        refresh()
        initial_setup()
        st.rerun()
    elif not (
        (len(user_guess) == 1 and user_guess.isalpha())
        or (len(user_guess) == len(st.session_state["hangman"]["solution"]))
    ):
        st.session_state["hangman"]["input_feedback"] = lang_dict[
            st.session_state["hangman"]["language"]
        ]["msg_allowed_input"]
    elif (
        user_guess in st.session_state["hangman"]["wrong_guesses"]
        or user_guess in st.session_state["hangman"]["correct_guesses"]
    ):
        st.session_state["hangman"]["input_feedback"] = lang_dict[
            st.session_state["hangman"]["language"]
        ]["msg_repeat"]
    elif len(user_guess) == len(st.session_state["hangman"]["solution"]):
        if user_guess == st.session_state["hangman"]["solution"]:
            st.session_state["hangman"]["guessed_word_so_far"] = st.session_state[
                "hangman"
            ]["solution"]
        else:
            st.session_state["hangman"]["input_feedback"] = lang_dict[
                st.session_state["hangman"]["language"]
            ]["msg_not_solution"].format(user_guess=user_guess)
            st.session_state["hangman"]["remaining_guesses"] -= 1
    else:
        if user_guess in st.session_state["hangman"]["solution"]:
            for i in range(len(st.session_state["hangman"]["solution"])):
                if st.session_state["hangman"]["solution"][i] == user_guess:
                    st.session_state["hangman"]["guessed_word_so_far"] = (
                        st.session_state["hangman"]["guessed_word_so_far"][: 2 * i]
                        + user_guess
                        + st.session_state["hangman"]["guessed_word_so_far"][
                            2 * i + 1 :
                        ]
                    )
            st.session_state["hangman"]["correct_guesses"].append(user_guess)
            st.session_state["hangman"]["input_feedback"] = lang_dict[
                st.session_state["hangman"]["language"]
            ]["msg_correct_lett"].format(user_guess=user_guess)
        else:
            st.session_state["hangman"]["wrong_guesses"].append(user_guess)
            st.session_state["hangman"]["remaining_guesses"] -= 1
            st.session_state["hangman"]["input_feedback"] = lang_dict[
                st.session_state["hangman"]["language"]
            ]["msg_wrong_lett"].format(user_guess=user_guess)
        for i in range(len(st.session_state["hangman"]["possible_guesses"])):
            st.session_state["hangman"]["possible_guesses"][i] = st.session_state[
                "hangman"
            ]["possible_guesses"][i].replace(user_guess, " ")
    st.session_state["hangman"]["letters_to_guess"] = st.session_state["hangman"][
        "guessed_word_so_far"
    ].count("_")


def final_display() -> None:
    st.title("Game Results")
    if st.session_state["hangman"]["remaining_guesses"] > 0:
        st.write("")
        st.code(
            Figlet(font=st.session_state["hangman"]["figlet"])
            .renderText(
                lang_dict[st.session_state["hangman"]["language"]]["header_win"],
            )
            .rstrip()
            + "\n\n"
            + lang_dict[st.session_state["hangman"]["language"]]["msg_success"].format(
                solution=st.session_state["hangman"]["solution"],
            ),
            language=None,
        )
    else:
        st.code(
            Figlet(font=st.session_state["hangman"]["figlet"])
            .renderText(
                lang_dict[st.session_state["hangman"]["language"]]["header_lost"],
            )
            .rstrip()
            + "\n\n"
            + figures[st.session_state["hangman"]["figure"]][6]
            + "\n\n"
            + lang_dict[st.session_state["hangman"]["language"]]["msg_reveal"].format(
                solution=st.session_state["hangman"]["solution"],
            ),
            language=None,
        )

    st.write("")

    refresh()
    if st.button("Restart"):
        initial_setup()
        st.rerun()


def run_game() -> None:
    initial_setup()
    if "solution" not in st.session_state["hangman"]:
        settings_display()
    elif (
        st.session_state["hangman"]["remaining_guesses"] == 0
        or st.session_state["hangman"]["letters_to_guess"] == 0
    ):
        final_display()
    else:
        game_display()
