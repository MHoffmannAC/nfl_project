from datetime import datetime, timezone

from langchain.chains.base import Chain
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from sources.sql import create_sql_engine, get_news, query_db
from streamlit_server_state import no_rerun, server_state, server_state_lock

import streamlit as st

sql_engine = create_sql_engine()


@st.cache_resource
def create_llm() -> Chain:
    ChatGroq.model_rebuild()
    summary_prompt = PromptTemplate(
        input_variables=["text", "style"],
        template=(
            "Summarize the following text in such a way that it can be understood by a {style}. Answer such that it is neither overwhelming nor boring:\n\n"
            "Text: {text}\n\n"
            "Summary:"
        ),
    )
    llm = ChatGroq(
        groq_api_key=st.secrets["GROQ_TOKEN"],
        model_name="llama-3.1-8b-instant",
    )
    return summary_prompt | llm


summary_chain = create_llm()

news = query_db(
    sql_engine,
    "SELECT * FROM news WHERE published >= NOW() - INTERVAL 7 DAY ORDER BY published DESC;",
)

if "news_infos" not in server_state:
    with no_rerun, server_state_lock["news_infos"]:
        server_state["news_infos"] = {}
if "last_updated" not in server_state["news_infos"]:
    with no_rerun, server_state_lock["news_infos"]:
        latest_news = query_db(
            sql_engine,
            "SELECT published FROM news ORDER BY published DESC LIMIT 1;",
        )
        server_state["news_infos"] = {
            "last_updated": latest_news[0]["published"].replace(tzinfo=timezone.utc),
        }

st.title("News Summarizer", anchor=False)

st.write(
    "Get a summary of the latest american football related news. Choose a news and a style.",
)


@st.fragment
def news_summary_fragment() -> None:
    headline_to_story = {i["headline"]: i["story"] for i in news}
    headline_to_id = {i["headline"]: i["news_id"] for i in news}
    headline = st.selectbox(
        "Select a news:",
        options=[i["headline"] for i in news],
        index=None,
        placeholder="",
    )

    style = st.segmented_control(
        "Choose a target audience to decide how do present the news:",
        ["NFL expert", "Normal person", "Child", "Custom"],
        default=None,
        selection_mode="single",
    )

    if style == "Custom":
        custom_style = st.text_input(
            "Enter a custom style prompt for the summary (e.g., 'Shape your response targeted at a college student who watches football occasionally and enjoys learning about the sport'):",
            placeholder="Shape your response targeted at a college student who watches football occasionally and enjoys learning about the sport",
        )

    if headline is not None and not (style == "Custom" and not custom_style):
        story = headline_to_story[headline]
        news_id = headline_to_id[headline]

        long_style = {
            "NFL expert": "'An NFL Expert who watches almost every game and is very familiar with the terminology and is particularly interested in statistics'",
            "Normal person": "'An average person who might watch some games every now and then but besides that is not much involved with American Football or the NFL'",
            "Child": "'Five year old child who knows nothing about football but is super enthusiastic to learn, yet needs most american football related words explained in an easy understandable way by relating to kids topics'",
        }

        prompt = None
        if style == "Custom":
            prompt = custom_style
        elif style in long_style:
            prompt = long_style[style]

        if style and prompt:
            sql_column = {
                "NFL expert": "ai_expert",
                "Normal person": "ai_normal",
                "Child": "ai_child",
            }.get(style)
            st.markdown("---")
            st.subheader(headline, anchor=False)
            if sql_column:
                ai_from_sql = query_db(
                    sql_engine,
                    f"SELECT {sql_column} FROM news WHERE news_id = :news_id;",  # noqa: S608
                    news_id=news_id,
                )[0][sql_column]
            else:
                ai_from_sql = None
            if ai_from_sql:
                styled_summary = ai_from_sql
            else:
                styled_summary = summary_chain.invoke(
                    {"text": story, "style": prompt},
                ).content
                if sql_column:
                    query_db(
                        sql_engine,
                        f"UPDATE news SET {sql_column} = :styled_summary WHERE news_id = :news_id;",  # noqa: S608
                        styled_summary=styled_summary,
                        news_id=news_id,
                    )

            st.write(styled_summary)
        st.divider()
        if st.toggle("Display original news"):
            st.write(story)


news_summary_fragment()

st.divider()


@st.fragment
def update_news_fragment() -> None:
    if st.button("Update News"):
        with st.spinner(text="Loading latest news..."):
            get_news(sql_engine)
            with no_rerun, server_state_lock["news_infos"]:
                server_state["news_infos"]["last_updated"] = datetime.now(timezone.utc)
        st.toast("News updated.")
        st.rerun()
    st.markdown("Last updated:")
    st.write(server_state["news_infos"]["last_updated"].strftime("%Y-%m-%d %H:%M %Z"))


update_news_fragment()
