import streamlit as st
import streamlit_nested_layout as stnl

st.title("Overview of Streamlit functionalities", anchor=False)

with st.expander("General Streamlit functionalities", expanded=True):
    
    with st.expander("Basic text: `st.write()` and `st.markdown()`"):
        st.markdown("""
        **What they do in general:**
        - `st.write()` is the most flexible way to display text, numbers, DataFrames, or even plots.  
        - `st.markdown()` renders Markdown-formatted text (headings, bold, italics, links, lists).  

        **How they are used in this app:**
        - Used throughout the app to display explanatory text and formatted content.  

        **Where they are used:**
        - Almost everywhere throughout the app.  

        ##### Streamlit documentation:
        - [st.write()](https://docs.streamlit.io/develop/api-reference/write-magic/st.write)  
        - [st.markdown()](https://docs.streamlit.io/develop/api-reference/text/st.markdown)
        """, unsafe_allow_html=True)

    with st.expander("Headings: `st.title()`, `st.header()`, and `st.subheader()`"):
        st.markdown("""
        **What they do in general:**
        - Provide structured headings to organize your app visually.  

        **How they are used in this app:**
        - Define the main app title (`st.title`) and section titles (`st.header`, `st.subheader`).  

        **Where they are used:**
        - On nearly all app pages.  

        ##### Streamlit documentation:
        - [st.title()](https://docs.streamlit.io/develop/api-reference/text/st.title)  
        - [st.header()](https://docs.streamlit.io/develop/api-reference/text/st.header)  
        - [st.subheader()](https://docs.streamlit.io/develop/api-reference/text/st.subheader)
        """, unsafe_allow_html=True)

    with st.expander("Formatted text: `st.code()` and `st.html()`"):
        st.markdown("""
        **What they do in general:**
        - `st.code()` displays syntax-highlighted code blocks.  
        - `st.html()` can render raw HTML (experimental).  

        **How they are used in this app:**
        - Used to illustrate SQL or Python snippets.  

        **Where they are used:**
        - In the <a href='data' target='_self'>Data Aquisition page</a>, for example, to show how SQL queries are used. The <a href='details' target='_self'>Teams page</a> also uses `st.html` to inject custom styling.  

        ##### Streamlit documentation:
        - [st.code()](https://docs.streamlit.io/develop/api-reference/text/st.code)  
        - [st.html()](https://docs.streamlit.io/develop/api-reference/text/st.html)
        """, unsafe_allow_html=True)

    with st.expander("Tabular data: `st.dataframe()` and `st.table()`"):
        st.markdown("""
        **What they do in general:**
        - `st.dataframe()` displays interactive, scrollable DataFrames.  
        - `st.table()` shows static tables.  

        **How they are used in this app:**
        - Displaying NFL team stats, player data, and standings.  

        **Where they are used:**
        - For example on the <a href='standings' target='_self'>Standings page</a> to display conference and division standings.  

        ##### Streamlit documentation:
        - [st.dataframe()](https://docs.streamlit.io/develop/api-reference/data/st.dataframe)  
        - [st.table()](https://docs.streamlit.io/develop/api-reference/data/st.table)
        """, unsafe_allow_html=True)

    with st.expander("Plotting: `st.pyplot()` and `st.pydeck_chart()`"):
        st.markdown("""
        **What they do in general:**
        - `st.pyplot()` renders Matplotlib figures.  
        - `st.pydeck_chart()` renders geospatial data with Deck.gl.  

        **How they are used in this app:**
        - `st.pyplot()` is used to show charts like win percentages or point distributions.
        - `st.pydeck_chart()` is used to display team locations on a map.  

        **Where they are used:**
        - On the <a href='schedule' target='_self'>Schedule</a> and <a href='prediction' target='_self'>PlayPredictor</a> as well as on the <a href='details' target='_self'>Teams</a> pages.  

        ##### Streamlit documentation:
        - [st.pyplot()](https://docs.streamlit.io/develop/api-reference/charts/st.pyplot)  
        - [st.pydeck_chart()](https://docs.streamlit.io/develop/api-reference/charts/st.pydeck_chart)
        """, unsafe_allow_html=True)

    with st.expander("Input widgets (buttons): `st.button()`, `st.download_button()`, `st.form_submit_button()`"):
        st.markdown("""
        **What they do in general:**
        - Provide interactive buttons for triggering actions or downloads.  

        **How they are used in this app:**
        - Buttons are used to refresh standings, confirm choices, or download data exports.  

        **Where they are used:**
        - For example on the <a href='details' target='_self'>Teams page</a> and at the <a href='news' target='_self'>News Summarizer</a> for updating data.  

        ##### Streamlit documentation:
        - [st.button()](https://docs.streamlit.io/develop/api-reference/widgets/st.button)  
        - [st.download_button()](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button)  
        - [st.form_submit_button()](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form_submit_button)
        """, unsafe_allow_html=True)

    with st.expander("Input widgets (selections): `st.checkbox()`, `st.color_picker()`, `st.feedback()`, `st.multiselect()`, `st.radio()`, `st.segmented_control()`, `st.selectbox()`, `st.select_slider()`, `st.toggle()`"):
        st.markdown("""
        **What they do in general:**
        - Provide UI elements for user selections.  

        **How they are used in this app:**
        - For filtering standings, choosing teams, and interactive user inputs.  

        **Where they are used:**
        - For example the <a href='news' target='_self'>News Summarizer</a> uses a `st.segmented_control` and the <a href='schedule' target='_self'>Schedule page</a> uses a `selectbox` while the <a href='drawing' target='_self'>LogoRecognizer</a> utilizes `st.color_picker` elements to select drawing colors.

        ##### Streamlit documentation:
        - [st.checkbox()](https://docs.streamlit.io/develop/api-reference/widgets/st.checkbox)  
        - [st.color_picker()](https://docs.streamlit.io/develop/api-reference/widgets/st.color_picker)  
        - [st.feedback()](https://docs.streamlit.io/develop/api-reference/widgets/st.feedback)  
        - [st.multiselect()](https://docs.streamlit.io/develop/api-reference/widgets/st.multiselect)  
        - [st.radio()](https://docs.streamlit.io/develop/api-reference/widgets/st.radio)  
        - [st.segmented_control()](https://docs.streamlit.io/develop/api-reference/widgets/st.segmented_control)  
        - [st.selectbox()](https://docs.streamlit.io/develop/api-reference/widgets/st.selectbox)  
        - [st.select_slider()](https://docs.streamlit.io/develop/api-reference/widgets/st.select_slider)  
        - [st.toggle()](https://docs.streamlit.io/develop/api-reference/widgets/st.toggle)
        """, unsafe_allow_html=True)

    with st.expander("Input widgets (numeric): `st.number_input()` and `st.slider()`"):
        st.markdown("""
        **What they do in general:**
        - Numeric input fields and sliders for number ranges.  

        **How they are used in this app:**
        - Used for setting thresholds like minimum games played or score ranges.  

        **Where they are used:**
        - Mainly used for the <a href='prediction' target='_self'>PlayPredictor</a> inputs.  

        ##### Streamlit documentation:
        - [st.number_input()](https://docs.streamlit.io/develop/api-reference/widgets/st.number_input)  
        - [st.slider()](https://docs.streamlit.io/develop/api-reference/widgets/st.slider)
        """, unsafe_allow_html=True)

    with st.expander("Input widgets (others): `st.chat_input()`, `st.text_area()`, `st.text_input()`, and `st.file_uploader()`"):
        st.markdown("""
        **What they do in general:**
        - Input fields for free text, file uploads, and chat-style interaction.  

        **How they are used in this app:**
        - File uploads are used for uploading drawings for the LogoRecognizer, text inputs for chats, feedbacks and more.  

        **Where they are used:**
        - The <a href='chat' target='_self'>Chat page</a> and <a href='chatbot' target='_self'>ChatBot</a> for chat input, and the <a href='drawing' target='_self'>LogoRecognizer</a> for drawing uploads.  

        ##### Streamlit documentation:
        - [st.chat_input()](https://docs.streamlit.io/develop/api-reference/chat/st.chat_input)  
        - [st.text_area()](https://docs.streamlit.io/develop/api-reference/widgets/st.text_area)  
        - [st.text_input()](https://docs.streamlit.io/develop/api-reference/widgets/st.text_input)  
        - [st.file_uploader()](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
        """, unsafe_allow_html=True)

    with st.expander("Media elements: `st.audio()`, `st.image()`, `st.logo()`, `st.video()`"):
        st.markdown("""
        **What they do in general:**
        - Display or play various media types.  

        **How they are used in this app:**
        - Main sources of media.  

        **Where they are used:**
        - Almost everywhere. For example the <a href='details' target='_self'>Teams page</a> displays team logos as well as player pictures while the <a href='news' target='_self'>News Podcast page</a> uses `st.audio` for playing the podcast.

        ##### Streamlit documentation:
        - [st.audio()](https://docs.streamlit.io/develop/api-reference/media/st.audio)  
        - [st.image()](https://docs.streamlit.io/develop/api-reference/media/st.image)  
        - [st.logo()](https://docs.streamlit.io/develop/api-reference/media/st.logo)  
        - [st.video()](https://docs.streamlit.io/develop/api-reference/media/st.video)
        """, unsafe_allow_html=True)

    with st.expander("Layouts and containers: `st.columns()`, `st.container()`, `st.dialog()`, `st.expander()`, `st.form()`, `st.sidebar()`"):
        st.markdown("""
        **What they do in general:**
        - Provide structure for organizing the app layout.  

        **How they are used in this app:**
        - Columns for side-by-side arrangements, sidebar for navigation, others for styling.  

        **Where they are used:**
        - Across all pages, e.g., the <a href='prediction' target='_self'>PlayPredictor page</a> and the <a href='details' target='_self'>Teams page</a>.  

        ##### Streamlit documentation:
        - [st.columns()](https://docs.streamlit.io/develop/api-reference/layout/st.columns)  
        - [st.container()](https://docs.streamlit.io/develop/api-reference/layout/st.container)  
        - [st.dialog()](https://docs.streamlit.io/develop/api-reference/execution-flow/st.dialog)  
        - [st.expander()](https://docs.streamlit.io/develop/api-reference/layout/st.expander)  
        - [st.form()](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form)  
        - [st.sidebar()](https://docs.streamlit.io/develop/api-reference/layout/st.sidebar)
        """, unsafe_allow_html=True)

    with st.expander("Status elements: `st.success()`, `st.info()`, `st.warning()`, `st.error()`, `st.progress()`, `st.spinner()`"):
        st.markdown("""
        **What they do in general:**
        - Visual feedback messages, progress bars, and spinners.  

        **How they are used in this app:**
        - Used to confirm successful SQL uploads, loading data, or warning about missing values.  

        **Where they are used:**
        - For example the <a href='drawing' target='_self'>LogoRecognizer</a> utilizes status messages for its predictions while the <a href='chatbot' target='_self'>ChatBot</a> uses spinners when loading data.  

        ##### Streamlit documentation:
        - [st.success()](https://docs.streamlit.io/develop/api-reference/status/st.success)  
        - [st.info()](https://docs.streamlit.io/develop/api-reference/status/st.info)  
        - [st.warning()](https://docs.streamlit.io/develop/api-reference/status/st.warning)  
        - [st.error()](https://docs.streamlit.io/develop/api-reference/status/st.error)  
        - [st.progress()](https://docs.streamlit.io/develop/api-reference/status/st.progress)  
        - [st.spinner()](https://docs.streamlit.io/develop/api-reference/status/st.spinner)
        """, unsafe_allow_html=True)

    with st.expander("Navigation: `st.navigation()`, `st.Page()`, `st.page_link()`"):
        st.markdown("""
        **What they do in general:**
        - Handle multi-page navigation in Streamlit apps.  

        **How they are used in this app:**
        - Define the structure of pages and enable linking between them.  

        **Where they are used:**
        - The <a href='/' target='_self'>Home page</a> is the main entry point for navigation.  

        ##### Streamlit documentation:
        - [st.navigation()](https://docs.streamlit.io/develop/api-reference/navigation/st.navigation)  
        - [st.Page()](https://docs.streamlit.io/develop/api-reference/navigation/st.Page)  
        - [st.page_link()](https://docs.streamlit.io/develop/api-reference/widgets/st.page_link)
        """, unsafe_allow_html=True)

    with st.expander("Execution flow: `st.fragment()`, `st.rerun()`, `st.stop()`"):
        st.markdown("""
        **What they do in general:**
        - Control the execution of Streamlit scripts.  

        **How they are used in this app:**
        - `st.rerun()` is used after data refresh; `st.stop()` for early exits.  

        **Where they are used:**
        - The <a href='news' target='_self'>News Summarizer</a> and <a href='prediction' target='_self'>PlayPredictor</a> pages both use `st.rerun()` to update the page after a user action.
        - Tic TacToe in the <a href='games' target='_self'>Games page</a> uses `st.fragment()` to reload only parts of the app regularly. 

        ##### Streamlit documentation:
        - [st.fragment()](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment)  
        - [st.rerun()](https://docs.streamlit.io/develop/api-reference/execution-flow/st.rerun)  
        - [st.stop()](https://docs.streamlit.io/develop/api-reference/execution-flow/st.stop)
        """, unsafe_allow_html=True)

    with st.expander("Caching and state: `st.cache_data()`, `st.cache_resource()`, `st.session_state()`, `st.query_params()`"):
        st.markdown("""
        **What they do in general:**
        - Provide caching for expensive computations and state management across reruns.  

        **How they are used in this app:**
        - Used to cache SQL queries and manage session-wide selections (like chosen team).  

        **Where they are used:**
        - `st.session_state` is used almost everywhere.  

        ##### Streamlit documentation:
        - [st.cache_data()](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data)  
        - [st.cache_resource()](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource)  
        - [st.session_state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)  
        - [st.query_params()](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.query_params)
        """, unsafe_allow_html=True)

