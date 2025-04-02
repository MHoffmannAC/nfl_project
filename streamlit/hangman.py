import random
import streamlit as st
from pyfiglet import Figlet
import textwrap


def initial_setup():
    if "language" not in st.session_state:
        st.session_state["language"] = "en"
    if "difficulty" not in st.session_state or st.session_state["difficulty"] not in list(lang_dict[st.session_state["language"]]['difficulties'].keys()):
        st.session_state["difficulty"] = list(lang_dict[st.session_state["language"]]['difficulties'].keys())[0]
    if "figure" not in st.session_state:
        st.session_state["figure"] = "hangman"
    if "figlet" not in st.session_state:
        st.session_state["figlet"] = "ansi_regular"
    if "input_feedback" not in st.session_state:    
        st.session_state["input_feedback"] = ""
    if "input_text" not in st.session_state:    
        st.session_state["input_text"] = ""

def cleaned_solution(solution):
    return solution.replace('Ö', 'OE').replace('Ü', 'UE').replace('Ä', 'AE').replace(",", "").replace(".", "").replace("!", "").replace("?", "").replace(":", "").replace(";", "").replace("-", "").replace("_", " ").replace("\"", "").replace(")","").replace("(", "").replace("\n", "").strip()

def refresh():
    del st.session_state["solution"]
    del st.session_state["remaining_guesses"]
    del st.session_state["guessed_word_so_far"]
    del st.session_state["possible_guesses"]
    del st.session_state["wrong_guesses"]
    del st.session_state["correct_guesses"]
    del st.session_state["letters_to_guess"]
    del st.session_state["input_feedback"]
    del st.session_state["input_text"]   
    del st.session_state["reset_flag"]

    #del st.session_state["language"]
    #del st.session_state["difficulty"]
    #del st.session_state["figure"]
    #del st.session_state["figlet"]

def settings_display():

    st.code(Figlet(font=st.session_state['figlet']).renderText("HANGMAN").rstrip())
    st.write("")
    st.write("Welcome to a new round of hangman. Please select your game settings. To start a game, press \"Start Game\"")
    
    st.write("")
        
    st.header(lang_dict[st.session_state['language']]['msg_avail_diff'])
    difficulties = list(lang_dict[st.session_state["language"]]['difficulties'].keys())
    st.session_state["difficulty"] = st.radio(lang_dict[st.session_state['language']]['msg_avail_diff'],
                                              difficulties,
                                              index=difficulties.index(st.session_state["difficulty"]),
                                              label_visibility="collapsed")
    
    st.write("")
    
    st.header(lang_dict[st.session_state['language']]['msg_avail_lang'])
    languages = [lang_dict[language]['lang_full'] for language in lang_dict.keys()]
    language = st.radio(lang_dict[st.session_state['language']]['msg_avail_lang'],
                                              languages,
                                              index = languages.index(lang_dict[st.session_state['language']]['lang_full']),
                                              label_visibility="collapsed")
    
    lang_short = next((key for key, value in lang_dict.items() if value.get("lang_full") == language), None)
    if lang_short != st.session_state["language"]:
        st.session_state["language"] = lang_short
        st.rerun()
    
    st.write("")
    
    st.header(lang_dict[st.session_state['language']]['msg_avail_figs'])
    all_figures = list(figures.keys())
    chosen_figure = st.radio(lang_dict[st.session_state['language']]['msg_avail_figs'],
                                          all_figures,
                                          index = all_figures.index(st.session_state["figure"]),
                                          label_visibility="collapsed")
    if chosen_figure != st.session_state["figure"]:
        st.session_state["figure"] = chosen_figure
        st.rerun()
    
    st.write("")

    if st.button("Start Game"):
        initialize_game()

