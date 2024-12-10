import streamlit as st
from streamlit_server_state import server_state, server_state_lock

# Initialize "rooms" in server_state if not already present
if "rooms" not in server_state:
    with server_state_lock["rooms"]:
        server_state["rooms"] = []

rooms: list[str] = server_state["rooms"]

for room in rooms:
    room_key = f"room_{room}"
    if room_key not in server_state:
        with server_state_lock[room_key]:
            server_state[room_key] = []

is_admin_logged_in = st.session_state.get("admin_logged_in", False)

# Define columns for layout
col1, col2 = st.columns([1, 4])

# --- COLUMN 1: Room Selection and Creation ---
with col1:
    st.subheader("Rooms")

    # Room selection
    selected_room = st.radio("Select room", rooms, key="selected_room", index=rooms.index("General") if "General" in rooms else None)

    if is_admin_logged_in:
        toggle_admin = st.toggle("Toggle admin options")
        if toggle_admin:

            with st.form("create_room_form"):
                new_room_name = st.text_input("New room:", key="new_room_name")
                create_room_btn = st.form_submit_button("Create Room")
                room_key = f"room_{new_room_name}"
                if create_room_btn and new_room_name:
                    with server_state_lock["rooms"]:
                        if new_room_name not in server_state["rooms"]:
                            server_state["rooms"].append(new_room_name)
                            st.success(f"Room '{new_room_name}' created!")
                        else:
                            st.warning(f"Room '{new_room_name}' already exists!")

            room_to_delete = None

            for room in rooms:
                cols = st.columns([4, 1])
                with cols[0]:
                    st.write(f"**{room}**")
                with cols[1]:
                    if st.button("❌", key=f"delete_{room}"):
                        room_to_delete = room

            # Delete the selected room
            if room_to_delete:
                with server_state_lock["rooms"]:
                    server_state["rooms"].remove(room_to_delete)
                room_key = f"room_{room_to_delete}"
                if room_key in server_state:
                    with server_state_lock[room_key]:
                        del server_state[room_key]
                st.success(f"Room '{room_to_delete}' deleted successfully!")
                st.rerun()

    # Stop if no room is selected
    if not selected_room:
        st.info("Please create or select a room.")
        st.stop()


# --- COLUMN 2: Room Messages ---
with col2:
    st.header(f"Room: {selected_room}")

    room_key = f"room_{selected_room}"

    if not "nickname" in st.session_state:
        nickname_key = f"nickname_{selected_room}"
        nickname = st.text_input("Your nickname", key=nickname_key)
        if nickname == "Admin" and (not is_admin_logged_in):
            st.error("Please use a different name!")
            nickname = None
            st.stop()
        elif not nickname:
            st.warning("Please enter a nickname to join the room.")
            #st.stop()

    if nickname:
        message_key = f"message_input_{selected_room}"
        def send_message():
            message_text = st.session_state.get(message_key, "").strip()
            if message_text:
                new_message = {"nickname": nickname, "text": message_text}
                with server_state_lock[room_key]:
                    server_state[room_key].append(new_message)
                st.session_state[message_key] = ""  # Clear input box after sending

        st.text_input("Message", key=message_key, on_change=send_message)

    # Display chat history
    st.subheader("Chat:")
    with server_state_lock[room_key]:
        msg_to_delete = None
        
        cols = st.columns([9,1])
        for msg in server_state[room_key]:
            with cols[0]:
                st.write(f"**{msg['nickname']}:** {msg['text']}")
            if toggle_admin:
                with cols[1]:
                    if st.button("❌", key=f"delete_{msg['nickname']}_{msg['text']}"):
                        msg_to_delete = msg

        if msg_to_delete:
            with server_state_lock[room_key]:
                server_state[room_key].remove(msg_to_delete)
            st.success(f"Message '{msg_to_delete}' deleted successfully!")
            st.rerun()