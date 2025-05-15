import streamlit as st
from streamlit_server_state import server_state, server_state_lock, no_rerun
import streamlit_antd_components as sac
from streamlit_autorefresh import st_autorefresh

from datetime import datetime
from profanity_check import predict

from sources.sql import validate_username


# Initialize "rooms" in server_state if not already present
if "rooms" not in server_state:
    with no_rerun:
        with server_state_lock["rooms"]:
            server_state["rooms"] = []

def extract_all_values(nodes):
    values = []
    def traverse(node):
        values.append(node["value"])
        if "children" in node:
            for child in node["children"]:
                traverse(child)
    for node in nodes:
        traverse(node)
    return values

def find_value_for_label(tree, label):
    for node in tree:
        if node["label"] == label:
            return node["value"]
        if "children" in node:
            value = find_value_for_label(node["children"], label)
            if value:
                return value
    return None

#format for streamlit_tree_select
nodes = [
    {"label": "General", "value": "general"},
    {"label": "AFC", "value": "afc", "children": [
        {"label": "AFC East", "value": "afc_east", "children": [
            {"label": "Buffalo Bills", "value": "buffalo_bills"},
            {"label": "Miami Dolphins", "value": "miami_dolphins"},
            {"label": "New England Patriots", "value": "new_england_patriots"},
            {"label": "New York Jets", "value": "new_york_jets"}
        ]},
        {"label": "AFC North", "value": "afc_north", "children": [
            {"label": "Baltimore Ravens", "value": "baltimore_ravens"},
            {"label": "Cincinnati Bengals", "value": "cincinnati_bengals"},
            {"label": "Cleveland Browns", "value": "cleveland_browns"},
            {"label": "Pittsburgh Steelers", "value": "pittsburgh_steelers"}
        ]},
        {"label": "AFC South", "value": "afc_south", "children": [
            {"label": "Houston Texans", "value": "houston_texans"},
            {"label": "Indianapolis Colts", "value": "indianapolis_colts"},
            {"label": "Jacksonville Jaguars", "value": "jacksonville_jaguars"},
            {"label": "Tennessee Titans", "value": "tennessee_titans"}
        ]},
        {"label": "AFC West", "value": "afc_west", "children": [
            {"label": "Denver Broncos", "value": "denver_broncos"},
            {"label": "Kansas City Chiefs", "value": "kansas_city_chiefs"},
            {"label": "Las Vegas Raiders", "value": "las_vegas_raiders"},
            {"label": "Los Angeles Chargers", "value": "los_angeles_chargers"}
        ]}
    ]},
    {"label": "NFC", "value": "nfc", "children": [
        {"label": "NFC East", "value": "nfc_east", "children": [
            {"label": "Dallas Cowboys", "value": "dallas_cowboys"},
            {"label": "New York Giants", "value": "new_york_giants"},
            {"label": "Philadelphia Eagles", "value": "philadelphia_eagles"},
            {"label": "Washington Commanders", "value": "washington_commanders"}
        ]},
        {"label": "NFC North", "value": "nfc_north", "children": [
            {"label": "Chicago Bears", "value": "chicago_bears"},
            {"label": "Detroit Lions", "value": "detroit_lions"},
            {"label": "Green Bay Packers", "value": "green_bay_packers"},
            {"label": "Minnesota Vikings", "value": "minnesota_vikings"}
        ]},
        {"label": "NFC South", "value": "nfc_south", "children": [
            {"label": "Atlanta Falcons", "value": "atlanta_falcons"},
            {"label": "Carolina Panthers", "value": "carolina_panthers"},
            {"label": "New Orleans Saints", "value": "new_orleans_saints"},
            {"label": "Tampa Bay Buccaneers", "value": "tampa_bay_buccaneers"}
        ]},
        {"label": "NFC West", "value": "nfc_west", "children": [
            {"label": "Arizona Cardinals", "value": "arizona_cardinals"},
            {"label": "Los Angeles Rams", "value": "los_angeles_rams"},
            {"label": "San Francisco 49ers", "value": "san_francisco_49ers"},
            {"label": "Seattle Seahawks", "value": "seattle_seahawks"}
        ]}
    ]}
]

