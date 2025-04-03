import streamlit as st
from streamlit_server_state import server_state, server_state_lock
from streamlit_tree_select import tree_select

# Initialize "rooms" in server_state if not already present
if "rooms" not in server_state:
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

def find_label_for_value(tree, value):
    for node in tree:
        if node["value"] == value:
            return node["label"]
        if "children" in node:
            label = find_label_for_value(node["children"], value)
            if label:
                return label
    return None

def find_checked_and_expanded(tree, checked_value):
    checked_nodes = []
    expanded_nodes = []

    def traverse(node, parent_expanded=False):
        node_value = node["value"]
        is_checked = node_value == checked_value
        has_checked_child = False

        # Traverse the children if they exist
        if "children" in node:
            for child in node["children"]:
                # Recursively traverse the child node and check if it is checked
                child_has_checked = traverse(child, parent_expanded=is_checked)
                has_checked_child = has_checked_child or child_has_checked

        # If this node is checked, add it to the checked_nodes list
        if is_checked:
            checked_nodes.append(node_value)

        # If the node has checked children, it should be expanded
        if has_checked_child:
            expanded_nodes.append(node_value)

        return has_checked_child or is_checked

    # Start traversal from each node in the tree
    for node in tree:
        traverse(node)

    return checked_nodes, expanded_nodes

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
rooms = extract_all_values(nodes)

if "checked_node" not in st.session_state:
    st.session_state["checked_node"] = None
checked_nodes = []
checked_nodes, expanded_nodes = find_checked_and_expanded(nodes, st.session_state["checked_node"])
for room in rooms:
    room_key = f"room_{room}"
    if room_key not in server_state:
        with server_state_lock[room_key]:
            server_state[room_key] = []

is_admin_logged_in = st.session_state.get("admin_logged_in", False)

col1, col2 = st.columns([1, 4])

with col1:
    st.subheader("Rooms")
    
    selected_nodes = tree_select(nodes, check_model="leaf", no_cascade=True, show_expand_all=True, expand_on_click=False, checked=[node for node in checked_nodes], expanded=expanded_nodes)

    current_checked = selected_nodes.get("checked", [])
    if current_checked:
        if len(current_checked) > 1:
            previous_checked_node = st.session_state["checked_node"]
            current_checked = [node for node in current_checked if node != previous_checked_node]
            st.session_state["checked_node"] = current_checked[0] if current_checked else None
            st.rerun()
        else:
            st.session_state["checked_node"] = current_checked[0]

    selected_room_value = st.session_state["checked_node"]
    selected_room_label = find_label_for_value(nodes, selected_room_value)

    if not selected_room_value:
        st.info("Please select a room.")
        st.stop()


with col2:
    st.header(f"Room: {selected_room_label}")

    room_key = f"room_{selected_room_value}"

    if not "nickname" in st.session_state:
        nickname_key = f"nickname_{selected_room_value}"
        nickname_input = st.text_input("Your nickname", key=nickname_key)
        if nickname_input != "":
            st.session_state["nickname"] = nickname_input
            if st.session_state["nickname"] == "Admin" and (not is_admin_logged_in):
                st.error("Please use a different name!")
                st.session_state["nickname"] = None
                st.stop()
            elif not st.session_state["nickname"]:
                st.warning("Please enter a nickname to join the room.")
                st.stop()
            else:
                st.rerun()

    else:
        message_key = f"message_input_{selected_room_value}"
        def send_message():
            message_text = st.session_state.get(message_key, "").strip()
            if message_text:
                new_message = {"nickname": st.session_state["nickname"], "text": message_text}
                with server_state_lock[room_key]:
                    server_state[room_key].append(new_message)
                st.session_state[message_key] = ""  # Clear input box after sending

        st.text_input("Message", key=message_key, on_change=send_message)

    # Display chat history
    st.subheader("Chat history:")
    with server_state_lock[room_key]:
        msg_to_delete = None
        
        cols = st.columns([9,1])
        for msg in server_state[room_key]:
            with cols[0]:
                st.write(f"**{msg['nickname']}:** {msg['text']}")
            is_admin_logged_in = st.session_state.get("admin_logged_in", False)
            if is_admin_logged_in:
                with cols[1]:
                    if st.button("❌", key=f"delete_{msg['nickname']}_{msg['text']}"):
                        msg_to_delete = msg

        if msg_to_delete:
            with server_state_lock[room_key]:
                server_state[room_key].remove(msg_to_delete)
            st.success(f"Message '{msg_to_delete}' deleted successfully!")
            st.rerun()