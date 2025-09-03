import streamlit as st
import streamlit_nested_layout as stnl

st.title("Overview of Streamlit functionalities", anchor=False)

with st.expander("General Streamlit functionalities"):
    
    with st.expander("Basic text: `st.write()` and `st.markdown()`"):
        st.write("Those are used to do ...")
        st.markdown("""##### Streamlit documentation:
- [st.write()](https://docs.streamlit.io/develop/api-reference/write-magic/st.write)
- [st.markdown()](https://docs.streamlit.io/develop/api-reference/text/st.markdown)""")
        
    with st.expander("Headings: `st.title()`, `st.header()`, and `st.subheader`"):
        st.write("...")
        
    with st.expander("Formatized text: `st.code()` and `st.html()`"):
        st.write("...")
        
    with st.expander("Tabular data: `st.dataframe()` and `st.table()`"):
        st.write("...")
        
    with st.expander("Plotting: `st.pyplot()` and `st.pydeck_chart()`"):
        st.write("...")
        
    with st.expander("input widgets (buttons): `st.button()`, `st.download_button()`, `st.form_submit_button()`"):
        st.write("...")
        
    with st.expander("input widgets (selections): `st.checkbox()`, `st.color_picker()`, `st.feedback()`, `st.multiselect()`, `st.radio()`, `st.segmented_control()`, `st.selectbox()`, `st.select_slider()`, `st.toggle()`"):
        st.write("...")
        
    with st.expander("input widgets (numeric): `st.number_input()` and `st.slider()`"):
        st.write("...")
        
    with st.expander("input widgets (others): `st.chat_input()`, `st.text_area()`, `st.text_input()`, and `st.file_uploader()`"):
        st.write("...")
        
    with st.expander("Media elements: `st.audio()`, `st.image()`, `st.logo()`, `st.pdf()`, `st.video()`"):
        st.write("...")
        
    with st.expander("Layouts and containers: `st.columns()`, `st.container()`, `st.dialog()`, `st.expander()`, `st.form()`, `st.sidebar()`"):
        st.write("...")
        
    with st.expander("Status elements: `st.success()`, `st.info()`, `st.warning()`, `st.error()`, `st.progress()`, `st.spinner()`"):
        st.write("...")
        
    with st.expander("Navigation: `st.navigation()`, `st.Page()`, `st.page_link()`"):
        st.write("...")
        
    with st.expander("Execution flow: `st.fragment()`, `st.rerun()`, `st.stop()`"):
        st.write("...")
        
    with st.expander("Caching and state: `st.cache_data()`, `st.cache_resource()`, `st.session_state()`, `st.query_params()`"):
        st.write("...")