import streamlit as st
import streamlit_nested_layout as stnl

st.title("Model descriptions", anchor=False)

st.write("On this page you can find a brief summary of the chosen approaches for each tool on this app.")

with st.expander("PlayPredictor (play type)"):
        
    st.markdown("""
### Model Description

The PlayPredictor uses a machine learning model to predict the type of play (Pass, Rush, Punt, or Field Goal) based on a variety of in-game data.

#### Data & Features

The model is trained on a dataset of NFL plays from the years 2009 through 2024. Data is sourced from an NFL database and undergoes extensive preprocessing. The features used for prediction include both play-specific and game-state information, such as:

* **Game-specific information:** Season, week, quarter, and time left on the clock.
* **Play-specific information:** Down, distance, yards to the endzone, and whether the offense is at home.
* **Team-specific information:** The offensive and defensive teams' win-loss standings (overall, home, and road).
* **Derived features:** Score differential and two aggregate metrics calculated from previous plays in the same game:
    * **Completion Rate:** The ratio of successful passes (completions) to total pass attempts.
    * **Pass to Rush Ratio:** The ratio of pass plays to rush plays.
""")
    if st.toggle("Show SQL queries"):
        st.code("""WITH play_stats AS (
        SELECT
            p.play_id,
            p.game_id,
            p.sequenceNumber,
            p.quarter,
            TIME_TO_SEC(p.clock) AS clock_seconds,
            p.offenseAtHome,
            p.down,
            p.distance,
            p.yardsToEndzone,
            p.playtype_id,
            g.season,
            g.game_type,
            g.week,
            CASE 
                WHEN p.offenseAtHome = TRUE THEN p.homeScore
                ELSE p.awayScore
            END AS offenseScore,
            CASE 
                WHEN p.offenseAtHome = FALSE THEN p.homeScore
                ELSE p.awayScore
            END AS defenseScore,
            CASE 
                WHEN p.offenseAtHome = TRUE THEN g.standing_home_overall_win
                ELSE g.standing_away_overall_win
            END AS standing_offense_overall_win,
            CASE 
                WHEN p.offenseAtHome = TRUE THEN g.standing_home_home_win
                ELSE g.standing_away_home_win
            END AS standing_offense_home_win,
            CASE 
                WHEN p.offenseAtHome = TRUE THEN g.standing_home_road_win
                ELSE g.standing_away_road_win
            END AS standing_offense_road_win,
            CASE 
                WHEN p.offenseAtHome = TRUE THEN g.standing_home_overall_loss
                ELSE g.standing_away_overall_loss
            END AS standing_offense_overall_loss,
            CASE 
                WHEN p.offenseAtHome = TRUE THEN g.standing_home_home_loss
                ELSE g.standing_away_home_loss
            END AS standing_offense_home_loss,
            CASE 
                WHEN p.offenseAtHome = TRUE THEN g.standing_home_road_loss
                ELSE g.standing_away_road_loss
            END AS standing_offense_road_loss,
            CASE 
                WHEN p.offenseAtHome = FALSE THEN g.standing_home_overall_win
                ELSE g.standing_away_overall_win
            END AS standing_defense_overall_win,
            CASE 
                WHEN p.offenseAtHome = FALSE THEN g.standing_home_home_win
                ELSE g.standing_away_home_win
            END AS standing_defense_home_win,
            CASE 
                WHEN p.offenseAtHome = FALSE THEN g.standing_home_road_win
                ELSE g.standing_away_road_win
            END AS standing_defense_road_win,
            CASE 
                WHEN p.offenseAtHome = FALSE THEN g.standing_home_overall_loss
                ELSE g.standing_away_overall_loss
            END AS standing_defense_overall_loss,
            CASE 
                WHEN p.offenseAtHome = FALSE THEN g.standing_home_home_loss
                ELSE g.standing_away_home_loss
            END AS standing_defense_home_loss,
            CASE 
                WHEN p.offenseAtHome = FALSE THEN g.standing_home_road_loss
                ELSE g.standing_away_road_loss
            END AS standing_defense_road_loss,
            t1.abbreviation AS offenseAbr,
            t2.abbreviation AS defenseAbr,
            CASE 
                WHEN p.offenseAtHome = TRUE THEN (p.homeScore - p.awayScore)
                ELSE (p.awayScore - p.homeScore)
            END AS scoreDiff,
            (TIME_TO_SEC(p.clock) + (4 - p.quarter) * 15 * 60) AS totalTimeLeft
        FROM
            nfl.plays p
        LEFT JOIN nfl.games g ON p.game_id = g.game_id
        LEFT JOIN nfl.teams t1 ON 
            (p.offenseAtHome = TRUE AND g.home_team_id = t1.team_id) OR
            (p.offenseAtHome = FALSE AND g.away_team_id = t1.team_id)
        LEFT JOIN nfl.teams t2 ON 
            (p.offenseAtHome = TRUE AND g.away_team_id = t2.team_id) OR
            (p.offenseAtHome = FALSE AND g.home_team_id = t2.team_id)
        WHERE
            g.season IN {years}
        ),
        play_aggregates AS (
            SELECT
                p1.game_id,
                p1.play_id,
                p1.sequenceNumber,
                -- Completion Rate Calculation
                (
                    SELECT 
                        COUNT(*) * 1.0 / NULLIF(
                            (SELECT COUNT(*) 
                            FROM nfl.plays p2 
                            WHERE p2.game_id = p1.game_id 
                            AND p2.sequenceNumber < p1.sequenceNumber 
                            AND p2.playtype_id IN (67, 51, 24, 3, 6, 26, 36)), 0
                        )
                    FROM nfl.plays p2
                    WHERE p2.game_id = p1.game_id 
                    AND p2.sequenceNumber < p1.sequenceNumber 
                    AND (p2.playtype_id IN (67, 24)
                        OR (p2.playtype_id = 51 AND p2.description NOT LIKE '%incomplete%')
                    )
                ) AS completionRate,
                -- Pass to Rush Ratio Calculation
                (
                    SELECT 
                        COUNT(*) * 1.0 / NULLIF(
                            (SELECT COUNT(*) 
                            FROM nfl.plays p2 
                            WHERE p2.game_id = p1.game_id 
                            AND p2.sequenceNumber < p1.sequenceNumber 
                            AND p2.playtype_id IN (5, 68)), 0
                        )
                    FROM nfl.plays p2
                    WHERE p2.game_id = p1.game_id 
                    AND p2.sequenceNumber < p1.sequenceNumber 
                    AND p2.playtype_id IN (67, 51, 24, 3, 6, 26, 36)
                ) AS passToRushRatio
            FROM nfl.plays p1
            LEFT JOIN nfl.games g ON p1.game_id = g.game_id
            WHERE g.season IN {years}
        )
        SELECT ps.*, pa.completionRate, pa.passToRushRatio
        FROM play_stats ps
        JOIN play_aggregates pa ON ps.play_id = pa.play_id;""")
    st.markdown("""
#### Model Training

Several classification models from the Scikit-learn library were considered, including **Random Forest Classifier**, **Logistic Regression**, and **K-Nearest Neighbors Classifier**. A separate neural network model was also developed using TensorFlow.

The primary model used for the "PlayPredictor (play type)" tool is a **Decision Tree Classifier**. This model was chosen for its ability to provide a clear, interpretable decision path, which is visualized directly in the app to explain the model's prediction.

The model's hyperparameters were tuned to optimize its performance. Key parameters for the Decision Tree include a maximum depth of 10, a minimum of 4 samples per leaf, and a Gini impurity criterion.
    """)

