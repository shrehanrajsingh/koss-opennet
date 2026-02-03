# VulnNet Authentication Routes
# INTENTIONALLY INSECURE - For educational purposes only

from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    make_response,
    session,
)
import hashlib
import time
import database

auth_bp = Blueprint("auth", __name__)


def generate_weak_token(user_id):
    """
    VULNERABLE: Weak session token generation
    Token is predictable: md5(user_id + timestamp)
    """
    timestamp = int(time.time())
    token = hashlib.md5(f"{user_id}{timestamp}".encode()).hexdigest()
    return token


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # VULNERABILITY: SQL Injection
        # The unsafe_login function uses string formatting
        # Exploit: username = admin'-- or ' OR '1'='1'--
        user = database.unsafe_login(username, password)

        if user:
            # VULNERABILITY: Weak session token
            token = generate_weak_token(user["id"])

            # Store session
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]  # VULNERABILITY: Role in session

            response = make_response(redirect(url_for("posts.feed")))

            # VULNERABILITY: Cookies not HttpOnly, not Secure
            response.set_cookie("session_token", token)
            response.set_cookie("user_id", str(user["id"]))
            response.set_cookie("username", user["username"])
            response.set_cookie("role", user["role"])  # VULNERABILITY: Role in cookie

            return response
        else:
            error = "Invalid credentials"

    # VULNERABILITY: Auth bypass via query parameter
    if request.args.get("admin") == "true":
        session["user_id"] = 1
        session["username"] = "admin"
        session["role"] = "admin"
        response = make_response(redirect(url_for("posts.feed")))
        response.set_cookie("role", "admin")
        return response

    return render_template("login.html", error=error)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        email = request.form.get("email", "")

        # VULNERABILITY: No password strength requirements
        # VULNERABILITY: Plaintext password storage
        try:
            database.create_user(username, password, email)
            success = "Account created! You can now login."
        except Exception as e:
            error = f"Registration failed: {str(e)}"

    return render_template("register.html", error=error, success=success)


@auth_bp.route("/logout")
def logout():
    session.clear()
    response = make_response(redirect(url_for("auth.login")))
    response.delete_cookie("session_token")
    response.delete_cookie("user_id")
    response.delete_cookie("username")
    response.delete_cookie("role")
    return response


def get_current_user():
    """Get current user from session or cookie"""
    user_id = session.get("user_id") or request.cookies.get("user_id")
    if user_id:
        users = database.get_user_by_id(user_id)
        if users:
            return dict(users[0])
    return None


def is_admin():
    """
    VULNERABLE: Admin check uses cookie instead of database
    Exploit: Set cookie 'role=admin' in browser
    """
    return request.cookies.get("role") == "admin" or session.get("role") == "admin"


def login_required(f):
    """Decorator to require login"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    VULNERABLE: Admin check based on cookie
    Decorator to require admin role
    """
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function
