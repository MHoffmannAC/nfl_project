import streamlit as st
import instaloader
from groq import Groq
import requests

st.error("Currently the instaloader has a bug...")

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
    print(caption)
    client = Groq(api_key=st.secrets['GROQ_TOKEN'])
    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",  # Use the model with vision capabilities
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
    
    # Extract the generated message
    return completion.choices[0].message.content

st.title("Memes from nflmemes_ig 'explained' by an AI")

# Example usage
username = 'nflmemes_ig'  # Replace with actual Instagram username
latest_images = fetch_latest_images(username, X=10)

# Generate captions for each image using Groq
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
