import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import requests
import base64

# Function to send concatenated input and location to the API
def send_concatenated_input_to_api(concatenated_input):
    api_url = "https://67db-106-51-78-137.ngrok-free.app/ask/"  # Replace with your API endpoint
    headers = {"Content-Type": "application/json"}
    payload = {"data": concatenated_input}

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()  # Assuming the API returns a JSON response with image and voice URLs
    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}

# Function to send base64-encoded image and location to the API
def send_base64_image_and_location_to_api(image, location):
    api_url = "https://67db-106-51-78-137.ngrok-free.app/ask/"  # Replace with your API endpoint
    image_base64 = base64.b64encode(image).decode('utf-8')
    payload = {
        "image": image_base64,
        "location": f"my current location is {location}"
    }

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()  # Assuming the API returns a JSON response with image and voice URLs
    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}

# Function to display image and play voice received from the API
def display_image_and_voice(image_base64, voice_url):
    image_data = base64.b64decode(image_base64)
    st.image(image_data, use_column_width=True)
    st.audio(voice_url, format="audio/mp3")

# Streamlit interface
st.set_page_config(page_title="Explorer App", page_icon=":globe_with_meridians:", layout="wide")

st.title("Explorer App")
st.markdown("### Enter your input and use the buttons below to submit text or capture an image with location:")

# Input field
user_input = st.text_input("Your Input:", placeholder="Type something...")

# Function to get the user's location
def get_location():
    location = streamlit_geolocation()
    # location = st.experimental_get_query_params().get('location', [None])[0]
    if location:
        return location
    else:
        st.warning("Location access is required. Please allow location access in your browser settings.")
        return None

# Button to submit text
if st.button("Submit Text"):
    if user_input:
        location = get_location()
        if location:
            concatenated_input = f"{user_input} and my current location is {location}"
            result = send_concatenated_input_to_api(concatenated_input)

            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.success("Input successfully sent to the API!")
                st.json(result)  # Display the JSON response from the API
                if 'image_base64' in result and 'voice_url' in result:
                    display_image_and_voice(result['image_base64'], result['voice_url'])
        else:
            st.warning("Location not available. Please enable location access.")
    else:
        st.warning("Please enter some input before submitting.")

# Image upload field
uploaded_image = st.file_uploader("Capture an Image", type=["png", "jpg", "jpeg"])

# Button to capture image and send it with location
if st.button("Capture Image and Send"):
    if uploaded_image:
        location = get_location()
        if location:
            image_bytes = uploaded_image.read()
            result = send_base64_image_and_location_to_api(image_bytes, location)

            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.success("Image and location successfully sent to the API!")
                st.json(result)  # Display the JSON response from the API
                if 'image_base64' in result and 'voice_url' in result:
                    display_image_and_voice(result['image_base64'], result['voice_url'])
        else:
            st.warning("Location not available. Please enable location access.")
    else:
        st.warning("Please capture an image before submitting.")

# Styling with CSS
st.markdown("""
<style>
    .css-18e3th9 {
        padding: 2rem 1rem;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    }
    .css-1d391kg {
        font-size: 1.5rem;
        color: #4CAF50;
    }
    .css-1cpxqw2 {
        padding: 1rem;
        background-color: #f0f0f0;
        border-radius: 5px;
        box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.1);
    }
    .css-1cpxqw2 input {
        font-size: 1.2rem;
    }
    .css-1d391kg .stButton button {
        background-color: #4CAF50;
        color: white;
        font-size: 1.2rem;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .css-1d391kg .stButton button:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)
