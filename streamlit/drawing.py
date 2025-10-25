from datetime import datetime, timedelta, timezone
from pathlib import Path

import dill
import numpy as np
import pandas as pd
from PIL import Image
from sources.sql import create_sql_engine, query_db
from sqlalchemy import text
from streamlit_drawable_canvas import st_canvas
from streamlit_image_comparison import image_comparison
from tensorflow.keras import Sequential

import streamlit as st

sql_engine = create_sql_engine()
WHITE_THRESHOLD = 0.95
PROBA_THRESHOLD = 0.3
MODEL_PATH = Path("streamlit/sources/logo_model.pkl")

st.title("LogoRecognizer", anchor=False)


@st.cache_resource
def load_model() -> Sequential:
    with st.spinner("Loading model..."), MODEL_PATH.open("rb") as f:
        return dill.load(f)  # TODO: change to keras load model


logo_model = load_model()


def get_team_prediction(image_for_prediction: np.ndarray) -> None:
    probability = logo_model.predict(image_for_prediction)[0][
        logo_model.predict(image_for_prediction).argmax()
    ]
    if probability > PROBA_THRESHOLD:
        st.success(
            f"AI prediction: I think you are drawing the {teams_dict[logo_model.predict(image_for_prediction).argmax()]}. I am {round(probability * 100)}% certain.",
        )
    else:
        st.error("AI prediction: I am not sure yet, please continue drawing")


st.write("Draw a logo of an NFL team and let the AI determine the team.")

col1, col2, col3 = st.columns([1, 3, 2])

with col1:
    # Specify canvas parameters in application
    st.session_state["drawing_mode"] = st.selectbox(
        "Drawing mode",
        ("freedraw", "line", "rect", "circle", "transform"),
        label_visibility="collapsed",
    )

    st.session_state["stroke_width"] = st.slider("Stroke width: ", 1, 25, 3)

    if st.session_state["drawing_mode"] == "point":
        point_display_radius = st.slider("Point display radius: ", 1, 25, 3)

    col11, col12 = st.columns(2)
    with col11:
        st.session_state["stroke_color"] = st.color_picker("Stroke color: ")
    with col12:
        st.session_state["stroke_opacity"] = st.slider(
            "Stroke opacity:",
            0.0,
            1.0,
            value=1.0,
        )
        st.session_state["stroke_opacity"] = hex(
            int(20.0 + st.session_state["stroke_opacity"] * 235.0),
        )[-2:]

    col11, col12 = st.columns(2)
    with col11:
        st.session_state["fill_color"] = st.color_picker("Fill color: ")
        st.session_state["bg_color"] = st.color_picker("Background: ", "#fff")
    with col12:
        st.session_state["fill_opacity"] = st.slider(
            "Fill opacity:",
            0.0,
            1.0,
            value=1.0,
        )
        st.session_state["fill_opacity"] = hex(
            int(20.0 + st.session_state["fill_opacity"] * 235.0),
        )[-2:]


with col2:
    # Create a canvas component
    canvas_result = st_canvas(
        fill_color=st.session_state["fill_color"] + st.session_state["fill_opacity"],
        stroke_width=st.session_state["stroke_width"],
        stroke_color=st.session_state["stroke_color"]
        + st.session_state["stroke_opacity"],
        background_color=st.session_state["bg_color"],
        background_image=None,  # Image.open(bg_image) if bg_image else None,
        update_streamlit=True,
        height=400,
        width=400,
        drawing_mode=st.session_state["drawing_mode"],
        point_display_radius=point_display_radius
        if st.session_state["drawing_mode"] == "point"
        else 0,
        key="canvas",
    )

    if canvas_result.image_data is not None:

        def preprocess_images(
            image_list: list[Image.Image],
            target_size: tuple[int, int] = (100, 100),
        ) -> np.ndarray:
            processed_images = []
            for img in image_list:
                processed_img = img.resize(target_size)
                processed_img = processed_img.convert("RGB")
                img_array = np.array(processed_img) / 255.0
                processed_images.append(img_array)
            return np.array(processed_images)

        image = Image.fromarray(canvas_result.image_data)
        teams = (
            sql_engine.connect()
            .execute(text("SELECT team_id, name, logo FROM teams"))
            .fetchall()
        )
        teams_dict = {i[0] - 1: i[1] for i in teams}
        image_for_prediction = np.expand_dims(preprocess_images([image])[0], axis=0)

        get_team_prediction(image_for_prediction)

with col3:
    st.write("Upload a (drawn) logo of an NFL team and let the AI determine the team.")
    logo_upload = st.file_uploader("File uploader:", type=["png", "jpg"])
    if logo_upload is not None:
        image = Image.open(logo_upload)
        uploaded_image = np.expand_dims(preprocess_images([image])[0], axis=0)
        st.image(uploaded_image, width="stretch")
        get_team_prediction(uploaded_image)

st.divider()


