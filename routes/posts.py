# VulnNet Posts Routes
# INTENTIONALLY INSECURE - For educational purposes only

from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    session,
    jsonify,
)

import os
import database
from config import UPLOAD_FOLDER
from routes.auth import get_current_user, login_required

posts_bp = Blueprint("posts", __name__)


@posts_bp.route("/")
@posts_bp.route("/feed")
def feed():
    """Main feed showing all posts"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    posts = database.get_all_posts()

    # Get liked and retweeted status for each post
    liked_posts = set()
    retweeted_posts = set()
    if current_user:
        liked_posts = database.get_user_liked_posts(current_user["id"])
        retweeted_posts = database.get_user_retweeted_posts(current_user["id"])

    # VULNERABILITY: Posts rendered with |safe in template (Stored XSS)
    return render_template(
        "feed.html",
        posts=posts,
        current_user=current_user,
        liked_posts=liked_posts,
        retweeted_posts=retweeted_posts,
    )


@posts_bp.route("/post/create", methods=["POST"])
def create_post():
    """
    VULNERABLE: No CSRF protection
    Exploit: Create malicious form on external site that POSTs here

    VULNERABLE: Stored XSS - content not sanitized
    Exploit: content = <script>alert('XSS')</script>
    """
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    content = request.form.get("content", "")
    image_filename = None

    # Handle Image Upload
    if "image" in request.files:
        file = request.files["image"]
        if file.filename != "":
            # VULNERABILITY: No file type validation (keeping with theme)
            image_filename = file.filename
            filepath = os.path.join(UPLOAD_FOLDER, image_filename)
            file.save(filepath)

    # VULNERABILITY: Content stored without sanitization
    database.create_post(current_user["id"], content, image_filename)

    return redirect(url_for("posts.feed"))


@posts_bp.route("/post/<int:post_id>")
def view_post(post_id):
    """View single post with comments"""
    posts = database.get_post_by_id(post_id)
    if not posts:
        return "Post not found", 404

    post = dict(posts[0])
    comments = database.get_comments_by_post(post_id)
    current_user = get_current_user()

    return render_template(
        "post.html", post=post, comments=comments, current_user=current_user
    )


@posts_bp.route("/post/<int:post_id>/comment", methods=["POST"])
def add_comment(post_id):
    """
    VULNERABLE: No CSRF protection
    VULNERABLE: Stored XSS in comments
    """
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    content = request.form.get("content", "")

    # VULNERABILITY: Comment content not sanitized
    database.create_comment(post_id, current_user["id"], content)

    return redirect(url_for("posts.view_post", post_id=post_id))


@posts_bp.route("/post/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    """
    Toggle like - if already liked, unlike. Otherwise, like.
    VULNERABLE: No CSRF protection
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Not logged in"}), 401

    # Check if already liked
    if database.has_liked(post_id, current_user["id"]):
        database.unlike_post(post_id, current_user["id"])
    else:
        database.like_post(post_id, current_user["id"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True})
    return redirect(url_for("posts.feed"))


@posts_bp.route("/post/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    """
    VULNERABLE: No authorization check
    Any user can delete any post
    """
    # VULNERABILITY: No check if user owns the post
    database.delete_post(post_id)
    return redirect(url_for("posts.feed"))


@posts_bp.route("/post/<int:post_id>/retweet", methods=["POST"])
def retweet_post(post_id):
    """
    Toggle retweet - if already retweeted, unretweet. Otherwise, retweet.
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Not logged in"}), 401

    # Check if already retweeted
    if database.has_retweeted(post_id, current_user["id"]):
        database.unretweet_post(post_id, current_user["id"])
    else:
        database.retweet_post(post_id, current_user["id"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True})
    return redirect(url_for("posts.feed"))
