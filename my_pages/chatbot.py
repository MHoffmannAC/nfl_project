import streamlit as st

from langchain_huggingface import HuggingFaceEndpoint, HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import os

os.environ.pop('HF_TOKEN', None)

hf_model = "meta-llama/Llama-3.2-3B-Instruct"
llm = HuggingFaceEndpoint(repo_id=hf_model, huggingfacehub_api_token = st.secrets['HF_TOKEN'])

# prompt
template = """You are a nice chatbot having a conversation with a human about the NFL. Keep your answers short and succinct. Only respond to the human's question without including further conversations that are not explicitly part of the chat history. In case you need to revise your answer, just provide the final response. Please be aware, humans like to change topics quickly. In that case just ignore your previous memory of the conversation. Please do not inform the human when you ignore the previous memory or similar technical details. Just provide the answer please.

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
faiss_folder_1 = "./ressources/chatbot/faiss_rulebook"
faiss_folder_2 = "./ressources/chatbot/faiss_glossary"

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
        position: fixed;
        bottom: 10px;
        left: 0;
        width: 100%;
        background-color: #00093a;
        padding: 10px;
        border-top: 1px solid #ccc;
    }
    div.stButton > button:first-child {
        background-color: #007BFF; /* Button color */
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
    col1, col2, _ = st.columns([1, 1, 6])

    with col1:
        if st.button("Rule Book"):
            with st.spinner("Updating my rules knowledge, please wait."):
                st.session_state.vector_db = load_vector_db(faiss_folder_1)
                st.session_state.messages.append({"role": "assistant", "content": "You've selected *Rule Book*. Let's dive in!"})
                st.session_state.selected_topic = True
                st.session_state.input_message = "Let's discuss some NFL rules!"

    with col2:
        if st.button("Glossary"):
            with st.spinner("Studying glossary, please wait."):
                st.session_state.vector_db = load_vector_db(faiss_folder_2)
                st.session_state.messages.append({"role": "assistant", "content": "You've selected *Glossary*. Let's dive in!"})
                st.session_state.selected_topic = True
                st.session_state.input_message = "Let's discuss some NFL glossary!"
    st.write("")

if not st.session_state.selected_topic:
    display_topic_buttons()

# Start conversation if topic is selected
if st.session_state.selected_topic:
    retriever = st.session_state.vector_db.as_retriever(search_kwargs={"k": 5})
    chain = ConversationalRetrievalChain.from_llm(llm,
                                                  retriever=retriever,
                                                  memory=memory,
                                                  return_source_documents=True,
                                                  verbose=1,
                                                  combine_docs_chain_kwargs={"prompt": prompt},
                                                  response_if_no_docs_found="Sorry, I don't know that. Maybe try to change the chat topic.")

    # Fixed input field at the bottom
    st.markdown('<div class="fixed-input">', unsafe_allow_html=True)
    prompt = st.chat_input(st.session_state.input_message)
    st.markdown('</div>', unsafe_allow_html=True)

    if prompt:
        if prompt.lower() == "change topic":
            st.session_state.selected_topic = False
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