if "last_submission" not in st.session_state:
    st.session_state["last_submission"] = datetime.now(timezone.utc)

col1, _ = st.columns(2)
with col1:
    st.write("")
    show_upload = st.toggle(
        "Show upload settings: The prediction model is still in training. Feel free to add your own drawings to the database to improve it, in particular if the model's prediction was wrong.",
        value=False,
        key=None,
        help=None,
        on_change=None,
        args=None,
        kwargs=None,
        disabled=False,
        label_visibility="visible",
    )

    if show_upload:
        teams = pd.DataFrame(query_db(sql_engine, "SELECT * FROM teams;"))
        teams = teams.loc[~(teams["team_id"].isin([-2, -1, 31, 32]))]
        teams = teams.sort_values(by="location")
        selected_team_name = st.selectbox(
            "Please select which team you have drawn:",
            options=list(teams["name"]),
            key="submit-team",
            index=None,
        )
        if selected_team_name is not None:
            selected_team_id = teams.loc[
                teams["name"] == selected_team_name,
                "team_id",
            ].to_numpy()[0]

        if st.button("Submit Image"):
            matches = np.all(
                canvas_result.image_data == np.array([255, 255, 255, 255]),
                axis=-1,
            )
            white_part = np.sum(matches) / (
                canvas_result.image_data.shape[0] * canvas_result.image_data.shape[1]
            )
            if white_part > WHITE_THRESHOLD:
                st.write("Please draw something before submission.")
            if selected_team_name is None:
                st.write("Please choose a team before submission.")
            else:
                current_time = datetime.now(timezone.utc)
                if current_time - st.session_state["last_submission"] >= timedelta(
                    minutes=1,
                ):
                    with st.spinner("Uploading Image..."):
                        image = Image.fromarray(canvas_result.image_data).convert("RGB")
                        image_array = np.array(image) / 255.0
                        np.set_printoptions(threshold=np.inf)
                        image_str = str(image_array)

                        query_db(
                            sql_engine,
                            "INSERT INTO logos (team_id, image) VALUES (:team_id, :image)",
                            team_id=int(selected_team_id),
                            image=image_str,
                        )

                    st.write("Submission successful. Thank you!")
                    st.session_state["last_submission"] = current_time
                else:
                    st.write(
                        "Please take your time to draw the image and try submitting again.",
                    )


@st.cache_resource(show_spinner=False)
def download_logos(min_id: int, max_id: int) -> list[dict]:
    return query_db(
        sql_engine,
        "SELECT logo_id, image, team_id FROM logos WHERE logo_id BETWEEN :min_id AND :max_id;",
        min_id=int(min_id),
        max_id=int(max_id),
    )


if st.session_state.get("roles", False) == "admin":
    st.divider()
    st.header("Admin settings", anchor=False)
    st.subheader("Display Logos from database", anchor=False)
    logos_limits = query_db(
        sql_engine,
        "SELECT MIN(logo_id) as 'min', MAX(logo_id) as 'max' FROM logos",
    )
    selected_range = st.slider(
        "Select Id range",
        min_value=logos_limits[0]["min"],
        max_value=logos_limits[0]["max"],
        value=(logos_limits[0]["min"], logos_limits[0]["max"]),
    )
    if "download_logos" not in st.session_state:
        if st.button("Download"):
            st.session_state["download_logos"] = True
            st.rerun()
    else:
        logos_db = download_logos(selected_range[0], selected_range[1])
        teams_db = query_db(sql_engine, "SELECT team_id, name, logo FROM teams;")
        teams_dict = {
            team["team_id"]: {"name": team["name"], "logo": team["logo"]}
            for team in teams_db
        }
        for image in logos_db:
            st.subheader(teams_dict[image["team_id"]]["name"], anchor=False)
            cols = st.columns([1, 1])
            with cols[0]:
                array = np.fromstring(
                    image["image"].replace("[", "").replace("]", ""),
                    sep=" ",
                ).reshape(400, 400, 3)
                array = (array * 255).astype(np.uint8)
                image_comparison(
                    img1=Image.fromarray(array, "RGB"),
                    img2=teams_dict[image["team_id"]]["logo"],
                    width=250,
                    show_labels=False,
                )
            with cols[1]:
                if st.button("Delete", key=f"delete_button_{image['logo_id']}"):
                    st.session_state["image_to_delete"] = image["logo_id"]
                    st.text_input(
                        "Confirm",
                        placeholder="Type 'delete' to confirm deletion",
                        label_visibility="visible",
                        key="user_confirmation",
                    )
            st.divider()

    if st.session_state.get(
        "user_confirmation",
        None,
    ) == "delete" and st.session_state.get("image_to_delete", False):
        image_to_delete = int(st.session_state["image_to_delete"])
        query_db(
            sql_engine,
            "DELETE FROM logos WHERE logo_id = :logo_id",
            logo_id=image_to_delete,
        )
        st.write(f"Image {st.session_state.get('image_to_delete', None)} was deleted!")
