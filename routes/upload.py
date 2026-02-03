# VulnNet Upload Routes
# INTENTIONALLY INSECURE - For educational purposes only

from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    send_from_directory,
)
import os
from werkzeug.utils import secure_filename
import database
from routes.auth import get_current_user, login_required
from config import UPLOAD_FOLDER

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload", methods=["GET", "POST"])
def upload_file():
    """
    VULNERABLE: No file type validation
    VULNERABLE: Path traversal
    VULNERABLE: Executable file uploads

    Exploits:
    - Upload .php, .py, .sh files for web shell
    - filename = ../../etc/passwd to overwrite files
    - Upload HTML with JavaScript for XSS
    """
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    message = None

    if request.method == "POST":
        if "file" not in request.files:
            message = "No file provided"
        else:
            file = request.files["file"]
            if file.filename == "":
                message = "No file selected"
            else:
                # VULNERABILITY: No file type validation
                # VULNERABILITY: filename not sanitized (path traversal)

                # Check if user wants to bypass security
                bypass = request.form.get("bypass", "")

                if bypass == "true":
                    # VULNERABILITY: Path traversal enabled
                    # Exploit: filename=../../config.py
                    filename = file.filename
                else:
                    # Still vulnerable to extension attacks
                    filename = file.filename

                filepath = os.path.join(UPLOAD_FOLDER, filename)

                # VULNERABILITY: No validation of file content
                # Could upload PHP shell, Python script, etc.
                file.save(filepath)

                # Update profile pic if image upload
                if request.form.get("profile_pic"):
                    database.update_user_profile(
                        current_user["id"], current_user.get("bio", ""), filename
                    )

                message = f"File uploaded successfully: {filename}"

    return render_template("upload.html", message=message, current_user=current_user)


@upload_bp.route("/uploads/<path:filename>")
def serve_upload(filename):
    """
    VULNERABLE: Path traversal in file serving
    Exploit: /uploads/../config.py
    """
    # VULNERABILITY: No path validation
    return send_from_directory(UPLOAD_FOLDER, filename)


@upload_bp.route("/download")
def download_file():
    """
    VULNERABLE: Path traversal via query parameter
    Exploit: /download?file=../../../etc/passwd
    """
    filename = request.args.get("file", "")

    # VULNERABILITY: Path traversal possible
    # No sanitization of filename
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except:
        return "File not found", 404
