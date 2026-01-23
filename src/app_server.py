"""Flask server"""

import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request
from loguru import logger

load_dotenv()

app = Flask(__name__)

if __name__ == "__main__":
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    print("=" * 50)
    print("🚀 eSocial Automation Server")
    print("=" * 50)
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print("=" * 50)

    app.run(host=host, port=port, debug=debug)