def initialize_game():
    rand_func, rand_args, rand_kwargs = lang_dict[st.session_state["language"]]['difficulties'][st.session_state["difficulty"]]
    st.session_state["solution"] = cleaned_solution(rand_func(*rand_args, **rand_kwargs).upper())
    st.session_state["remaining_guesses"] = 6
    st.session_state["guessed_word_so_far"] = "_ " * len(st.session_state["solution"])
    st.session_state["possible_guesses"] = ["A B C D E F G H I", "J K L M N O P Q R", "S T U V W X Y Z"]
    st.session_state["wrong_guesses"] = []
    st.session_state["correct_guesses"] = []
    st.session_state["letters_to_guess"] = st.session_state["guessed_word_so_far"].count("_")
    if(" " in st.session_state["solution"]):
        for i in range(len(st.session_state["solution"])):
            if(st.session_state["solution"][i] == " "):
                st.session_state["guessed_word_so_far"]=st.session_state["guessed_word_so_far"][:2*i]+" "+st.session_state["guessed_word_so_far"][2*i+1:]
    st.rerun()

def game_display():
    st.title("Hangman")
    space_needed=max(len(lang_dict[st.session_state['language']]['msg_guesses_left'][1].format(num_guesses=st.session_state["remaining_guesses"]))+10,len(st.session_state["guessed_word_so_far"])+5)
    st.write("")

    current_figure = figures_lines[st.session_state['figure']][6 - st.session_state["remaining_guesses"]]

    game_display = "\n".join([
        " " * space_needed + current_figure[0],
        st.session_state["guessed_word_so_far"].ljust(space_needed) + current_figure[1],
        " " * space_needed + current_figure[2],
        lang_dict[st.session_state['language']]['msg_avail_lett'].ljust(space_needed) + current_figure[3],
        st.session_state["possible_guesses"][0].ljust(space_needed) + current_figure[4],
        st.session_state["possible_guesses"][1].ljust(space_needed) + current_figure[5],
        st.session_state["possible_guesses"][2].ljust(space_needed) + current_figure[6],
        " " * space_needed + current_figure[7],
        lang_dict[st.session_state['language']]['msg_guesses_left'][1].format(num_guesses=st.session_state["remaining_guesses"]) if st.session_state["remaining_guesses"] > 1 
        else lang_dict[st.session_state['language']]['msg_guesses_left'][0],
        ""
    ])
    
    st.code(game_display)

    # workaround to empty input field after guess
    if "input_text" not in st.session_state:
        st.session_state["input_text"] = ""
    if "reset_flag" not in st.session_state:
        st.session_state["reset_flag"] = False  
    if st.session_state["reset_flag"]:
        st.session_state["input_text"] = ""  
        st.session_state["reset_flag"] = False  

    st.text_input(lang_dict[st.session_state['language']]['msg_choose_lett'], key="input_text").upper()
    if st.button("Guess"):
        evaluate_guess()
        
    st.write(st.session_state["input_feedback"])

    

def evaluate_guess():
    st.session_state["reset_flag"] = True
    user_guess = st.session_state["input_text"]
    if(not (  (len(user_guess)==1 and user_guess.isalpha())
                or
                (len(user_guess)==len(st.session_state["solution"]))
                )):
        st.session_state["input_feedback"] = (lang_dict[st.session_state['language']]['msg_allowed_input'])
    elif(user_guess in st.session_state["wrong_guesses"] or user_guess in st.session_state["correct_guesses"]):
        st.session_state["input_feedback"] = (lang_dict[st.session_state['language']]['msg_repeat'])
    elif(len(user_guess)==len(st.session_state["solution"])):
        if(user_guess==st.session_state["solution"]):
            st.session_state["guessed_word_so_far"]=st.session_state["solution"]
        else:
            st.session_state["input_feedback"] = (lang_dict[st.session_state['language']]['msg_not_solution'].format(user_guess=user_guess))
            st.session_state["remaining_guesses"]-=1
    else:
        if(user_guess in st.session_state["solution"]):
            for i in range(len(st.session_state["solution"])):
                if(st.session_state["solution"][i] == user_guess):
                    st.session_state["guessed_word_so_far"]=st.session_state["guessed_word_so_far"][:2*i]+user_guess+st.session_state["guessed_word_so_far"][2*i+1:]
            st.session_state["correct_guesses"].append(user_guess)
            st.session_state["input_feedback"] = (lang_dict[st.session_state['language']]['msg_correct_lett'].format(user_guess=user_guess))
        else:
            st.session_state["wrong_guesses"].append(user_guess)
            st.session_state["remaining_guesses"]-=1
            st.session_state["input_feedback"] = (lang_dict[st.session_state['language']]['msg_wrong_lett'].format(user_guess=user_guess))
        for i in range(len(st.session_state["possible_guesses"])):
            st.session_state["possible_guesses"][i] = st.session_state["possible_guesses"][i].replace(user_guess," ")
    st.session_state["letters_to_guess"] = st.session_state["guessed_word_so_far"].count("_")
    
