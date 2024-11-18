import streamlit as st

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# Streamlit App with Navigation
def main():
    st.set_page_config(layout="wide")
    local_css("style.css")
    st.logo("images/sidebar.png", size='large')
    page = st.navigation([st.Page("my_pages/start.py", title="Home Page", default=True), st.Page("my_pages/chatbot.py", title="NFLBot")])
    #st.image("images/header.png", use_container_width=True)

    page.run()

if __name__ == "__main__":
    main()
 