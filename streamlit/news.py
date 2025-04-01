import streamlit as st

from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from sources.sql import create_sql_engine, get_news, query_db
sql_engine = create_sql_engine()

@st.cache_resource
def create_llm():
    summary_prompt = PromptTemplate(
        input_variables=["text", "style"],
        template=(
            "Summarize the following text in such a way that it can be understood by a {style}, neither overwhelming the {style} nor boring the {style}:\n\n"
            "Text: {text}\n\n"
            "Summary:"
        )
    )
    llm = ChatGroq(groq_api_key=st.secrets['GROQ_TOKEN'],
                    model_name="gemma2-9b-it")
    summary_chain = LLMChain(llm=llm, prompt=summary_prompt)
    return summary_chain

summary_chain = create_llm()

news = query_db(sql_engine, "SELECT * FROM news ORDER BY news_id DESC LIMIT 50;")


st.title("News Page")

st.write("Get a summary of the latest american football related news. Choose a news and a style.")
headline_to_story = {i["headline"]: i["story"] for i in news}
headline = st.selectbox("Select a news:", options=[i['headline'] for i in news], index=None, placeholder="")
if headline is not None:
    story = headline_to_story[headline]
    style = st.segmented_control("Choose a target audience to decide how do present the news:", ["NFL expert", "Normal person", "Child"], default=None, selection_mode="single")
    long_style = {"NFL expert": "'An NFL Expert who watches almost every game and is very familiar with the terminology and is particularly interested in statistics'", 
              "Normal person": "'And average person who might watch some games every now and then but besides that is not much involved with American Football or the NFL'", 
              "Child": "'Five year old child who knows nothing about football but is super enthusiastic to learn, yet needs most american football related words explained in an easy understandable way by relating to kids topics'"}

    if (style is not None):
        st.markdown("---")
        st.subheader(headline)
        styled_summary = summary_chain.run({"text": story, "style": style})
        st.code(styled_summary, wrap_lines=True, language=None)

    if st.toggle("Display original news"):
        st.write(headline)
        st.write(story)
st.markdown("---")

if st.button("Update News"):
    with st.spinner(text="Loading latest news..."):
        get_news(sql_engine)
    st.write("News updated.")
    st.rerun()