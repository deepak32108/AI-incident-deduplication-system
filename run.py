from flask import send_from_directory
from src.api.routes import app
import os

# Intercept the root path to serve your frontend dashboard file
@app.route('/')
def index():
    # Serves dashboard.html directly from your project root folder
    return send_from_directory(os.getcwd(), 'dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)