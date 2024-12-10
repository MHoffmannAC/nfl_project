import streamlit as st

st.header("User login")
st.write("Some parts of the app require admin rights. Please login here:")

if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

if not st.session_state["admin_logged_in"]:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        # Validate credentials
        if submit_button:
            if username == st.secrets["admin_usr"] and password == st.secrets["admin_pwd"]:
                st.session_state["admin_logged_in"] = True
                st.success("Logged in successfully!")
                st.rerun()  # Refresh the page
            else:
                st.error("Invalid username or password. Please try again.")

else:
    st.success("You are already logged in as Admin.")
    if st.button("Logout"):
        st.session_state["admin_logged_in"] = False
        st.success("Logged out successfully!")
        st.rerun()