with st.expander("PlayPredictor (win probabilities)"):
    st.markdown("""
### Model Description

The Win Probability model is a deep neural network built with TensorFlow and Keras. It's a regression model trained to predict the win probability for the offensive team at any given moment during a game. The model outputs a value between 0 and 1, where 1 represents a 100% win probability.

#### Data & Features

The model is trained on a comprehensive dataset of NFL plays from an NFL database. The features used to predict win probability include:

* **Game State Information:** Time remaining in the game (`totalTimeLeft`), quarter, down, distance, and yards to the end zone (`yardline_100`).
* **Score Differential:** The difference in score between the offensive and defensive teams.
* **Team-specific Information:** The offensive team's overall win percentage and whether they are the home team.

The model architecture consists of several densely connected layers, with `relu` activation functions, and `Dropout` layers to prevent overfitting. It is trained using the `Adam` optimizer and a `mean_squared_error` loss function.
""")
    if st.toggle("Show neural network architecture"):
        st.code("""
def create_model(input_shape):
    model = Sequential([
        Input(shape=(input_shape,)),
        Dense(128, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
        Dropout(0.2),
        Dense(64, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dense(1, activation='sigmoid') # Sigmoid activation for a probability output
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model
""", language="python")

with st.expander("ChatBot"):
    st.write("The ChatBot is an agent-based system that combines several tools with a memory to answer user questions about the NFL.")
    st.markdown("""
### Model Description

The ChatBot is built using the Langchain framework and is powered by a large language model from Groq. Its core is a `ConversationalRetrievalChain` that can hold a conversation while also retrieving information from various sources.

#### Core Components
- **LLM:** The underlying large language model is `llama-3.3-70b-versatile` from `ChatGroq`.
- **Memory:** A `ConversationBufferMemory` allows the chatbot to remember previous messages and respond with greater context awareness.
- **Knowledge Base:** The bot uses `HuggingFaceEmbeddings` and a `FAISS` vector store to efficiently manage and retrieve information from a variety of documents, including a glossary and the NFL rulebook.

#### Sources
The agent has access to several specialized sources to assist with queries:
- **"RuleBook":** The official NFL rule set for the current season.
- **"Glossary":** A collection of NFL-related terms and their explanations.
- **"News":** All news published on ESPN.com during the last 7 days.
""")
    if st.toggle("Show LLM and Chain Initialization"):
        st.code("""
llm = ChatGroq(temperature=0,
               groq_api_key=st.secrets['GROQ_TOKEN'],
               model_name="llama-3.3-70b-versatile")

chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectordb.as_retriever(),
    memory=memory,
    combine_docs_chain_kwargs={"prompt": qa_prompt}
)
""", language="python")

