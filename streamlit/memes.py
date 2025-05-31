import streamlit as st
from streamlit_server_state import server_state, server_state_lock, no_rerun

import time
import requests
from groq import Groq

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from bs4 import BeautifulSoup

st.title("Memes from nflmemes_ig 'explained' by an AI")
st.subheader("We let an AI 'explain' to us the latest memes from nflmemes_ig. Let's see whether artificial intelligence gets the jokes...")

if not "memes" in server_state:
    with no_rerun:
        with server_state_lock["memes"]:
            server_state["memes"] = []

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
            if not src in [i['src'] for i in server_state["memes"]]:
                with no_rerun:
                    with server_state_lock["memes"]:
                        server_state["memes"].append({"src": src, "alt": alt, "ai": ""})
except Exception as e:
    driver = get_driver()
    driver.quit()
    print(e)

for i in range(10):
    if server_state['memes'][-i].get('ai', "") == "":
        server_state['memes'][-i]['ai'] = get_image_caption(server_state['memes'][-i]['src'], server_state['memes'][-i]['alt'])
    st.divider()        
    cols = st.columns([1,2])
    img_data = requests.get(server_state['memes'][-i]['src']).content
    cols[0].image(img_data, width=300)
    cols[1].text(server_state['memes'][-i]['ai'])
    