with st.expander("External Streamlit-related Libraries:", expanded=True):

    with st.expander("streamlit_server_state"):
        st.markdown("""
        **What it does in general:**
        - Manages a **global state** that is shared across all user sessions connected to the Streamlit server. This is in contrast to `st.session_state`, which is unique for each user. It's essential for building multi-user, collaborative apps.

        **How it's used in this app:**
        - Used to allow communication between different clients to allow real-time chatting as well as gaming.
        
        **Where it's used:**
        - The <a href='chat' target='_self'>Chat</a> uses it to store chat messages and multiple <a href='games' target='_self'>Games</a> utilize it to allow for real-time competitions.

        ##### Documentation:
        - [streamlit-server-state](https://github.com/whitphx/streamlit-server-state)
        """, unsafe_allow_html=True)

    with st.expander("streamlit_antd_components"):
        st.markdown("""
        **What it does in general:**
        - Provides a set of high-quality UI components from the Ant Design library, offering a more polished and professional look than the default Streamlit widgets.

        **How it's used in this app:**
        - The app uses it to display the `tree` widget, which is used for selecting the chat room in a visually appealing way.

        **Where it's used:**
        - <a href='chat' target='_self'>Chat</a>

        ##### Documentation:
        - [streamlit-antd-components](https://github.com/nicedouble/StreamlitAntdComponents)
        """, unsafe_allow_html=True)
        
    with st.expander("streamlit_autorefresh"):
        st.markdown("""
        **What it does in general:**
        - A lightweight utility that automatically reloads the Streamlit app at a specified interval.

        **How it's used in this app:**
        - Used in the chat functionality to automatically refresh the page. This ensures new messages from other users appear immediately without requiring manual interaction.

        **Where it's used:**
        - <a href='chat' target='_self'>Chat</a>

        ##### Documentation:
        - [streamlit-autorefresh](https://github.com/kmcgrady/streamlit-autorefresh)
        """, unsafe_allow_html=True)
        
        st.warning("Note: might be replaced by `st.fragment()` in the future, which is part of Streamlit itself.", icon="⚠️")
        
    with st.expander("streamlit_drawable_canvas"):
        st.markdown("""
        **What it does in general:**
        - Adds an interactive canvas component to a Streamlit app. Users can draw on the canvas, and the drawing data can be returned to the app as an image or a list of strokes.

        **How it's used in this app:**
        - It's the core component of the <a href='drawing' target='_self'>LogoRecognizer</a> page, where users can draw a team's logo for the AI model to analyze.

        **Where it's used:**
        - <a href='drawing' target='_self'>LogoRecognizer</a>

        ##### Documentation:
        - [streamlit-drawable-canvas](https://github.com/andfanilo/streamlit-drawable-canvas)
        """, unsafe_allow_html=True)
        
    with st.expander("streamlit_image_comparison"):
        st.markdown("""
        **What it does in general:**
        - A visual tool for comparing two images side by side using a movable slider. It's useful for demonstrating changes or differences between images.

        **How it's used in this app:**
        - The <a href='drawing' target='_self'>LogoRecognizer</a> page uses this component to let admins compare the drawn logo with the actual NFL team logo.

        **Where it's used:**
        - <a href='drawing' target='_self'>LogoRecognizer</a>

        ##### Documentation:
        - [streamlit-image-comparison](https://github.com/fcakyon/streamlit-image-comparison)
        """, unsafe_allow_html=True)
        
        st.warning("Note: Only visible for admins currently", icon="⚠️")

        
    with st.expander("streamlit_authenticator"):
        st.markdown("""
        **What it does in general:**
        - A secure and customizable authentication solution for Streamlit apps. It provides functions for user login, registration, password resets, and managing user roles.

        **How it's used in this app:**
        - This library is used on the <a href='login' target='_self'>User Login</a> page to handle user authentication and manage different user roles (like 'admin').

        **Where it's used:**
        - <a href='login' target='_self'>User Login</a>

        ##### Documentation:
        - [streamlit-authenticator](https://github.com/mkhorasani/Streamlit-Authenticator)
        """, unsafe_allow_html=True)
        
    with st.expander("streamlit_nested_layout"):
        st.markdown("""
        **What it does in general:**
        - Extends Streamlit's layout capabilities by enabling the nesting of columns and other layout components, allowing for more complex and custom designs.

        **How it's used in this app:**
        - Used on this very page (<a href='streamlit' target='_self'>Streamlit functionalities</a>) as well as on the <a href='models' target='_self'>Model Overview</a> to create the structured hierarchy of expandable sections and sub-expanders.

        **Where it's used:**
        - <a href='streamlit' target='_self'>Streamlit functionalities</a>
        - <a href='models' target='_self'>ML/AI models</a>

        ##### Documentation:
        - [streamlit-nested-layout](https://github.com/joy13975/streamlit-nested-layout)
        """, unsafe_allow_html=True)
        
    with st.expander("streamlit_extras"):
        st.markdown("""
        **What it does in general:**
        - A collection of small, useful functionalities that are not built into Streamlit. These "extras" help developers add flair, interactivity, and custom features to their apps without writing a lot of custom code.

        **How it's used in this app:**
        - Currently just used for visual feedback after a game of <a href='games' target='_self'>Tic Tac Toe</a>.

        **Where it's used:**
        - <a href='games' target='_self'>Tic Tac Toe</a>
        
        ##### Documentation:
        - [streamlit-extras](https://arnaudmiribel.github.io/streamlit-extras/)
        """, unsafe_allow_html=True)