with st.expander("NewsSummarizer"):
    st.markdown("""
### Model Description

The NewsSummarizer summarizes recent news in a user defined style. It leverage large language models (LLMs) to process and present information.

#### Data & Features

The summarization feature fetches the latest news from ESPN.com. For each article, an LLM is used to generate a concise summary. This summary can be tailored to a specific audience, such as a "NFL Expert", "Normal Person", or "Child", by providing different prompt instructions to the model.
* **LLM:** The underlying LLM is a `llama-3.1-405b`. It is used in a simple LLM-chain with a prompt template.

""")

        

with st.expander("AIPodcast"):
    st.markdown("""
### Model Description

Conversations between two AIs in the format of a podcast. It leverages large language models (LLMs) to process and present information.

#### Core Components

The podcast feature uses a separate LLM to generate a conversational script based on a news article summary. The script is structured as a dialogue between two hosts: Dave and Julia. This conversation is then converted to audio using a Text-to-Speech (TTS) model.
* **LLM:** The LLM used for the podcast conversation is `llama-3.1-405b`.
* **TTS Model:** The TTS model used to generate the audio is `SpeechT5` from the `transformers` library, which provides a high-quality, natural-sounding voice.
* **News:** The podcast functionality relies on the stored news articles from ESPN, which are pre-processed and ready for the podcast script generation.
""")
    if st.toggle("Show LLM and TTS Initialization"):
        st.code("""
from llama_index.llms.groq import Groq
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import torch

# LLM and Chat Engine
llm = Groq(
    model="llama-3.1-405b", 
    groq_api_key=st.secrets['GROQ_TOKEN']
)

memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

chat_engine = SimpleChatEngine.from_defaults(
    llm=llm,
    memory=memory,
    system_prompt=(
        "You are a sports podcast host named Dave..."
    )
)

# TTS Model
processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
""", language="python")