def final_display():
    st.title("Game Results")
    if(st.session_state["remaining_guesses"]>0):
      st.write("")
      st.code(textwrap.dedent(Figlet(font=st.session_state['figlet']).renderText(lang_dict[st.session_state['language']]['header_win']).rstrip()), language=None)
      st.write("")
      st.write(lang_dict[st.session_state['language']]['msg_success'].format(solution=st.session_state["solution"]))
    else:
      st.code(textwrap.dedent(Figlet(font=st.session_state['figlet']).renderText(lang_dict[st.session_state['language']]['header_lost']).rstrip()), language=None)
      st.code(textwrap.dedent(figures[st.session_state['figure']][6]), language=None)
      st.write("")
      st.write(lang_dict[st.session_state['language']]['msg_reveal'].format(solution=st.session_state["solution"]))
    st.write("")
    
    if st.button("Restart"):
        refresh()
        initialize_game()
        st.rerun()
    #user_input = input(lang_dict[st.session_state['language']]['msg_restart_quit'])
    #if(user_input == "r"):
    #  return True
    #elif(user_input == "q"):
    #  return False

    
figures = {

        'hangman': ['''
    +---+
    |   |
        |
        |
        |
        |
    =========''', '''
    +---+
    |   |
    O   |
        |
        |
        |
    =========''', '''
    +---+
    |   |
    O   |
    |   |
        |
        |
    =========''', '''
    +---+
    |   |
    O   |
    /|   |
        |
        |
    =========''', '''
    +---+
    |   |
    O   |
    /|\  |
        |
        |
    =========''', '''
    +---+
    |   |
    O   |
    /|\  |
    /    |
        |
    =========''', '''
      +------+
       |   |
       O   |
      /|\  |
      / \  |
           |
    ========='''],


        'flowers': [r'''
            wWWWw               wWWWw
    vVVVv (___) wWWWw         (___)  vVVVv
    (___)  ~Y~  (___)  vVVVv   ~Y~   (___)
        ~Y~   \|    ~Y~   (___)    |/    ~Y~
        \|   \ |/   \| /  \~Y~/   \|    \ |/
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^''',
    r'''
            wWWWw
    vVVVv (___) wWWWw                vVVVv
    (___)  ~Y~  (___)  vVVVv         (___)
        ~Y~   \|    ~Y~   (___)    |     ~Y~
        \|   \ |/   \| /  \~Y~/    |    \ |/
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^''',
    r'''
            wWWWw
            (___) wWWWw                vVVVv
            ~Y~  (___)  vVVVv         (___)
            \|    ~Y~   (___)    |     ~Y~
        |   \ |/   \| /  \~Y~/    |    \ |/
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^''',
    r'''
            wWWWw
            (___) wWWWw                vVVVv
            ~Y~  (___)                (___)
            \|    ~Y~            |     ~Y~
        |   \ |/   \| /           |    \ |/
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^''',
    r'''

                wWWWw                vVVVv
                (___)                (___)
            |    ~Y~            |     ~Y~
        |     |    \| /           |    \ |/
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^''',
    r'''

                wWWWw
                (___)
            |    ~Y~            |
        |     |    \| /           |      |
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^''',
    r'''



            |                   |
        |     |     |             |      |
    \\|// \\|// \\|/// \\|//  \\|// \\\|///
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^''',
    ],
        'chase': [r'''

    ____□_
    -/|_||_\`.__---------------------------- __o ----
    ( POLICE _  \ _    ___    ___    ___   _ \<_   __
    =`-(_)--(_)-'                         (_)/(_)
    -------------------------------------------------
    ''',
    r'''

        ____□_
    ------/|_||_\`.__----------------------- __o ----
    ___  ( POLICE _  \ ___    ___    ___   _ \<_   __
        =`-(_)--(_)-'                    (_)/(_)
    -------------------------------------------------
    ''',
    r'''

                ____□_
    -----------/|_||_\`.__------------------ __o ----
    ___    ___( POLICE _  \   ___    ___   _ \<_   __
            =`-(_)--(_)-'               (_)/(_)
    -------------------------------------------------
    ''',
    r'''

                    ____□_
    ----------------/|_||_\`.__------------- __o ----
    ___    ___    _( POLICE _  \_    ___   _ \<_   __
                =`-(_)--(_)-'          (_)/(_)
    -------------------------------------------------
    ''',
    r'''

                        ____□_
    ---------------------/|_||_\`.__-------- __o ----
    ___    ___    ___   ( POLICE _  \___   _ \<_   __
                        =`-(_)--(_)-'     (_)/(_)
    -------------------------------------------------
    ''',
    r'''

                            ____□_
    --------------------------/|_||_\`.__--- __o ----
    ___    ___    ___    ___ ( POLICE _  \ _ \<_   __
                            =`-(_)--(_)-'(_)/(_)
    -------------------------------------------------
    ''',
    r'''      _________________________
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
    ''']    
    }
    
