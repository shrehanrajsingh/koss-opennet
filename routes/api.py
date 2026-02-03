# VulnNet API Routes
# INTENTIONALLY INSECURE - For educational purposes only

from flask import Blueprint, request, jsonify
import database
from routes.auth import get_current_user

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/users")
def api_users():
    """
    VULNERABLE: No authentication required
    VULNERABLE: Excessive data exposure (includes passwords)
    VULNERABLE: Account enumeration

    Exploit: Anyone can GET /api/users to see all users and passwords
    """
    users = database.get_all_users()

    # VULNERABILITY: Exposing all user data including passwords
    result = []
    for user in users:
        result.append(
            {
                "id": user["id"],
                "username": user["username"],
                "password": user["password"],  # VULNERABILITY: Exposing passwords
                "email": user["email"],
                "bio": user["bio"],
                "role": user["role"],
                "created_at": user["created_at"],
            }
        )

    return jsonify(result)


@api_bp.route("/users/<int:user_id>")
def api_user(user_id):
    """
    VULNERABLE: IDOR - No authorization check
    VULNERABLE: Sensitive data exposure
    """
    users = database.get_user_by_id(user_id)
    if not users:
        return jsonify({"error": "User not found"}), 404

    user = dict(users[0])
    return jsonify(user)


@api_bp.route("/posts")
def api_posts():
    """Get all posts"""
    posts = database.get_all_posts()

    result = []
    for post in posts:
        result.append(
            {
                "id": post["id"],
                "user_id": post["user_id"],
                "username": post["username"],
                "content": post["content"],
                "like_count": post["like_count"],
                "comment_count": post["comment_count"],
                "created_at": post["created_at"],
            }
        )

    return jsonify(result)


@api_bp.route("/posts/<int:post_id>")
def api_post(post_id):
    """Get single post"""
    posts = database.get_post_by_id(post_id)
    if not posts:
        return jsonify({"error": "Post not found"}), 404

    post = dict(posts[0])
    comments = database.get_comments_by_post(post_id)

    post["comments"] = [dict(c) for c in comments]
    return jsonify(post)


@api_bp.route("/posts", methods=["POST"])
def api_create_post():
    """
    VULNERABLE: No CSRF protection
    VULNERABLE: No authentication required (can check cookie)
    VULNERABLE: Mass assignment potential
    """
    data = request.get_json() or request.form

    # VULNERABILITY: user_id from request, not session
    user_id = data.get("user_id")
    content = data.get("content", "")

    if not user_id:
        current_user = get_current_user()
        if current_user:
            user_id = current_user["id"]
        else:
            return jsonify({"error": "Not authenticated"}), 401

    # VULNERABILITY: No content sanitization
    post_id = database.create_post(user_id, content)

    return jsonify({"id": post_id, "success": True})


@api_bp.route("/messages", methods=["GET"])
def api_all_messages():
    """
    VULNERABLE: IDOR via user_id parameter
    Exploit: /api/messages?user_id=1 (get admin's messages)
    """
    user_id = request.args.get("user_id")

    if not user_id:
        current_user = get_current_user()
        if current_user:
            user_id = current_user["id"]
        else:
            return jsonify({"error": "Not authenticated"}), 401

    # VULNERABILITY: No check if requester is the user
    messages = database.get_messages_for_user(user_id)

    result = []
    for msg in messages:
        result.append(
            {
                "id": msg["id"],
                "sender_id": msg["sender_id"],
                "sender_name": msg["sender_name"],
                "receiver_id": msg["receiver_id"],
                "receiver_name": msg["receiver_name"],
                "content": msg["content"],
                "created_at": msg["created_at"],
            }
        )

    return jsonify(result)


@api_bp.route("/messages/<int:message_id>")
def api_message(message_id):
    """
    VULNERABLE: IDOR - Any message accessible
    """
    messages = database.get_message_by_id(message_id)
    if not messages:
        return jsonify({"error": "Message not found"}), 404

    return jsonify(dict(messages[0]))


@api_bp.route("/search")
def api_search():
    """
    VULNERABLE: SQL Injection
    Exploit: /api/search?q=' UNION SELECT * FROM users--
    """
    query = request.args.get("q", "")

    # VULNERABILITY: SQL Injection
    users = database.unsafe_search(query)
    posts = database.unsafe_search_posts(query)

    return jsonify(
        {"users": [dict(u) for u in users], "posts": [dict(p) for p in posts]}
    )


@api_bp.route("/user/update", methods=["POST"])
def api_update_user():
    """
    VULNERABLE: Mass assignment
    VULNERABLE: No authorization check
    Exploit: Include role=admin in request body
    """
    data = request.get_json() or request.form

    user_id = data.get("user_id")

    # VULNERABILITY: Can update any user
    if "bio" in data:
        database.update_user_profile(user_id, data["bio"])

    # VULNERABILITY: Mass assignment - can set role
    if "role" in data:
        database.update_user_role(user_id, data["role"])

    return jsonify({"success": True})
