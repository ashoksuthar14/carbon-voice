from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import io
import base64

app = Flask(__name__)

# Load environment variables and configure Gemini
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)

# Set up the model with safety settings
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    safety_settings=safety_settings
)

chat = model.start_chat(history=[])

# Initialize speech recognizer
recognizer = sr.Recognizer()

def get_gemini_response(prompt, context):
    base_prompt = """You are a friendly and enthusiastic environmentalist having a conversation about sustainability.
    Current user input: {user_input}
    
    If this is a new activity being discussed:
    1. Ask 1-2 specific follow-up questions to better understand their current habits and situation
    2. Show genuine interest in their response
    3. Keep the tone warm and encouraging
    
    If you have enough context about their activity:
    1. Acknowledge their current approach
    2. Suggest 1-2 specific eco-friendly alternatives
    3. Include an approximate carbon footprint reduction estimate
    4. End with an encouraging note
    
    Remember to:
    - Keep responses conversational and friendly
    - Use casual language with occasional emojis
    - Show enthusiasm for sustainable choices
    - Be specific with suggestions and numbers
    - Ask only one question at a time
    
    Respond in a natural, chatty way:"""
    
    try:
        full_prompt = base_prompt.format(user_input=prompt)
        response = chat.send_message(full_prompt)
        return response.text
    except Exception as e:
        return f"Sorry, there was an error: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    try:
        # Convert the audio file to text
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            
        # Get AI response
        context = {"understanding_phase": True}
        ai_response = get_gemini_response(text, context)
        
        return jsonify({
            'user_text': text,
            'ai_response': ai_response
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    context = {"understanding_phase": True}
    ai_response = get_gemini_response(user_message, context)
    
    return jsonify({
        'response': ai_response
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
