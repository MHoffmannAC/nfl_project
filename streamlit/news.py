import streamlit as st
from sources.sql import create_sql_engine, get_news, query_db

sql_engine = create_sql_engine()

st.title("News Page")

news = query_db(sql_engine, "SELECT * FROM news ORDER BY news_id DESC LIMIT 10;")

for news_i in news:
    st.write(news_i["headline"])

if st.button("Update News"):
    with st.spinner(text="Loading latest news..."):
        get_news(sql_engine)
    st.write("News updated.")
    st.rerun()