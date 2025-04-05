import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask application
from voice_assistant import app

if __name__ == "__main__":
    # Run the app directly if executed
    app.run()
else:
    # Run via WSGI server (e.g., gunicorn)
    application = app  # for compatibility with some WSGI servers
