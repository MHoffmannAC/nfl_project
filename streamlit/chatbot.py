from datetime import datetime, timezone

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from sources.sql import create_sql_engine, query_db
from streamlit_server_state import no_rerun, server_state, server_state_lock

import streamlit as st

sql_engine = create_sql_engine()

llm = ChatGroq(
    temperature=0,
    groq_api_key=st.secrets["GROQ_TOKEN"],
    model_name="llama-3.3-70b-versatile",
)

# prompt
# template = """You are a nice chatbot having a conversation with a human about the NFL.  Give only replies based on the provided extracted parts of long documents (the context). No need to mention explicitly something like "Based on the provided context". If you don't know the answer based on the provided context, just say "I don't know the answer.".
template = """You are a nice chatbot having a conversation with a human about the NFL.
              Give only replies based on the provided extracted parts of long documents (the context).
              Do not say "Based on the provided context" or "According to the context" or similar. Just provide the answer.".

Previous conversation:
{chat_history}

Context to answer question:
{context}

New human question: {question}
Response:"""

prompt = PromptTemplate(template=template, input_variables=["context", "question"])

# embeddings
embedding_model = "sentence-transformers/all-MiniLM-l6-v2"
faiss_rulebook = "./ressources/chatbot/faiss_rulebook"
faiss_glossary = "./ressources/chatbot/faiss_glossary"
faiss_news = "./ressources/chatbot/faiss_news"


@st.cache_resource(show_spinner=False)
def load_vector_db(folder_path: str) -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)  # ,
    # cache_folder="./ressources/chatbot/embeddings")
    return FAISS.load_local(
        folder_path,
        embeddings,
        allow_dangerous_deserialization=True,
    )


# memory
def init_memory(_llm: ChatGroq) -> ConversationBufferMemory:
    return ConversationBufferMemory(
        llm=llm,
        output_key="answer",
        memory_key="chat_history",
        return_messages=True,
    )


def build_news_vector_db() -> FAISS:
    def chunk_news(
        news_rows: list[dict],
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> list[Document]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " "],
        )

        return [
            Document(page_content=chunk, metadata={"headline": row["headline"]})
            for row in news_rows
            for chunk in text_splitter.split_text(row["story"])
        ]

    news_rows = query_db(
        sql_engine,
        "SELECT headline, story FROM news WHERE published >= NOW() - INTERVAL 7 DAY",
    )
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
    docs = chunk_news(news_rows)
    return FAISS.from_documents(docs, embeddings)


