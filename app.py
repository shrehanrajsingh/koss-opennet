#!/usr/bin/env python3
"""
VulnNet - Intentionally Vulnerable Social Network
EDUCATIONAL PURPOSES ONLY - DO NOT DEPLOY TO PRODUCTION

This application contains intentional security vulnerabilities
for security training and penetration testing practice.
"""

from flask import Flask, render_template
from flask_socketio import SocketIO
import os

# Import configuration
from config import SECRET_KEY, UPLOAD_FOLDER, DEBUG

# Import database
import database

# Import blueprints
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.posts import posts_bp
from routes.messages import messages_bp
from routes.search import search_bp
from routes.admin import admin_bp
from routes.upload import upload_bp
from routes.api import api_bp
from routes.social import social_bp


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # VULNERABILITY: Hardcoded secret key
    app.secret_key = SECRET_KEY

    # Configure upload folder
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    # VULNERABILITY: Debug mode enabled (exposes stack traces)
    app.config["DEBUG"] = DEBUG

    # VULNERABILITY: Session cookies not HttpOnly or Secure
    app.config["SESSION_COOKIE_HTTPONLY"] = False
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SESSION_COOKIE_SAMESITE"] = None

    # Create upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Initialize database
    database.init_db()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(social_bp)

    # VULNERABILITY: No X-Frame-Options header (Clickjacking)
    # VULNERABILITY: No Content-Security-Policy header

    @app.after_request
    def add_insecure_headers(response):
        """Intentionally omit security headers"""
        # Not setting X-Frame-Options (Clickjacking vulnerability)
        # Not setting X-Content-Type-Options
        # Not setting X-XSS-Protection
        # Not setting Content-Security-Policy
        return response

    @app.route("/robots.txt")
    def robots():
        """
        VULNERABILITY: Reveals hidden paths
        """
        return """User-agent: *
Disallow: /admin
Disallow: /admin/backup
Disallow: /admin/logs
Disallow: /api/users
"""

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        # VULNERABILITY: Debug mode reveals stack traces
        return render_template("500.html", error=str(e)), 500

    return app


# Create app instance
app = create_app()

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Register SocketIO events
from socketio_events import register_socketio_events

register_socketio_events(socketio)

if __name__ == "__main__":
    print(
        """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║   ██╗   ██╗██╗   ██╗██╗     ███╗   ██╗███████╗████████╗║
    ║   ██║   ██║██║   ██║██║     ████╗  ██║██╔════╝╚══██╔══╝║
    ║   ██║   ██║██║   ██║██║     ██╔██╗ ██║█████╗     ██║   ║
    ║   ╚██╗ ██╔╝██║   ██║██║     ██║╚██╗██║██╔══╝     ██║   ║
    ║    ╚████╔╝ ╚██████╔╝███████╗██║ ╚████║███████╗   ██║   ║
    ║     ╚═══╝   ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ║
    ║                                                       ║
    ║              Social Network Platform                  ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    
    🌐 Server: http://localhost:5001
    """
    )

    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
