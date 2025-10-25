from datetime import datetime, timedelta, timezone

from sources.sql import create_sql_engine, query_db

import streamlit as st

sql_engine = create_sql_engine()

if "last_submission" not in st.session_state:
    st.session_state["last_submission"] = datetime.now(timezone.utc)

st.title("Feedback", anchor=False)

st.write(
    "Thanks for checking out my NFL tools. Feel free to leave feedback or recommendations.",
)
st.write("")
col1, col2, _ = st.columns([1, 3, 4])
with col1:
    st.write("Feedback:")
with col2:
    feedback_text = st.text_area(
        "label",
        value="",
        height=200,
        max_chars=2000,
        label_visibility="collapsed",
    )
col1, col2, _ = st.columns([1, 3, 4])
with col1:
    st.write("Overall Rating:")
with col2:
    feedback_rating = st.feedback(options="faces")

if st.button("Submit"):
    if feedback_text == "":
        st.write("Please write some feedback before submission")
    else:
        current_time = datetime.now(timezone.utc)
        if current_time - st.session_state["last_submission"] >= timedelta(minutes=1):
            with st.spinner("Submitting Feedback..."):
                query_db(
                    sql_engine,
                    "INSERT INTO feedbacks (rating, text) VALUES (:rating, :text)",
                    rating=int(feedback_rating),
                    text=str(feedback_text),
                )
            st.write("Submission successful. Thank you!")
            st.session_state["last_submission"] = current_time
        else:
            st.write(
                "Please take your time to formulate a feedback and try submitting again.",
            )

if st.session_state.get("roles", False) == "admin":
    st.divider()
    st.subheader("Admin settings", anchor=False)
    feedback_limits = query_db(
        sql_engine,
        "SELECT MIN(feedback_id) as 'min', MAX(feedback_id) as 'max' FROM feedbacks",
    )
    cols = st.columns([1, 1])
    with cols[0]:
        selected_range = st.slider(
            "Select Id range",
            min_value=feedback_limits[0]["min"],
            max_value=feedback_limits[0]["max"],
            value=(feedback_limits[0]["min"], feedback_limits[0]["max"]),
        )
    feedbacks = query_db(
        sql_engine,
        "SELECT * FROM feedbacks WHERE feedback_id BETWEEN :min_id AND :max_id",
        min_id=int(selected_range[0]),
        max_id=int(selected_range[1]),
    )
    st.dataframe(feedbacks)
