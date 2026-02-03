# VulnNet Search Routes
# INTENTIONALLY INSECURE - For educational purposes only

from flask import Blueprint, request, render_template
import database
from routes.auth import get_current_user

search_bp = Blueprint("search", __name__)


@search_bp.route("/search")
def search():
    """
    VULNERABLE: SQL Injection in search query
    VULNERABLE: Reflected XSS - search term echoed unsanitized

    SQL Injection Exploits:
    - /search?q=' UNION SELECT id, username, password, email, bio, profile_pic, role, created_at FROM users--
    - /search?q=' OR '1'='1

    XSS Exploits:
    - /search?q=<script>alert('XSS')</script>
    - /search?q=<img src=x onerror=alert('XSS')>
    """
    query = request.args.get("q", "")
    current_user = get_current_user()

    users = []
    posts = []

    if query:
        # VULNERABILITY: SQL Injection - wrapped in try/except so UNION attacks work
        try:
            users = database.unsafe_search(query)
        except Exception as e:
            print(f"User search error (SQLi?): {e}")

        try:
            posts = database.unsafe_search_posts(query)
        except Exception as e:
            print(f"Post search error (SQLi?): {e}")

    # VULNERABILITY: query echoed in template without escaping
    return render_template(
        "search.html",
        query=query,  # Rendered with |safe in template
        users=users,
        posts=posts,
        current_user=current_user,
    )


@search_bp.route("/redirect")
def open_redirect():
    """
    VULNERABLE: Open Redirect
    Exploit: /redirect?url=http://evil.com
    """
    url = request.args.get("url", "/")

    # VULNERABILITY: No validation of redirect URL
    from flask import redirect

    return redirect(url)
