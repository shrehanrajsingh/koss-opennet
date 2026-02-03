# VulnNet Admin Routes
# INTENTIONALLY INSECURE - For educational purposes only

from flask import Blueprint, request, render_template, redirect, url_for, jsonify
import database
from routes.auth import get_current_user, is_admin, admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
def admin_dashboard():
    """
    VULNERABLE: Admin check based on cookie, not database
    Exploit: Set cookie 'role=admin' in browser DevTools

    Also: Hidden admin route - discoverable via directory brute-forcing
    """
    # VULNERABILITY: Using is_admin() which checks cookie
    if not is_admin():
        return "Access Denied", 403

    users = database.get_all_users()
    posts = database.get_all_posts()
    current_user = get_current_user()

    # VULNERABILITY: Exposes all user data including passwords
    return render_template(
        "admin/dashboard.html", users=users, posts=posts, current_user=current_user
    )


@admin_bp.route("/users")
def admin_users():
    """List all users for admin"""
    if not is_admin():
        return "Access Denied", 403

    users = database.get_all_users()
    current_user = get_current_user()

    return render_template("admin/users.html", users=users, current_user=current_user)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    """
    VULNERABLE: No CSRF protection
    VULNERABLE: Admin check via cookie only
    """
    if not is_admin():
        return "Access Denied", 403

    database.delete_user(user_id)
    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
def change_role(user_id):
    """
    VULNERABLE: Privilege escalation possible
    Exploit: Any user with admin cookie can make others admin
    """
    if not is_admin():
        return "Access Denied", 403

    new_role = request.form.get("role", "user")
    database.update_user_role(user_id, new_role)

    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
def admin_delete_post(post_id):
    """Delete any post as admin"""
    if not is_admin():
        return "Access Denied", 403

    database.delete_post(post_id)
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/logs")
def view_logs():
    """
    VULNERABLE: Exposes system information
    Hidden endpoint that might reveal sensitive data
    """
    if not is_admin():
        return "Access Denied", 403

    # Simulated log data with hints
    logs = [
        "[INFO] User 'admin' logged in from 192.168.1.1",
        "[WARN] Failed login attempt for 'admin' - password: 'admin123'",
        "[DEBUG] Database path: /Volumes/Seagate/NodeProjects/koss-workshop-cb/vulnnet.db",
        "[INFO] Session token generated: predictable_md5_hash",
        "[ERROR] SQL syntax error near '-- (SQL Injection attempt detected)",
    ]

    current_user = get_current_user()
    return render_template("admin/logs.html", logs=logs, current_user=current_user)


@admin_bp.route("/backup")
def backup():
    """
    VULNERABLE: Exposes database backup
    Should never expose in production
    """
    if not is_admin():
        return "Access Denied", 403

    users = database.get_all_users()

    # VULNERABILITY: Excessive data exposure
    data = {
        "users": [dict(u) for u in users],
        "database_path": database.DATABASE_PATH,
        "secret_key": "super_secret_key_12345",  # VULNERABILITY: Exposed secret
    }

    return jsonify(data)
