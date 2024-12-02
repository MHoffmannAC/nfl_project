import pandas as pd
import numpy as np
from PIL import Image
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from io import StringIO
import dill 

import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Input
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from scikeras.wrappers import KerasClassifier

from sqlalchemy import text
from sources.sql import create_sql_engine
sql_engine = create_sql_engine()

st.header("LogoRecognizer")

@st.cache_resource
def load_model():
    with st.spinner("Loading model..."):
        with open('streamlit/sources/logo_model.pkl', 'rb') as f:
            logo_model = dill.load(f)
    return logo_model

logo_model = load_model()

st.write("Draw a logo of an NFL team and let the AI determine the team.")


col1, col2, col3 = st.columns([1,3,2])

with col1:

    # Specify canvas parameters in application
    st.session_state["drawing_mode"] = st.selectbox(
        "", ("freedraw", "line", "rect", "circle", "transform")
    )

    st.session_state["stroke_width"] = st.slider("Stroke width: ", 1, 25, 3)

    if st.session_state["drawing_mode"] == 'point':
        point_display_radius = st.slider("Point display radius: ", 1, 25, 3)

    col11, col12 = st.columns(2)
    with col11:
        st.session_state["stroke_color"] = st.color_picker("Stroke color: ")
    with col12:
        st.session_state["stroke_opacity"] = st.slider("Stroke opacity:", 0.0, 1.0, value=1.0)
        st.session_state["stroke_opacity"] = hex(int(20.0+st.session_state["stroke_opacity"]*235.0))[-2:]

    col11, col12 = st.columns(2)
    with col11:
        st.session_state["fill_color"] = st.color_picker("Fill color: ")
        st.session_state["bg_color"] = st.color_picker("Background: ", "#eee")
    with col12:
        st.session_state["fill_opacity"] = st.slider("Fill opacity:", 0.0, 1.0, value=1.0)
        st.session_state["fill_opacity"] = hex(int(20.0+st.session_state["fill_opacity"]*235.0))[-2:]


with col2:


    # Create a canvas component
    canvas_result = st_canvas(
        fill_color=st.session_state["fill_color"]+st.session_state["fill_opacity"],  
        stroke_width=st.session_state["stroke_width"],
        stroke_color=st.session_state["stroke_color"]+st.session_state["stroke_opacity"],
        background_color=st.session_state["bg_color"],
        background_image=None,  #Image.open(bg_image) if bg_image else None,
        update_streamlit=True,
        height=400,
        width=400,
        drawing_mode=st.session_state["drawing_mode"],
        point_display_radius=point_display_radius if st.session_state["drawing_mode"] == 'point' else 0,
        key="canvas",
    )

    if canvas_result.image_data is not None:

        def preprocess_images(image_list, target_size=(100, 100)):
            processed_images = []
            for img in image_list:
                img = img.resize(target_size)  # Resize image
                img = img.convert('RGB')       # Convert to RGB
                img_array = np.array(img) / 255.0  # Convert to array and normalize
                processed_images.append(img_array)
            return np.array(processed_images)
        image = Image.fromarray(canvas_result.image_data)
        teams = sql_engine.connect().execute(text(f"SELECT team_id, name, logo FROM teams")).fetchall()
        teams_dict = {i[0]-1: i[1] for i in teams}
        image_for_prediction = np.expand_dims(preprocess_images([image])[0], axis=0)
        #st.write(logo_model.predict(image_for_prediction))
        team_decoder = {0: 0, 1: 2, 2: 5, 3: 6, 4: 8, 5: 15, 6: 16, 7: 18, 8: 20, 9: 22, 10: 24, 11: 25}
        #st.write(logo_model.predict(image_for_prediction))
        probability = logo_model.predict(image_for_prediction)[0][logo_model.predict(image_for_prediction).argmax()]
        if probability > 0.3:
            st.success(f"The AI predicts: I think you are drawing the {teams_dict[team_decoder[logo_model.predict(image_for_prediction).argmax()]]}. I am {round(probability*100)}% certain.")
        else:
            st.error("The AI predicts: I am not sure yet, please continue drawing")

    url = "https://nfllogos-htglyicwaualwzhbrs2les.streamlit.app/"
        
    st.markdown("The model is still in training, feel free to add your own drawings to the database [here](%s)" % url)


with col3:
        st.write("Upload a (drawn) logo of an NFL team and let the AI determine the team.")
        logo_upload = st.file_uploader("File uploader:", type=["png", "jpg"])
        if logo_upload is not None:
            image = Image.open(logo_upload)
            houstan = np.expand_dims(preprocess_images([image])[0], axis=0)
            st.image(houstan, caption="Uploaded Image in RGB", use_container_width=True)
            st.write(houstan.shape)
            st.write(logo_model.predict(houstan))
            st.write(teams_dict[logo_model.predict(houstan).argmax()])

# weight = st.slider("  ", 0.0, 1.0, 0.0)

# mixed_image = image_for_prediction + weight * (houstan - image_for_prediction)
# st.image(mixed_image, caption="mixed image", use_container_width=True)
# st.write(mixed_image.shape)
# st.write(logo_model.predict(mixed_image))
# st.write(teams_dict[logo_model.predict(mixed_image).argmax()])
