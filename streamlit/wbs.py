from io import BytesIO

import fitz  # PyMuPDF
from PIL import Image

import streamlit as st

st.title("WBS Codingschool Community Demo Day", anchor=False)

st.write("""This app started as a final project during the Data Science Bootcamp of the [WBS Codingschool](https://tinyurl.com/wbscoding).

The project was chosen by a jury to be presented in front of the whole WBS community during a Community Demo Day.

Below you can find the slides for that presentation as well as a brief walkthrough video.
         """)

st.header("Slides", anchor=False)

if "wbs_page" not in st.session_state:
    st.session_state["wbs_page"] = 1

doc = fitz.open("./ressources/WBS-final_project.pdf")
num_pages = len(doc)

page = doc[st.session_state["wbs_page"] - 1]
pix = page.get_pixmap()
img = Image.open(BytesIO(pix.tobytes("ppm")))  # Convert to PIL image

# Display the image
st.image(img, caption=f"Page {st.session_state['wbs_page']}", width=1200)


page_selection = st.select_slider(
    "Select a page:",
    options=list(range(1, num_pages + 1)),
    value=st.session_state["wbs_page"],
    label_visibility="collapsed",
    format_func=lambda _: "",
)
if page_selection != st.session_state["wbs_page"]:
    st.session_state["wbs_page"] = page_selection
    st.rerun()


st.write("")
st.write("")
st.write("")

st.header("Video", anchor=False)
st.video("./ressources/NFL-WBS_final.mp4")

st.error("""If you consider diving into the world of Data Science, take a look at the bootcamps of the [WBS Codingschool](https://tinyurl.com/wbscoding).

If you just want to practice some basic Data Science skills, check out these [NFL-themed Exercises](https://nfl-ds-challenges.streamlit.app/).""")
