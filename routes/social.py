# OpenNet Social Routes
# Handles following, friend requests, and notifications

from flask import Blueprint, request, redirect, url_for, render_template, jsonify
import database
from routes.auth import get_current_user, login_required

social_bp = Blueprint("social", __name__)


@social_bp.route("/follow/<int:user_id>", methods=["POST"])
def follow_user(user_id):
    """Follow a user or send follow request if private"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    if current_user["id"] == user_id:
        return redirect(url_for("profile.view_profile", id=user_id))

    # Get target user
    target = database.get_user_by_id(user_id)
    if not target:
        return "User not found", 404

    target = dict(target[0])

    # Check if already following
    if database.is_following(current_user["id"], user_id):
        return redirect(url_for("profile.view_profile", id=user_id))

    # If private account, send follow request
    if target.get("is_private"):
        if not database.has_pending_request(current_user["id"], user_id):
            database.send_follow_request(current_user["id"], user_id)
    else:
        # Public account - follow directly
        database.follow_user(current_user["id"], user_id)
        # Create notification
        database.create_notification(user_id, "follow", current_user["id"])

    return redirect(url_for("profile.view_profile", id=user_id))


@social_bp.route("/unfollow/<int:user_id>", methods=["POST"])
def unfollow_user(user_id):
    """Unfollow a user"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    database.unfollow_user(current_user["id"], user_id)
    return redirect(url_for("profile.view_profile", id=user_id))


@social_bp.route("/request/<int:request_id>/accept", methods=["POST"])
def accept_request(request_id):
    """Accept a follow request"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    # Verify this request is for the current user
    req = database.get_follow_request(request_id)
    if req and req["target_id"] == current_user["id"]:
        database.accept_follow_request(request_id)

    return redirect(url_for("social.notifications"))


@social_bp.route("/request/<int:request_id>/reject", methods=["POST"])
def reject_request(request_id):
    """Reject a follow request"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    # Verify this request is for the current user
    req = database.get_follow_request(request_id)
    if req and req["target_id"] == current_user["id"]:
        database.reject_follow_request(request_id)

    return redirect(url_for("social.notifications"))


@social_bp.route("/notifications")
def notifications():
    """View notifications/activity page"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    # Get pending follow requests
    pending_requests = database.get_pending_requests(current_user["id"])

    # Get all notifications
    all_notifications = database.get_notifications(current_user["id"])

    # Mark as read
    database.mark_notifications_read(current_user["id"])

    return render_template(
        "notifications.html",
        pending_requests=pending_requests,
        notifications=all_notifications,
        current_user=current_user,
    )
