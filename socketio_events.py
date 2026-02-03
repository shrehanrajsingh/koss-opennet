# SocketIO Event Handlers for Real-Time Chat
# INTENTIONALLY INSECURE - For educational purposes only

from flask_socketio import emit, join_room, leave_room
from flask import session
import database


def register_socketio_events(socketio):
    """Register all SocketIO event handlers"""

    @socketio.on("connect")
    def handle_connect():
        """Handle client connection"""
        user_id = session.get("user_id")
        if user_id:
            # Join personal room for direct messages
            join_room(f"user_{user_id}")
            emit("connected", {"status": "connected", "user_id": user_id})

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle client disconnection"""
        user_id = session.get("user_id")
        if user_id:
            leave_room(f"user_{user_id}")

    @socketio.on("join_chat")
    def handle_join_chat(data):
        """Join a chat room with another user"""
        user_id = session.get("user_id")
        other_user_id = data.get("other_user_id")
        if user_id and other_user_id:
            # Create consistent room name (smaller id first)
            room = f"chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
            join_room(room)
            emit("joined_chat", {"room": room, "other_user_id": other_user_id})

    @socketio.on("leave_chat")
    def handle_leave_chat(data):
        """Leave a chat room"""
        user_id = session.get("user_id")
        other_user_id = data.get("other_user_id")
        if user_id and other_user_id:
            room = f"chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
            leave_room(room)

    @socketio.on("send_message")
    def handle_send_message(data):
        """Handle sending a new message"""
        user_id = session.get("user_id")
        receiver_id = data.get("receiver_id")
        content = data.get("content", "").strip()

        if not user_id or not receiver_id or not content:
            emit("error", {"message": "Invalid message data"})
            return

        # Save to database
        message_id = database.send_message(user_id, receiver_id, content)

        # Get sender info
        sender = database.get_user_by_id(user_id)
        sender_name = sender[0]["username"] if sender else "Unknown"
        sender_pic = sender[0]["profile_pic"] if sender else "default.png"

        # Message payload
        message_data = {
            "id": message_id,
            "sender_id": user_id,
            "sender_name": sender_name,
            "sender_pic": sender_pic,
            "receiver_id": receiver_id,
            "content": content,
            "created_at": "Just now",
        }

        # Emit to the chat room
        room = f"chat_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
        emit("new_message", message_data, room=room)

        # Also emit to receiver's personal room for notifications
        emit("new_message_notification", message_data, room=f"user_{receiver_id}")

    @socketio.on("typing")
    def handle_typing(data):
        """Handle typing indicator"""
        user_id = session.get("user_id")
        other_user_id = data.get("other_user_id")
        if user_id and other_user_id:
            room = f"chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
            emit("user_typing", {"user_id": user_id}, room=room, include_self=False)

    @socketio.on("stop_typing")
    def handle_stop_typing(data):
        """Handle stop typing indicator"""
        user_id = session.get("user_id")
        other_user_id = data.get("other_user_id")
        if user_id and other_user_id:
            room = f"chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
            emit(
                "user_stop_typing", {"user_id": user_id}, room=room, include_self=False
            )
