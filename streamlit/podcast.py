import streamlit as st
from sources.sql import create_sql_engine, get_news
sql_engine = create_sql_engine()

iframe = """
<iframe
src="https://nfl-ai-podcast.streamlit.app?embed=true"
style="height: 1000px; width: 100%; border: none;">
</iframe>
"""

st.markdown(iframe, unsafe_allow_html=True)
st.write("")
st.markdown("Due to library incompatibilities, the podcast is hosted on an external streamlit page. If the app does not load, please head over [here](https://nfl-ai-podcast.streamlit.app/) to wake it up.")

st.divider()

if st.button("Update News"):
    with st.spinner(text="Loading latest news..."):
        get_news(sql_engine)
    st.toast("News updated.")
    st.rerun()