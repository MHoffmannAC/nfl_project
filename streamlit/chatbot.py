import streamlit as st

from langchain_groq import ChatGroq

from langchain_huggingface import HuggingFaceEndpoint, HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

#import os
#os.environ.pop('HF_TOKEN', None)
#hf_model = "meta-llama/Llama-3.2-3B-Instruct"
#hf_model = "mistralai/Mistral-7B-Instruct-v0.3"
#llm = HuggingFaceEndpoint(repo_id=hf_model, huggingfacehub_api_token = st.secrets['HF_TOKEN'])
llm = ChatGroq(temperature=0,
               groq_api_key=st.secrets['GROQ_TOKEN'],
               model_name="mixtral-8x7b-32768")

# prompt
template = """You are a nice chatbot having a conversation with a human about the NFL.  Give only replies based on the provided extracted parts of long documents (the context). No need to mention explicitly something like "Based on the provided context". If you don't know the answer based on the provided context, just say "I don't know the answer.".

Previous conversation:
{chat_history}

Context to answer question:
{context}

New human question: {question}
Response:"""

prompt = PromptTemplate(template=template,
                        input_variables=["context", "question"])

# embeddings
embedding_model = "sentence-transformers/all-MiniLM-l6-v2"
faiss_rulebook = "./ressources/chatbot/faiss_rulebook"
faiss_glossary = "./ressources/chatbot/faiss_glossary"
faiss_news = "./ressources/chatbot/faiss_news"

@st.cache_resource(show_spinner=False)
def load_vector_db(folder_path):
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model,
                                       cache_folder="./ressources/chatbot/embeddings")
    return FAISS.load_local(folder_path, embeddings, allow_dangerous_deserialization=True)

# memory
@st.cache_resource(show_spinner=False)
def init_memory(_llm):
    return ConversationBufferMemory(
        llm=llm,
        output_key='answer',
        memory_key='chat_history',
        return_messages=True)

memory = init_memory(llm)

##### streamlit #####

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
    unsafe_allow_html=True
)

st.title("NFLBot: Know Everything About the NFL")

if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome! Please choose a topic to discuss:"}
    ]

# Display chat messages in a scrollable container
st.divider()
with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    st.markdown('</div>', unsafe_allow_html=True)

# Topic selection as a chat message
def display_topic_buttons():

    st.session_state.selected_topic = st.segmented_control("Topic selection", ["Rule Book", "Glossary", "News"], default=None, selection_mode="single", label_visibility="collapsed")

    if st.session_state.selected_topic == "Rule Book":
        with st.spinner("Updating my rules knowledge, please wait."):
            st.session_state.vector_db = load_vector_db(faiss_rulebook)
        st.session_state.messages.append({"role": "assistant", "content": "You've selected *Rule Book*. Let's dive in!"})
        st.session_state.selected_topic = True
        st.session_state.input_message = "Let's discuss some NFL rules!"

    if st.session_state.selected_topic == "Glossary":
        with st.spinner("Studying glossary, please wait."):
            st.session_state.vector_db = load_vector_db(faiss_glossary)
        st.session_state.messages.append({"role": "assistant", "content": "You've selected *Glossary*. Let's dive in!"})
        st.session_state.selected_topic = True
        st.session_state.input_message = "Let's discuss some NFL glossary!"

    if st.session_state.selected_topic == "News":
        with st.spinner("Studying latest news, please wait."):
            st.session_state.vector_db = load_vector_db(faiss_news)
        st.session_state.messages.append({"role": "assistant", "content": "You've selected *News*. Let's dive in!"})
        st.session_state.selected_topic = True
        st.session_state.input_message = "Let's discuss some NFL news!"

    st.write("")

if not st.session_state.selected_topic:
    display_topic_buttons()

# Start conversation if topic is selected
if st.session_state.selected_topic:
    retriever = st.session_state.vector_db.as_retriever(search_kwargs={"k": 5})
    chain = ConversationalRetrievalChain.from_llm(llm,
                                                  retriever=retriever,
                                                  memory=memory,
                                                  return_source_documents=False,
                                                  verbose=0,
                                                  combine_docs_chain_kwargs={"prompt": prompt},
                                                  response_if_no_docs_found="Sorry, I don't know that. Maybe try to change the chat topic.")

    # Fixed input field at the bottom
    st.markdown('<div class="fixed-input">', unsafe_allow_html=True)
    prompt = st.chat_input(st.session_state.input_message)
    st.markdown('</div>', unsafe_allow_html=True)

    if prompt:
        if prompt.lower() == "change topic":
            st.session_state.selected_topic = False
            st.chat_message("assistant").markdown("Sure! Let's change the topic. Please choose a new topic:")
            st.session_state.messages.append({"role": "assistant", "content": "Sure! Let's change the topic. Please choose a new topic:"})
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
