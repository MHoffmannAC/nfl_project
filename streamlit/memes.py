import streamlit as st
import instaloader
from groq import Groq
import requests

def fetch_latest_images(username, X=5):
    L = instaloader.Instaloader()
    profile = instaloader.Profile.from_username(L.context, username)
    latest_images = []
    for post in profile.get_posts():
        if len(latest_images) < X:
            latest_images.append({
                'image_url': post.url,          # Direct image URL
                'caption': post.caption         # Caption of the post
            })
        else:
            break
    return latest_images

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

st.title("Memes from nflmemes_ig 'explained' by an AI")
st.subheader("We let an AI 'explain' to us the latest memes from nflmemes_ig. Let's see whether artificial intelligence gets the jokes...")

latest_images = []
#latest_images = fetch_latest_images('nflmemes_ig', X=10)


for post in latest_images:
    image_url = post['image_url']
    caption = post['caption']
    cols = st.columns(2)

    with cols[0]:
        response = requests.get(image_url)
        if response.status_code == 200:
            st.image(response.content, width=300)  # Pass the raw image content
        else:
            st.error("Failed to load image")
        st.text(caption)
    with cols[1]:
        caption = get_image_caption(image_url, caption)
        st.write(caption)
    st.divider()



from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import requests
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from streamlit_server_state import server_state, server_state_lock, no_rerun

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920x1080")

service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
driver = webdriver.Chrome(service=service, options=options)

username = "nflmemes_ig" 
url = f"https://www.instagram.com/{username}/"
driver.get(url)

time.sleep(5)

for _ in range(3):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

if not "memes" in server_state:
    with no_rerun:
        with server_state_lock["memes"]:
            server_state["memes"] = []

for container in soup.find_all("div", class_="_aagv"):
    img = container.find("img")
    if img and img.get("src"):
        src = img["src"]
        alt = img.get("alt", "")
        if not src in [i['src'] for i in server_state_lock["memes"]]:
            with no_rerun:
                with server_state_lock["memes"]:
                    server_state["memes"].append({"src": src, "alt": alt, "ai": ""})

#with no_rerun:
#    with server_state_lock["memes"]:    
#        server_state["memes"] = server_state["memes"][:10]


for i in server_state['memes'][-10:]:
    print(i)
    print(i.get('ai', ""))
    if i.get('ai', "") == "":
        i['ai'] = get_image_caption(i['src'], i['alt'])

    st.divider()        
    cols = st.columns([1,2])
    img_data = requests.get(i['src']).content
    cols[0].image(img_data, width=300)
    cols[1].text(i['ai'])
