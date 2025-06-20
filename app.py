import os
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
from utils.routes import astrology_bp
from flask_session import Session
# Load env vars
load_dotenv()


app = Flask(__name__)
# CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'      # ✅ required
app.config['SESSION_COOKIE_SECURE'] = False         # ✅ False if you're using HTTP
Session(app)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
os.makedirs("charts", exist_ok=True)
CHART_DIR = "charts"
# USER_CACHE = {}
# Register blueprint
app.register_blueprint(astrology_bp)
# USER_CACHE = {}
if __name__ == '__main__':
    app.run(debug=True)
