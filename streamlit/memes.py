import streamlit as st
from streamlit_server_state import server_state, server_state_lock, no_rerun

import time
import requests
from groq import Groq
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from bs4 import BeautifulSoup

from urllib.parse import urlparse

from sources.sql import create_sql_engine, text, query_db
sql_engine = create_sql_engine()

st.title("Memes from nflmemes_ig 'explained' by an AI", anchor=False)
st.subheader("We let an AI 'explain' to us the latest memes from nflmemes_ig. Let's see whether artificial intelligence gets the jokes...", anchor=False)

if not "memes" in server_state:
    with no_rerun:
        with server_state_lock["memes"]:
            server_state["memes"] = [{"src": i['src'], "alt": i['alt'], "ai": i['ai']} for i in query_db(sql_engine, "SELECT * FROM memes;")]

def get_image_caption(image_url, caption):
    client = Groq(api_key=st.secrets['GROQ_TOKEN'])
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"The image shows an NFL related meme. The related caption on instagram was {caption} Please explain the meme."},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )
    return completion.choices[0].message.content

def normalize_url(url):
    parsed = urlparse(url)
    return parsed.path.split('/')[-1]

@st.cache_resource(show_spinner=False)
def get_driver():
    return webdriver.Chrome(
        service=Service(
            ChromeDriverManager(
                chrome_type=ChromeType.CHROMIUM
                ).install()
        ),
        options=options,
    )

try:
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")

    driver = get_driver()

    username = "nflmemes_ig" 
    url = f"https://www.instagram.com/{username}/"

    driver.get(url)

    time.sleep(5)

    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    
    for container in soup.find_all("div", class_="_aagv"):
        img = container.find("img")
        if img and img.get("src"):
            src = img["src"]
            alt = img.get("alt", "")
            #if not normalize_url(src) in [normalize_url(i['src']) for i in server_state["memes"]]:
            if not src in [i['src'] for i in server_state["memes"]]:
                ai = get_image_caption(src, alt)
                with no_rerun:
                    with server_state_lock["memes"]:
                        server_state["memes"].append({"src": src, "alt": alt, "ai": ai})
                with sql_engine.connect() as conn:
                    conn.execute(
                        text("INSERT INTO memes (src, alt, ai) VALUES (:src, :alt, :ai)"),
                        {"src": src, "alt": alt, "ai": ai}
                    )
                    conn.commit()
                    
except Exception as e:
    print(e)
    driver = get_driver()
    driver.quit()

for i in range(min(10, len(server_state['memes']))):
    placeholder = st.empty()
    try:
        img_data = requests.get(server_state['memes'][-i]['src']).content
        cols = st.columns([1,2])
        cols[0].image(img_data, width=300)
        cols[1].text(server_state['memes'][-i]['ai'])
        placeholder.divider()
    except Exception as e:
        placeholder.empty()