figures_lines = {}
for figure in figures:
    figures_lines[figure] = []
    for i in range(len(figures[figure])):
        figures_lines[figure].append(figures[figure][i].split("\n"))
            
lang_dict = {

    'en': {
                    'lang_full': "english",
                    'msg_avail_diff': "Available difficulties:",
                    'difficulties': {
                        'Words - easy   (handpicked)': (random.choice,[["Quarterback", "Touchdown", "Interception", "Gameday"]],{}),
                        'Words - easy 2  (handpicked)': (random.choice,[["Quarterback", "Touchdown", "Interception", "Gameday"]],{}),
                        # '2': {
                        #     'function': (wonderwords.RandomWord().word, [], {'include_parts_of_speech': ["nouns"]}),
                        #     'label': "   Words - medium (random nouns)"
                        # },
                        # '3': {
                        #     'function': (wonderwords.RandomWord().word, [], {}),
                        #     'label': "   Words - hard   (random words)"
                        # },
                        # '4': {
                        #     'function': (wonderwords.RandomSentence().sentence, [], {}),
                        #     'label': "   Sentence - hard (often gibberish)"
                        # },
                        # '5': {
                        #     'function': (getpass, ["Choose your solution word or sentence:  "], {}),
                        #     'label': "   Use user input as solution"
                        # },
                        # '1984': {
                        #     'function': (random_from_web, ["https://raw.githubusercontent.com/MHoffmannAC/Data-Science-Primer/main/doublethink"], {}),
                        #     'label': "Doublethink sentences"
                        # }
                    },
        'msg_inp_diff': "Enter difficulty to start a new game\nor choose different language or illustration\n",
        'msg_avail_lett': "Available letters:",
        'msg_avail_lang': "Available languages:",
        'msg_avail_figs': "Available illustrations:",
        'msg_guesses_left': ["You have one life left",
                             "You have {num_guesses} lives left"],
        'msg_choose_lett': "Please choose a letter or guess the solution   ",
        'msg_allowed_input': "Please enter a single letter or the full solution",
        'msg_repeat': "You already guessed this letter",
        'msg_not_solution': "Sorry, {user_guess} is not the solution",
        'msg_correct_lett': "Congratulations, {user_guess} is in the solution",
        'msg_wrong_lett': "Sorry, {user_guess} is not in the solution",
        'msg_success': "You successfully guessed the solution {solution}",
        'msg_reveal': "The correct solution was {solution}",
        'msg_restart_quit': "Choose 'r' to restart the game or 'q' to quit the game    ",
        'header_win': "YOU WIN",
        'header_lost': "GAME OVER",
        'fig_texts': {
            'hangman': "Classical hangman figure",
            'flowers': "Field of flowers",
            'chase': "  Police chase"
        }
    },

    'de': {
        'lang_full': "deutsch",
        'msg_avail_diff': "Verfügbare Schwierigkeitsgrade:",
        'difficulties': {
            '1': {
                'function': (random.choice, [["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]],{}),
                'label': "   Wörter - einfach (handerlesen)"
            },
            # '2': {
            #     'function': (random_from_web, ["https://raw.githubusercontent.com/JackShannon/1000-most-common-words/master/1000-most-common-german-words.txt"], {'minlen': 7}),
            #     'label': "   Wörter - mittel  (1000 häufigste Wörter)"
            # },
            # '3': {
            #     'function': (random_from_web, ["https://gist.githubusercontent.com/MarvinJWendt/2f4f4154b8ae218600eb091a5706b5f4/raw/36b70dd6be330aa61cd4d4cdfda6234dcb0b8784/wordlist-german.txt"], {'minlen': 7}),
            #     'label': "   Wörter - schwer  (Alle möglichen Wörter)"
            # },
            # '4': {
            #     'function': (getpass, ["Wähle Lösungswort oder -Satz:  "], {}),
            #     'label': "   Lösung aus Benutzereingabe"
            # },
            # '1984': {
            #     'function': (random_from_web, ["https://raw.githubusercontent.com/MHoffmannAC/Data-Science-Primer/main/doppeldenk"], {}),
            #     'label': "Doppeldenk-Sätze"
            # }
        },
        'msg_inp_diff': "Wähle Schwierigkeitsgrad um ein neues Spiel zu beginnen,\noder ändere die Sprache oder Illustration\n",
        'msg_avail_lett': "Mögliche Buchstaben:",
        'msg_avail_lang': "Mögliche Sprachen:",
        'msg_avail_figs': "Mögliche Illustrationen:",
        'msg_guesses_left': ["Du hast noch ein Leben",
                             "Du hast noch {num_guesses} Leben über"],
        'msg_choose_lett': "Bitte wähle einen Buchstaben oder rate die Lösung  ",
        'msg_allowed_input': "Bitte gib einen einzelnen Buchstaben oder die komplette Lösung ein",
        'msg_repeat': "Dieser Buchstabe wurde bereits zuvor geraten",
        'msg_not_solution': "{user_guess} ist leider nicht die Lösung",
        'msg_correct_lett': "Glückwunsch, {user_guess} kommt in der Lösung vor",
        'msg_wrong_lett': "{user_guess} kommt leider nicht in der Lösung vor",
        'msg_success': "Du hast erfolgreich die Lösung {solution} erraten",
        'msg_reveal': "Die korrekte Lösung wäre {solution} gewesen",
        'msg_restart_quit': "Wähle 'r' zum Neustarten oder 'q' zum Beenden des Spiels    ",
        'header_win': "GEWONNEN",
        'header_lost': "VERLOREN",
        'fig_texts': {
            'hangman': "Klassisches Galgenmännchen",
            'flowers': "Blumenfeld",
            'chase': "  Verfolgungsjagd mit Polizei"
        }
    }

# here, new languages can be added. make sure to define ALL dict entries (i.e., copy from an existing one and replace accordingly)

}