# Apply custom CSS
st.markdown(
    """
    <style>
    .chat-container {
        max-height: 60vh;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 10px;
        background-color: #f9f9f9;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
    }
    .st-chat-message {
        background-color: #ffffff !important;  /* Resetting message background */
        padding: 8px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .stTextArea textarea {
        width: 100%;
        height: 50px;
    }
    .fixed-input {
        bottom: 10px;
        left: 0;
        width: 100%;
        background-color: #00093a;
        padding: 10px;
        border-top: 1px solid #ccc;
        flex-shrink: 0;
    }
    div.stButton > button:first-child {
        background-color: #00093a; /* Button color */
        color: white; /* Text color */
        font-size: 16px;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
        margin: 5px;
    }
    div.stButton > button:first-child:hover {
        background-color: #0056b3; /* Darker blue on hover */
        color: white;
    }
    textarea[data-testid="stChatInputTextArea"]::placeholder {
        color: red !important; /* Change placeholder text color to red */
        font-style: italic;    /* Optional: Italicize the placeholder */
        font-size: 16px;       /* Optional: Adjust font size */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("NFLBot: Know Everything About the NFL", anchor=False)

if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome!"},
        {
            "role": "assistant",
            "content": "Please choose a topic to discuss:",
            "avatar": "⚙️",
        },
    ]

if "llms" not in st.session_state:
    st.session_state.llms = {}

if "news_infos" not in server_state:
    with no_rerun, server_state_lock["news_infos"]:
        server_state["news_infos"] = {}
if "faiss" not in server_state["news_infos"]:
    with no_rerun, server_state_lock["news_infos"]:
        server_state["news_infos"]["faiss"] = None
        server_state["news_infos"]["faiss_updated"] = datetime(
            1970,
            1,
            1,
            tzinfo=timezone.utc,
        )  # dummy old date

if "last_updated" not in server_state["news_infos"]:
    with no_rerun, server_state_lock["news_infos"]:
        latest_news = query_db(
            sql_engine,
            "SELECT published FROM news ORDER BY published DESC LIMIT 1;",
        )
        server_state["news_infos"] = {
            "last_updated": latest_news[0]["published"].replace(tzinfo=timezone.utc),
        }

# Display chat messages in a scrollable container
st.divider()
with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message.get("avatar")):
            st.markdown(message["content"])
    st.markdown("</div>", unsafe_allow_html=True)


# Topic selection as a chat message
def display_topic_buttons() -> None:
    st.session_state.selected_topic = st.segmented_control(
        "Topic selection",
        ["Rule Book", "Glossary", "News"],
        default=None,
        selection_mode="single",
        label_visibility="collapsed",
    )

    if (
        st.session_state.selected_topic
        and st.session_state.selected_topic not in st.session_state.llms
    ):
        st.session_state.llms[st.session_state.selected_topic] = {}
        st.session_state.llms[st.session_state.selected_topic]["memory"] = init_memory(
            llm,
        )

    if st.session_state.selected_topic == "Rule Book":
        if "vector_db" not in st.session_state.llms[st.session_state.selected_topic]:
            with st.spinner("Updating my rules knowledge, please wait."):
                st.session_state.llms[st.session_state.selected_topic]["vector_db"] = (
                    load_vector_db(faiss_rulebook)
                )
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "You've selected *Rule Book*. (Type 'Change topic' to change selection)",
                "avatar": "⚙️",
            },
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": "Let's dive in!"},
        )
        st.session_state.input_message = "Let's discuss some NFL rules!"

    if st.session_state.selected_topic == "Glossary":
        if "vector_db" not in st.session_state.llms[st.session_state.selected_topic]:
            with st.spinner("Studying glossary, please wait."):
                st.session_state.llms[st.session_state.selected_topic]["vector_db"] = (
                    load_vector_db(faiss_glossary)
                )
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "You've selected *Glossary*. (Type 'Change topic' to change selection)",
                "avatar": "⚙️",
            },
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": "Let's dive in!"},
        )
        st.session_state.input_message = "Let's discuss some NFL glossary!"

    if st.session_state.selected_topic == "News":
        if (
            "vector_db" not in st.session_state.llms[st.session_state.selected_topic]
        ) or (
            server_state["news_infos"]["faiss_updated"]
            < server_state["news_infos"]["last_updated"]
        ):
            with st.spinner("Studying latest news, please wait."):
                if (not server_state["news_infos"]["faiss"]) or (
                    server_state["news_infos"]["faiss_updated"]
                    < server_state["news_infos"]["last_updated"]
                ):
                    st.session_state.llms[st.session_state.selected_topic][
                        "vector_db"
                    ] = build_news_vector_db()
                    with no_rerun, server_state_lock["news_infos"]:
                        server_state["news_infos"]["faiss"] = st.session_state.llms[
                            st.session_state.selected_topic
                        ]["vector_db"]
                        server_state["news_infos"]["faiss_updated"] = datetime.now(
                            timezone.utc,
                        )
                else:
                    st.session_state.llms[st.session_state.selected_topic][
                        "vector_db"
                    ] = server_state["news_infos"]["faiss"]
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "You've selected *News*. (Type 'Change topic' to change selection)",
                "avatar": "⚙️",
            },
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": "Let's dive in!"},
        )
        st.session_state.input_message = "Let's discuss some NFL news!"

    if st.session_state.selected_topic:
        st.rerun()

    st.write("")


if not st.session_state.selected_topic:
    display_topic_buttons()

# Start conversation if topic is selected

if st.session_state.selected_topic:
    memory = st.session_state.llms[st.session_state.selected_topic]["memory"]
    retriever = st.session_state.llms[st.session_state.selected_topic][
        "vector_db"
    ].as_retriever(search_kwargs={"k": 5})

    chain = ConversationalRetrievalChain.from_llm(
        llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=False,
        verbose=0,
        combine_docs_chain_kwargs={"prompt": prompt},
        response_if_no_docs_found="Sorry, I don't know that. Maybe try to change the chat topic.",
    )

    # Fixed input field at the bottom
    st.markdown('<div class="fixed-input">', unsafe_allow_html=True)
    prompt = st.chat_input(st.session_state.input_message)
    st.markdown("</div>", unsafe_allow_html=True)

    if prompt:
        if prompt.lower() == "change topic":
            st.session_state.selected_topic = False
            st.chat_message("assistant").markdown("Sure! Let's change the topic.")
            st.chat_message("assistant", avatar="⚙️").markdown(
                "Please choose a new topic:",
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": "Sure! Let's change the topic."},
            )
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": "Please choose a new topic:",
                    "avatar": "⚙️",
                },
            )
            display_topic_buttons()
        else:
            # Display user message
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Generate assistant response
            with st.spinner("Hold tight, I'm about to throw a touchdown of a reply!"):
                # send question to chain to get answer
                answer = chain.invoke(prompt)
                response = answer["answer"]

            # Display assistant response
            st.chat_message("assistant").markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
