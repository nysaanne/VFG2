import requests
import pandas as pd
import streamlit as st
import google.generativeai as genai
import json

def get_weather(api_key, location='Saint Lucia, LC'):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=imperial'
    response = requests.get(url)
    return response.json()

def suggest_action(weather_data):
    weather = weather_data['weather'][0]['main']
    suggestions = {
        'Thunderstorm': 'Cozy up indoors with a good book and avoid using electrical appliances.',
        'Drizzle': 'Grab your favorite umbrella and take extra care on the road.',
        'Rain': 'If its pouring, stay dry inside or head to a safe place nearby.',
        'Clear': 'Enjoy the sunshine! Don’t forget your sunscreen if you’re heading out.',
        'Clouds': 'Perfect weather to relax indoors or take a leisurely walk.',
        'Tropical Storm': 'Stay safe by finding a secure shelter quickly and stay connected for updates.',
        'Hurricane': 'Make safety a priority—head to an emergency shelter as soon as possible.'
    }
    return suggestions.get(weather, 'Be prepared for any weather conditions.')

@st.cache_data
def load_data(file_name):
    return pd.read_csv(f'{file_name}.csv')

API_KEY_WEATHER = '52d8d3fbd86148499b0273f6bc7a6bb4'
API_KEY_GEMINI = "AIzaSyDguVIkytn21HBhcQoQJis_e7JcuAPQMko"

genai.configure(api_key=API_KEY_GEMINI)

model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat()

def initializeAI():
    initialPrompt = """
    Your role is to be a chatbot responding to the messages from a user.
    Your response should be a string in json format with two keys. A response
    key and a quit key. The value to the response key should be the response to
    the user's prompt and the value for the quit key should be the response if
    the user want to end the conversation. Here is an example of how I want your
    response to be to the prompt 'What is good morning in spanish?'. 
    {'response': 'Good morning in spanish is buenos dias', 'quit': false}
    """
    chat.send_message(initialPrompt)

initializeAI()

def get_gemini_response(message):
    try:
        response = chat.send_message(message)
        reply = response.text
        map = json.loads(reply[8:len(response.text)-4])
        return map['response'], map['quit']
    except Exception as e:
        st.error(f"Error with Gemini API: {str(e)}")
        return "I'm sorry, I couldn't process that request. Please try again.", False

def main():
    
    st.set_page_config(page_title="Weather Wizard 🌦️", page_icon="🌦️")

     # Custom CSS to increase font size of input boxes, dataframes, and general text
    st.markdown("""
    <style>
    .stTextInput > div > div > input {
        font-size: 20px;
    }
    .dataframe {
        font-size: 40px !important;
    }
    .dataframe th {
        font-size: 40px !important;
    }
    .dataframe td {
        font-size: 40px !important;
    }
    .large-font {
        font-size: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Weather Wizard 🌦️")

    with st.chat_message(name="assistant", avatar="🌦️"):
        st.markdown('<p class="large-font">Hello! Welcome to the Weather Wizard!</p>', unsafe_allow_html=True)
        st.markdown('<p class="large-font">Get live weather updates and chat with Weather AI for more weather information. Stay updated on weather conditions and be informed about hospitals, shelters and other necessary information needed prior, mid and post disaster</p>', unsafe_allow_html=True)

    # Initialize session state
    if 'location' not in st.session_state:
        st.session_state.location = "Saint Lucia, LC"
    if 'user_message' not in st.session_state:
        st.session_state.user_message = ""

    location = st.text_input("Enter Location", value=st.session_state.location, key="location_input")
    if st.button("Fetch Weather"):
        weather_data = get_weather(API_KEY_WEATHER, location)

        if weather_data.get('cod') != 200:
            st.error(f"Error fetching weather data: {weather_data.get('message')}")
            return

        weather_condition = weather_data['weather'][0]['main']
        temperature = weather_data['main']['temp']
        suggestion = suggest_action(weather_data)

        st.markdown(f'<p class="large-font">Weather in {location}: {weather_condition}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="large-font">Temperature: {temperature}°F</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="large-font">Suggestion: {suggestion}</p>', unsafe_allow_html=True)

        if weather_condition in ['Tropical Storm', 'Hurricane']:
            shelters = load_data('emergency_shelters')
            st.markdown('### Emergency Shelters', unsafe_allow_html=True)
            st.dataframe(shelters[['Shelter Name', 'Address', 'Contact']],hide_index=True)

    st.markdown('## Chat with Weather Wizard', unsafe_allow_html=True)
    user_message = st.text_input("You:", value=st.session_state.user_message, key="user_message_input")
    if st.button("Send", key="send_button"):
        if user_message:
            # Convert user message to lowercase for case-insensitive matching
            user_message_lower = user_message.lower()

            # Check for specific keywords and display corresponding dataframes
            if any(keyword in user_message_lower for keyword in ['hospital', 'health centre', 'hospitals', 'health centres']):
                hospitals = load_data('hospitals')
                st.markdown('### Hospitals', unsafe_allow_html=True)
                st.dataframe(hospitals, hide_index=True)
            elif any(keyword in user_message_lower for keyword in ['rebuild', 'nemo', 'news', 'hurricane centre', 'hurricane essentials']):
                hurricane_essentials = load_data('hurricane_essentials')
                st.markdown('### Hurricane Essentials', unsafe_allow_html=True)
                st.dataframe(hurricane_essentials, hide_index=True)
            elif any(keyword in user_message_lower for keyword in ['emergency', 'shelter', 'shelters']):
                shelters = load_data('emergency_shelters')
                st.markdown('### Emergency Shelters', unsafe_allow_html=True)
                st.dataframe(shelters[['Shelter Name', 'Address']], hide_index=True)
            else:
                # If no specific keywords are detected, use the Gemini API
                ai_response, quit = get_gemini_response(user_message)
                st.markdown(f'<p class="large-font"><strong>Assistant:</strong> {ai_response}</p>', unsafe_allow_html=True)

                if quit:
                    st.markdown('<p class="large-font">Exiting the chat. Goodbye!</p>', unsafe_allow_html=True)

    if st.button("Reset"):
        st.session_state.location = "Saint Lucia, LC"
        st.session_state.user_message = ""
        st.rerun()

if __name__ == '__main__':
    main()
