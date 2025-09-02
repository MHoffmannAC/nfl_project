import streamlit as st
import time

from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from sources.sql import create_sql_engine, get_news, query_db
sql_engine = create_sql_engine()

news_bot = st.segmented_control(
    options=["NewsSummarizer", "Podcast"],
    label="Select your desired news bot.",
    default=None
)

if news_bot == "NewsSummarizer":

    @st.cache_resource
    def create_llm():
        ChatGroq.model_rebuild()
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
        summary_chain = summary_prompt | llm
        return summary_chain

    summary_chain = create_llm()

    news = query_db(sql_engine, "SELECT * FROM news WHERE published >= NOW() - INTERVAL 7 DAY ORDER BY published DESC;")


    st.title("News Page", anchor=False)

    st.write("Get a summary of the latest american football related news. Choose a news and a style.")
    headline_to_story = {i["headline"]: i["story"] for i in news}
    headline_to_id = {i["headline"]: i["news_id"] for i in news}
    headline = st.selectbox("Select a news:", options=[i['headline'] for i in news], index=None, placeholder="")
    if headline is not None:
        story = headline_to_story[headline]
        news_id = headline_to_id[headline]
        style = st.segmented_control("Choose a target audience to decide how do present the news:", ["NFL expert", "Normal person", "Child"], default=None, selection_mode="single")
        long_style = {"NFL expert": "'An NFL Expert who watches almost every game and is very familiar with the terminology and is particularly interested in statistics'", 
                "Normal person": "'And average person who might watch some games every now and then but besides that is not much involved with American Football or the NFL'", 
                "Child": "'Five year old child who knows nothing about football but is super enthusiastic to learn, yet needs most american football related words explained in an easy understandable way by relating to kids topics'"}

        if (style is not None):
            sql_column = {"NFL expert": "ai_expert", 
                        "Normal person": "ai_normal", 
                        "Child": "ai_child"}[style]
            st.markdown("---")
            st.subheader(headline, anchor=False)
            ai_from_sql = query_db(sql_engine, f"SELECT {sql_column} FROM news WHERE news_id = {news_id};")[0][sql_column]
            if ai_from_sql:
                styled_summary = ai_from_sql
            else:
                styled_summary = summary_chain.invoke({"text": story, "style": style}).content
                query_db(sql_engine, f"UPDATE news SET {sql_column} = :styled_summary WHERE news_id = :news_id;", styled_summary=styled_summary, news_id=news_id)

            #def stream_summary(text):
            #    for chunk in text.split(' '):
            #        yield chunk + ' '
            #        time.sleep(0.15)
            #st.write_stream(stream_summary(styled_summary))
            st.write(styled_summary)
        st.divider()
        if st.toggle("Display original news"):

            st.write(story)
    st.markdown("---")

    if st.button("Update News"):
        with st.spinner(text="Loading latest news..."):
            get_news(sql_engine)
        st.write("News updated.")
        st.rerun()
        
elif news_bot == "Podcast":
    iframe = """
<iframe
    src="https://nfl-ai-podcast.streamlit.app?embed=true"
    style="height: 1000px; width: 100%; border: none;">
</iframe>
"""

    st.markdown(iframe, unsafe_allow_html=True)
else:
    st.error("Please select your desired NewsBot. Either get brief summaries in the style of your choice or listen to an AI generated podcast.")