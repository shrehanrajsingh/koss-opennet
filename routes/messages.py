# VulnNet Messages Routes
# INTENTIONALLY INSECURE - For educational purposes only

from flask import Blueprint, request, render_template, redirect, url_for, jsonify
import database
from routes.auth import get_current_user, login_required

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/messages")
def inbox():
    """View message inbox"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    messages = database.get_messages_for_user(current_user["id"])
    users = database.get_following(current_user["id"])

    return render_template(
        "messages.html", messages=messages, users=users, current_user=current_user
    )


@messages_bp.route("/messages/<int:message_id>")
def view_message(message_id):
    """
    VULNERABLE: IDOR - Any user can view any message
    Exploit: /messages/1, /messages/2, etc.
    """
    # VULNERABILITY: No check if user is sender or receiver
    messages = database.get_message_by_id(message_id)
    if not messages:
        return "Message not found", 404

    message = dict(messages[0])
    current_user = get_current_user()

    # VULNERABILITY: Reflected XSS in preview parameter
    preview = request.args.get("preview", "")

    return render_template(
        "message_view.html",
        message=message,
        preview=preview,  # VULNERABLE: Rendered unsafely
        current_user=current_user,
    )


@messages_bp.route("/messages/send", methods=["POST"])
def send_message():
    """
    VULNERABLE: No CSRF protection
    VULNERABLE: Stored XSS in message content
    """
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    receiver_id = request.form.get("receiver_id")
    content = request.form.get("content", "")

    # VULNERABILITY: Content not sanitized
    database.send_message(current_user["id"], receiver_id, content)

    return redirect(url_for("messages.inbox"))


@messages_bp.route("/api/messages")
def api_messages():
    """
    VULNERABLE: IDOR via user_id parameter
    Exploit: /api/messages?user_id=1 to get admin's messages
    """
    # VULNERABILITY: user_id from query parameter, not session
    user_id = request.args.get("user_id")

    if not user_id:
        current_user = get_current_user()
        if current_user:
            user_id = current_user["id"]
        else:
            return jsonify({"error": "Not authenticated"}), 401

    messages = database.get_messages_for_user(user_id)

    # Convert to list of dicts for JSON
    result = []
    for msg in messages:
        result.append(
            {
                "id": msg["id"],
                "sender_id": msg["sender_id"],
                "sender_name": msg["sender_name"],
                "receiver_id": msg["receiver_id"],
                "receiver_name": msg["receiver_name"],
                "content": msg[
                    "content"
                ],  # VULNERABILITY: Might contain sensitive data
                "created_at": msg["created_at"],
            }
        )

    return jsonify(result)


@messages_bp.route("/messages/chat/<int:user_id>")
def chat(user_id):
    """Real-time chat view with a specific user"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    # Get other user's info
    other_user = database.get_user_by_id(user_id)
    if not other_user:
        return "User not found", 404

    other_user = dict(other_user[0])

    # Get conversation history
    messages = database.get_conversation(current_user["id"], user_id)

    # Get conversation list for sidebar
    conversations = database.get_conversation_list(current_user["id"])

    return render_template(
        "chat.html",
        other_user=other_user,
        messages=messages,
        conversations=conversations,
        current_user=current_user,
    )


@messages_bp.route("/api/messages/conversation/<int:user_id>")
def api_conversation(user_id):
    """API endpoint for getting conversation with a user"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Not authenticated"}), 401

    messages = database.get_conversation(current_user["id"], user_id)

    result = []
    for msg in messages:
        result.append(
            {
                "id": msg["id"],
                "sender_id": msg["sender_id"],
                "sender_name": msg["sender_name"],
                "sender_pic": msg["sender_pic"],
                "receiver_id": msg["receiver_id"],
                "content": msg["content"],
                "created_at": msg["created_at"],
                "is_mine": msg["sender_id"] == current_user["id"],
            }
        )

    return jsonify(result)