with st.expander("LogoRecognizer"):
    st.markdown("""
### Model Description

The LogoRecognizer uses a Convolutional Neural Network (CNN) to classify hand-drawn NFL logos. The model is built using TensorFlow and Keras, which are powerful deep learning frameworks.

#### Image Sources

The model was trained on a dataset created from a variety of sources to ensure a robust and comprehensive training set. The images used include:

* **Hand-drawn logos** from the "Branded in Memory" project: https://www.signs.com/branded-in-memory-nfl/
* **Additional hand-drawn versions** for all NFL teams.
* **Real, professional logos** from each team to provide a baseline for the model.

#### Training and Architecture

The model was trained using the `ImageDataGenerator` from Keras, which performs data augmentation to increase the size and diversity of the training dataset. This helps the model become more robust and generalize better to new, unseen drawings.

The CNN architecture includes several key layers:

* **Convolutional Layers (`Conv2D`):** These layers extract features from the input images by applying a series of filters.
* **Pooling Layers (`MaxPooling2D`):** These layers reduce the spatial dimensions of the feature maps, which helps to make the model's predictions more stable and reduce computational load.
* **Dropout Layers (`Dropout`):** This technique randomly "turns off" a fraction of neurons during training, which helps prevent the model from overfitting to the training data.
* **Fully Connected Layers (`Dense`):** These layers perform the final classification based on the features extracted by the convolutional and pooling layers.

#### Prediction Process

When a user draws a logo, the image data is passed to the trained model. The model outputs a probability distribution across all possible NFL team logos. A prediction is made only if the highest probability (or "confidence") is above a specific threshold (0.3). This ensures that the model only provides a prediction when it is reasonably confident, and it prompts the user to continue drawing if the confidence is low.

""")
    st.warning("Note: The model was trained on a limited dataset and may not perform well on all drawings. The accuracy can vary significantly based on the quality and style of the drawing. Feel free to upload your drawings to help improve the model!")
    
with st.expander("MemeExplainer"):
    st.markdown("""
### Model Description

The MemeExplainer uses a multimodal large language model (LLM) to analyze and explain NFL-related memes. It fetches recent memes from a popular Instagram account and then leverages the LLM's vision capabilities to understand the humor and context of the image.

#### Key Components
* **Web Scraping:** The application uses `BeautifulSoup` and `Selenium` to scrape images and captions from the `nflmemes_ig` Instagram page. This allows the app to stay up-to-date with the latest memes.
* **Multimodal LLM:** The core of the explainer is a large language model from `Groq`, specifically `meta-llama/llama-4-scout-17b-16e-instruct`. This model is capable of processing both text (the image caption) and image data to generate a coherent explanation of the meme.
* **Database:** Explained memes are stored in a SQL database to avoid re-processing the same content on every page load. The app checks the database to see if a meme has already been explained before making a new API call to the LLM.

#### Process
1.  The app scrapes the latest memes and their captions from the specified Instagram page.
2.  For each new meme, it sends a request to the multimodal LLM with the image URL and the Instagram caption.
3.  The LLM analyzes the image and text, then generates a text-based explanation of the meme's joke.
4.  The generated explanation is stored in the database along with the meme's image source and caption.
5.  The app displays a selection of the latest memes and their AI-generated explanations.
""")
    if st.toggle("Show LLM Initialization"):
        st.code("""
def get_image_caption(image_url, caption):
    client = Groq(api_key=st.secrets['GROQ_TOKEN'])
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"The image shows an NFL related meme. The related caption on instagram was {caption} Please explain the meme."},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )
    return completion.choices[0].message.content
        """, language="python")
