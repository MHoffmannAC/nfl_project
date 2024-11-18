import streamlit as st

from langchain_huggingface import HuggingFaceEndpoint, HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

from keys import HF_TOKEN

hf_model = "meta-llama/Llama-3.2-3B-Instruct"
llm = HuggingFaceEndpoint(repo_id=hf_model)

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

st.title("NFLBot: know everything about the NFL")

if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome! Please choose a topic to discuss:"}
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Topic selection as a chat message
def display_topic_buttons():
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Rule Book"):
            with st.spinner("Updating my rules knowledge, please wait."):
                st.session_state.vector_db = load_vector_db(faiss_folder_1)
                st.session_state.messages.append({"role": "assistant", "content": "You've selected *Rule Book*. Let's dive in! (Type 'Change topic' to select a different topic)"})
                st.session_state.selected_topic = True
                st.session_state.input_message = "Let's discuss some NFL rules!"

    with col2:
        if st.button("Glossary"):
            with st.spinner("Studying glossary, please wait."):
                st.session_state.vector_db = load_vector_db(faiss_folder_2)
                st.session_state.messages.append({"role": "assistant", "content": "You've selected *Glossary*. Let's dive in! (Type 'Change topic' to select a different topic)"})
                st.session_state.selected_topic = True
                st.session_state.input_message = "Let's discuss some NFL glossary!"

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
                                                  combine_docs_chain_kwargs={"prompt": prompt})

    # React to user input
    if prompt := st.chat_input(st.session_state.input_message):
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
