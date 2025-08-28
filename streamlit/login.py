import streamlit as st
import streamlit_authenticator as stauth
from time import sleep

from sources.sql import create_sql_engine, text, query_db
sql_engine = create_sql_engine()

st.title("User login")

if not "authenticator" in st.session_state:
    
    st.session_state["user_data"] = {
    "usernames": {
        entry["user_name"]: {
            "password": entry["password"],
            "roles": entry["roles"],
            "email": entry["email"],
            "first_name": entry["first_name"],
            "last_name": entry["last_name"]
            }
        for entry in query_db(sql_engine, "SELECT * FROM users;")
        }
    }
    stauth.Hasher.hash_passwords(st.session_state["user_data"])
    st.session_state["authenticator"] = stauth.Authenticate(
        credentials = st.session_state["user_data"],
        cookie_name = "nfl-tools-cookie",
        cookie_key = "nfl-tools-cookie-key",
        cookie_expiry_days = 0,
        api_key = st.secrets["authenticator_api_key"]
    )

subpage = st.segmented_control("Select subpage", ["Login", "Register", "Forgot credentials", "Update details"], default="Login", label_visibility="collapsed")

def login_page():
    if st.session_state.get('authentication_status'):
        st.session_state["authenticator"].logout()
        if st.session_state.get("roles", None) == "admin":
            st.success(f'Welcome Admin. You are successfully logged in!')
        else:
            st.success(f'Welcome *{st.session_state.get("username")}*. You are successfully logged in!')
    else:
        try:
            st.session_state["authenticator"].login()
        except Exception as e:
            st.error(e)
        if st.session_state.get('authentication_status') is False:
            st.warning('Username/password is incorrect')
            st.session_state["authentication_status"] = None
        elif st.session_state.get('authentication_status') is None:
            st.success('Please enter your username and password')
        if st.session_state.get('authentication_status'):
            st.rerun()

    st.divider()
    st.subheader("""List of features for registered members:""")
    st.write("""
            - name is protected and cannot be used by others (chat, games)
            - automatic name in chat and games""")
    st.divider()
    st.subheader("""List of features for admins:""")
    st.write("""
            - delete chat messages 
            - delete leaderboard entries or reset leaderboard (PixelLogo)
            - read user feedback
            - view and compare submitted logo drawings
            - delete logo drawings from database
            - update full season schedule
            - update team rosters""")

def update_page():
    
    def update_user_in_db():
        current_data = st.session_state["user_data"]["usernames"][st.session_state.get('username')]
        with sql_engine.connect() as conn:
            update_query = text("""UPDATE users
                            SET first_name = :first_name,
                                last_name = :last_name,
                                email = :email,
                                roles = :roles,
                                password = :password
                            WHERE user_name = :username
                        """)
            conn.execute(update_query, {
                "first_name": current_data["first_name"],
                "last_name": current_data["last_name"],
                "email": current_data["email"],
                "roles": current_data["roles"],
                "password": current_data["password"],
                "username": st.session_state.get("username")
            })
            conn.commit()
    
    if st.session_state.get('authentication_status'):
        try:
            if st.session_state["authenticator"].reset_password(st.session_state.get('username')):
                update_user_in_db()
                st.success('Password modified successfully')
        except Exception as e:
            st.error(e)
        try:
            if st.session_state["authenticator"].update_user_details(st.session_state.get('username')):
                update_user_in_db()
                st.success('Entries updated successfully')
        except Exception as e:
            st.error(e)
    else:
        st.warning("Log in first!")

def register_page():
    try:
        def update_user_in_db(username):
            current_data = st.session_state["user_data"]["usernames"][username]
            with sql_engine.connect() as conn:
                update_query = text("""INSERT INTO users (user_name, first_name, last_name, email, password, roles)
                                        VALUES (:user_name, :first_name, :last_name, :email, :password, :roles)
                                    """)
                conn.execute(update_query, {
                    "first_name": current_data["first_name"],
                    "last_name": current_data["last_name"],
                    "email": current_data["email"],
                    "roles": current_data["roles"],
                    "password": current_data["password"],
                    "user_name": username
                })
                conn.commit()
        
        email_of_registered_user, \
        username_of_registered_user, name_of_registered_user = st.session_state["authenticator"].register_user(two_factor_auth=True, password_hint=False, fields={"Password": "Password (will be hashed)"})
        if email_of_registered_user:
            update_user_in_db(username_of_registered_user)
            st.success('User registered successfully')
    except Exception as e:
        st.warning(e)

def forgot_page():
    forgotten = st.segmented_control("Choose the forgotten credential", ["Password", "User name"])
    
    def forgotten_username():
        try:
            username_of_forgotten_username, email_of_forgotten_username = st.session_state["authenticator"].forgot_username(send_email=True, captcha=True)
            if username_of_forgotten_username:
                st.success(f'Username was sent to "{email_of_forgotten_username}"')
            else:
                st.warning(f'Email "{email_of_forgotten_username}" not found')
        except Exception as e:
            st.rerun()
            
    def forgotten_password():
        try:
            username_of_forgotten_password, email_of_forgotten_password, password_of_forgotten_password = st.session_state["authenticator"].forgot_password(send_email=True, captcha=True)
            if username_of_forgotten_password:
                st.success(f'New password was sent to "{email_of_forgotten_password}"')
        except Exception as e:
            st.warning("Username or captcha wrong")
        
    if forgotten == "User name":
        forgotten_username()
    elif forgotten == "Password":
        forgotten_password()

if subpage=="Login":
    login_page()
elif subpage=="Update details":
    update_page()
elif subpage=="Register":
    register_page()
elif subpage=="Forgot credentials":
    forgot_page()