def convert_nodes_to_sac_tree_items(nodes):
    def convert_node(node):
        children = [convert_node(child) for child in node.get("children", [])]
        return sac.TreeItem(
            label=node["label"],
            tooltip=node["value"],  # store original "value" for reference
            children=children if children else None
        )
    return [convert_node(node) for node in nodes]

rooms = extract_all_values(nodes)

for room in rooms:
    room_key = f"room_{room}"
    with no_rerun:
        if room_key not in server_state:
            with server_state_lock[room_key]:
                server_state[room_key] = []

col1, col2 = st.columns([2, 4], gap="large")

with col1:    
    if st.session_state.get("selected_chat_room", "no_room") == "no_room":
        st.info("Please select a room.")
        st.session_state["selected_chat_room"] = "no_room"
    selected_nodes = sac.tree(
                            items=convert_nodes_to_sac_tree_items(nodes),
                            label='## Chat rooms',
                            icon='',
                            checkbox=False,
                            open_all=False,
                            on_change=st.rerun,
                            key="antd_tree",
                            )
    if selected_nodes:
        if len(selected_nodes) == 1:
            selected_nodes = selected_nodes[0]

    selected_room_label = selected_nodes
    selected_room_value = find_value_for_label(nodes, selected_room_label)
    if selected_room_value:
        if not selected_room_value == st.session_state["selected_chat_room"]:
            st.session_state["selected_chat_room"] = selected_room_value
            st.rerun()
        st_autorefresh(10000)
    else:
        st_autorefresh(1000)



if selected_room_value:
    with col2:
        st.header(f"Selected room: {selected_room_label}")

        room_key = f"room_{selected_room_value}"

        if not "chat_username" in st.session_state:
            if st.session_state.get("username", None):
                st.session_state["chat_username"] = st.session_state["username"]
                st.rerun()
            else:
                chat_username_key = f"chat_username_{selected_room_value}"
                chat_username_input = st.text_input("Select your nickname", key=chat_username_key)
                if chat_username_input:
                    if validate_username(chat_username_input):
                        st.session_state["chat_username"] = chat_username_input
                        st.rerun()
                    else:
                        st.warning("Please use a different name!")

                else:
                    st.success("Please enter a nickname to join the room.")

        else:
            message_key = f"message_input_{selected_room_value}"
            def send_message():
                message_text = st.session_state.get(message_key, "").strip()
                if message_text:
                    if predict([message_text]) == 0:
                        new_message = {"chat_username": st.session_state["chat_username"], "text": message_text, "time": datetime.now()}
                        with server_state_lock[room_key]:
                            server_state[room_key].append(new_message)
                    else:
                        st.warning("Your text seems inappropriate!")
                    st.session_state[message_key] = ""  # Clear input box after sending

            st.text_area("Message", key=message_key, placeholder="Type your message or paste an URL to an image", height=100, max_chars=1000, label_visibility="visible", on_change=send_message, help="test")

        # Display chat history
        st.subheader("Chat history:")
        with server_state_lock[room_key]:
            msg_to_delete = None
            
            for msg in server_state[room_key][::-1]:
                cols = st.columns([2,9,1], gap="medium")
                with cols[0]:
                    st.write(f"**{msg['chat_username']}**  \n  **[{msg['time'].strftime('%m/%d - %H:%M')}]**")
                with cols[1]:
                    try:
                        st.image(msg['text'], width=250)
                    except:
                        st.write(f"{msg['text']}")
                    
                if st.session_state.get("roles", False) == "admin":
                    with cols[2]:
                        if st.button("❌", key=f"delete_{msg['chat_username']}_{msg['text']}_{msg['time']}"):
                            msg_to_delete = msg
                            with server_state_lock[room_key]:
                                server_state[room_key].remove(msg_to_delete)
                            st.rerun()
                st.divider()