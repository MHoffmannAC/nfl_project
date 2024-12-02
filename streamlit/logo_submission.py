import streamlit as st
from streamlit_drawable_canvas import st_canvas
from datetime import datetime, timedelta
from PIL import Image
import numpy as np

from sources.sql import create_sql_engine
sql_engine = create_sql_engine()

if not "last_submission" in st.session_state:
    st.session_state["last_submission"] = datetime.now()

team_dict = {1: {'name': 'Atlanta Falcons', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/atl.png'}, 2: {'name': 'Buffalo Bills', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/buf.png'}, 3: {'name': 'Chicago Bears', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/chi.png'}, 4: {'name': 'Cincinnati Bengals', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/cin.png'}, 5: {'name': 'Cleveland Browns', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/cle.png'}, 6: {'name': 'Dallas Cowboys', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/dal.png'}, 7: {'name': 'Denver Broncos', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/den.png'}, 8: {'name': 'Detroit Lions', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/det.png'}, 9: {'name': 'Green Bay Packers', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/gb.png'}, 10: {'name': 'Tennessee Titans', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/ten.png'}, 11: {'name': 'Indianapolis Colts', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/ind.png'}, 12: {'name': 'Kansas City Chiefs', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/kc.png'}, 13: {'name': 'Las Vegas Raiders', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/lv.png'}, 14: {'name': 'Los Angeles Rams', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/lar.png'}, 15: {'name': 'Miami Dolphins', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/mia.png'}, 16: {'name': 'Minnesota Vikings', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/min.png'}, 17: {'name': 'New England Patriots', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/ne.png'}, 18: {'name': 'New Orleans Saints', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/no.png'}, 19: {'name': 'New York Giants', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png'}, 20: {'name': 'New York Jets', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png'}, 21: {'name': 'Philadelphia Eagles', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/phi.png'}, 22: {'name': 'Arizona Cardinals', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/ari.png'}, 23: {'name': 'Pittsburgh Steelers', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/pit.png'}, 24: {'name': 'Los Angeles Chargers', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/lac.png'}, 25: {'name': 'San Francisco 49ers', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/sf.png'}, 26: {'name': 'Seattle Seahawks', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/sea.png'}, 27: {'name': 'Tampa Bay Buccaneers', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/tb.png'}, 28: {'name': 'Washington Commanders', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png'}, 29: {'name': 'Carolina Panthers', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/car.png'}, 30: {'name': 'Jacksonville Jaguars', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/jax.png'}, 31: {'name': 'Afc', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/afc.png'}, 32: {'name': 'Nfc', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/nfc.png'}, 33: {'name': 'Baltimore Ravens', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/bal.png'}, 34: {'name': 'Houston Texans', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/hou.png'}}

st.header("NFL logo drawing")
st.write("Thanks for taking the time to pass by. Please draw an NFL logo and submit it via the submit button. Feel free to choose a team from the dropdown to show their respective logo as reference if needed.")

# Specify canvas parameters in application
st.session_state["drawing_mode"] = st.sidebar.selectbox(
    "Drawing tool:", ("freedraw", "line", "rect", "circle", "transform")
)

st.session_state["stroke_width"] = st.sidebar.slider("Stroke width: ", 1, 25, 3)

if st.session_state["drawing_mode"] == 'point':
    point_display_radius = st.sidebar.slider("Point display radius: ", 1, 25, 3)

col1, col2 = st.sidebar.columns(2)
with col1:
    st.session_state["stroke_color"] = st.color_picker("Stroke color: ")
with col2:
    st.session_state["stroke_opacity"] = st.slider("Stroke opacity:", 0.0, 1.0, value=1.0, label_visibility="hidden")
    st.session_state["stroke_opacity"] = hex(int(20.0+st.session_state["stroke_opacity"]*235.0))[-2:]

col1, col2 = st.sidebar.columns(2)
with col1:
    st.session_state["fill_color"] = st.color_picker("Fill color: ")
    st.session_state["bg_color"] = st.color_picker("Background: ", "#ffffff")
with col2:
    st.session_state["fill_opacity"] = st.slider("Fill opacity:", 0.0, 1.0, value=1.0, label_visibility="collapsed")
    st.session_state["fill_opacity"] = hex(int(20.0+st.session_state["fill_opacity"]*235.0))[-2:]

col1, col2 = st.columns(2)
with col1:

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
        pass

    team_names_to_ids = {value['name']: key for key, value in team_dict.items()}
    selected_team_name = st.selectbox("Please select which team you have drawn:", options=list(team_names_to_ids.keys()), key="submit-team", index=None)
    if not selected_team_name == None:
        selected_team_id = team_names_to_ids[selected_team_name]
    if st.button("Submit"):
        if (canvas_result.image_data is None) or (selected_team_name is None):
            st.write("Please draw something and choose a team before submission")
        else:
            current_time = datetime.now()
            if current_time - st.session_state["last_submission"] >= timedelta(minutes=1):
                image = Image.fromarray(canvas_result.image_data).convert('RGB')
                image_array = np.array(image) / 255.0
                np.set_printoptions(threshold=np.inf)
                with st.spinner("Uploading Image..."):
                    with sql_engine.connect() as conn:
                        conn.execute(text(f"INSERT INTO logos (team_id, image) VALUES ({selected_team_id}, '{image_array}')"))
                        conn.commit()
                    
                    imagefromsql = sql_engine.connect().execute(text(f"SELECT image FROM logos ORDER BY logo_id DESC LIMIT 1")).fetchone()[0]
                array = np.fromstring(imagefromsql.replace('[', '').replace(']', ''), sep=' ').reshape(400, 400, 3)
                array = (array * 255).astype(np.uint8)
                st.write("Submission successful. Thank you!")
                st.image(Image.fromarray(array, "RGB"))
                st.session_state["last_submission"] = current_time
            else:
                st.write("Please take your time to draw the image and try submitting again.")
        

with col2:
    selected_team_name2 = st.selectbox("Select a team to show their logo:", options=list(team_names_to_ids.keys()), index=None)
    if not selected_team_name2 == None:
        selected_team_id2 = team_names_to_ids[selected_team_name2]
        st.image(team_dict[selected_team_id2]['logo'])

