from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
from flask_cors import CORS
import os
import logging
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API using environment variable
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

try:
    genai.configure(api_key=api_key)
    logger.info("Successfully configured Gemini API")
except Exception as e:
    logger.error(f"Error configuring Gemini API: {str(e)}")
    raise

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

# Create a generative model and chat session
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    safety_settings=safety_settings
)

# Initialize chat session manager
class ChatSessionManager:
    def __init__(self, model):
        self.model = model
        self.chat = None
        self.initialize_chat()

    def initialize_chat(self):
        try:
            self.chat = self.model.start_chat(history=[])
            initial_prompt = """You are a friendly and enthusiastic environmentalist having conversations about sustainability. Your goal is to help people reduce their carbon footprint through engaging dialogue and practical suggestions.

Your conversation style should be:
1. Warm, encouraging, and positive
2. Use casual language with occasional emojis
3. Show genuine interest in people's activities
4. Be specific with suggestions and numbers
5. Make the environmental impact feel personal and achievable

Your response pattern should be:
1. For new topics: Ask specific questions to understand their current habits
2. Show interest in their answers and ask relevant follow-ups
3. Once you have enough context: 
   - Acknowledge their current approach
   - Suggest practical eco-friendly alternatives
   - Include specific carbon footprint reduction estimates
   - End with encouragement and an open question

Start by introducing yourself warmly and asking what activity they'd like to discuss."""
            
            # Initialize the chat with the prompt
            response = self.chat.send_message(initial_prompt)
            
            logger.info("Chat session initialized successfully")
            
            return "Hi! I'm your friendly environmental guide! 😊 I'm passionate about helping people live more sustainably. What activity would you like to discuss today?"
        
        except Exception as e:
            
            logger.error(f"Error initializing chat: {str(e)}")
            
            raise

    
    
    def get_response(self, user_input):
        
        try:
            
            if not self.chat:
                
                self.initialize_chat()
            
            response = self.chat.send_message(user_input)
            
            return response.text
        
        except Exception as e:
            
            logger.error(f"Error getting response: {str(e)}")
            
            self.initialize_chat()  # Try to recover by reinitializing
            
            raise


# Create chat session manager
chat_manager = ChatSessionManager(model)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    try:
        # Initialize chat session when homepage is loaded
        initial_message = chat_manager.initialize_chat()
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error initializing chat on homepage load: {str(e)}")
        return render_template('index.html')

@app.route('/process_command', methods=['POST'])
def process_command():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({'error': 'No data received'}), 400

        command = data.get('command')
        if not command:
            logger.error("No command in request data")
            return jsonify({'error': 'No command received'}), 400

        logger.info(f"Processing command: {command}")

        try:
            # Get response from chat manager
            response_text = chat_manager.get_response(command)
            logger.info(f"Generated response: {response_text}")
            return jsonify({
                'success': True,
                'response': response_text
            })

        except Exception as e:
            logger.error(f"Error getting response from chat manager: {str(e)}")
            # Try to reinitialize chat and provide a friendly error message
            chat_manager.initialize_chat()
            return jsonify({
                'error': 'Chat error',
                'response': 'I had a small hiccup in our conversation. 😅 Let\'s start fresh - what environmental topic would you like to discuss?'
            }), 500

    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'response': 'I\'m having trouble understanding right now. Could you please try again? 🤔'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
