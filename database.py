# VulnNet Database Module
# INTENTIONALLY INSECURE - For educational purposes only
# Uses raw SQL queries (no ORM) to enable SQL injection vulnerabilities

import sqlite3
import os
from config import DATABASE_PATH


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with schema"""
    conn = get_db()
    cursor = conn.cursor()

    # Users table - plaintext passwords (vulnerability)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            bio TEXT DEFAULT '',
            profile_pic TEXT DEFAULT 'default.png',
            role TEXT DEFAULT 'user',
            is_private INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Posts table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """
    )

    # Comments table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """
    )

    # Messages table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    """
    )

    # Likes table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(post_id, user_id)
        )
    """
    )

    # Sessions table - weak tokens (vulnerability)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """
    )

    # Follows table (for direct follows)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS follows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower_id INTEGER NOT NULL,
            followed_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (follower_id) REFERENCES users(id),
            FOREIGN KEY (followed_id) REFERENCES users(id),
            UNIQUE(follower_id, followed_id)
        )
    """
    )

    # Follow Requests table (for private accounts)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS follow_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (requester_id) REFERENCES users(id),
            FOREIGN KEY (target_id) REFERENCES users(id),
            UNIQUE(requester_id, target_id)
        )
    """
    )

    # Notifications table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            from_user_id INTEGER NOT NULL,
            reference_id INTEGER,
            read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (from_user_id) REFERENCES users(id)
        )
    """
    )

    # Retweets table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS retweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(post_id, user_id)
        )
    """
    )

    # Create admin user with plaintext password
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (username, password, email, role)
        VALUES ('admin', 'admin123', 'admin@vulnnet.local', 'admin')
    """
    )

    # Create sample users
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (username, password, email, bio)
        VALUES ('john', 'password123', 'john@vulnnet.local', 'Hello, I am John!')
    """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (username, password, email, bio)
        VALUES ('jane', 'jane2024', 'jane@vulnnet.local', 'Security enthusiast')
    """
    )

    conn.commit()
    conn.close()


# Raw SQL query functions - INTENTIONALLY VULNERABLE


def execute_query(query, params=None):
    """Execute a query and return results"""
    conn = get_db()
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


def execute_write(query, params=None):
    """Execute an insert/update/delete query"""
    conn = get_db()
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    conn.commit()
    lastrowid = cursor.lastrowid
    conn.close()
    return lastrowid


# VULNERABLE: These functions use string formatting instead of parameterized queries


def unsafe_login(username, password):
    """
    VULNERABLE: SQL Injection
    Exploit: username = admin'-- or password = ' OR '1'='1
    """
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    return user


def unsafe_search(search_term):
    """
    VULNERABLE: SQL Injection
    Exploit: search_term = ' UNION SELECT id,username,password,email,bio,profile_pic,role,created_at FROM users--

    Note: The users table has 8 columns:
    id, username, password, email, bio, profile_pic, role, created_at
    """
    query = f"SELECT * FROM users WHERE username LIKE '%{search_term}%' OR bio LIKE '%{search_term}%'"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


def unsafe_search_posts(search_term):
    """
    VULNERABLE: SQL Injection
    """
    query = f"SELECT posts.*, users.username FROM posts JOIN users ON posts.user_id = users.id WHERE posts.content LIKE '%{search_term}%'"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


def get_user_by_id(user_id):
    """Get user by ID - used for IDOR demonstration"""
    query = "SELECT * FROM users WHERE id = ?"
    return execute_query(query, (user_id,))


def get_all_users():
    """Get all users - excessive data exposure"""
    query = "SELECT * FROM users"
    return execute_query(query)


def create_user(username, password, email):
    """Create user with plaintext password (vulnerability)"""
    query = "INSERT INTO users (username, password, email) VALUES (?, ?, ?)"
    return execute_write(query, (username, password, email))


def update_user_profile(user_id, bio, profile_pic=None):
    """Update user profile - no access control check"""
    if profile_pic:
        query = "UPDATE users SET bio = ?, profile_pic = ? WHERE id = ?"
        return execute_write(query, (bio, profile_pic, user_id))
    else:
        query = "UPDATE users SET bio = ? WHERE id = ?"
        return execute_write(query, (bio, user_id))


def create_post(user_id, content, image_url=None):
    """Create a post - content not sanitized (XSS)"""
    query = "INSERT INTO posts (user_id, content, image_url) VALUES (?, ?, ?)"
    return execute_write(query, (user_id, content, image_url))


def get_all_posts():
    """Get all posts with user info"""
    query = """
        SELECT posts.*, users.username, users.profile_pic, users.role,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count,
               (SELECT COUNT(*) FROM comments WHERE comments.post_id = posts.id) as comment_count,
               (SELECT COUNT(*) FROM retweets WHERE retweets.post_id = posts.id) as retweet_count
        FROM posts 
        JOIN users ON posts.user_id = users.id 
        ORDER BY posts.created_at DESC
    """
    return execute_query(query)


def get_post_by_id(post_id):
    """Get single post"""
    query = """
        SELECT posts.*, users.username, users.profile_pic
        FROM posts 
        JOIN users ON posts.user_id = users.id 
        WHERE posts.id = ?
    """
    return execute_query(query, (post_id,))


def create_comment(post_id, user_id, content):
    """Create comment - not sanitized (XSS)"""
    query = "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)"
    return execute_write(query, (post_id, user_id, content))


def get_comments_by_post(post_id):
    """Get comments for a post"""
    query = """
        SELECT comments.*, users.username, users.profile_pic
        FROM comments 
        JOIN users ON comments.user_id = users.id 
        WHERE comments.post_id = ?
        ORDER BY comments.created_at ASC
    """
    return execute_query(query, (post_id,))


def send_message(sender_id, receiver_id, content):
    """Send message - content not sanitized"""
    query = "INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)"
    return execute_write(query, (sender_id, receiver_id, content))


def get_messages_for_user(user_id):
    """Get messages - no access control (IDOR)"""
    query = """
        SELECT messages.*, 
               sender.username as sender_name,
               receiver.username as receiver_name
        FROM messages
        JOIN users sender ON messages.sender_id = sender.id
        JOIN users receiver ON messages.receiver_id = receiver.id
        WHERE messages.receiver_id = ? OR messages.sender_id = ?
        ORDER BY messages.created_at DESC
    """
    return execute_query(query, (user_id, user_id))


def get_conversation(user1_id, user2_id):
    """Get messages between two specific users"""
    query = """
        SELECT messages.*, 
               sender.username as sender_name,
               sender.profile_pic as sender_pic,
               receiver.username as receiver_name,
               receiver.profile_pic as receiver_pic
        FROM messages
        JOIN users sender ON messages.sender_id = sender.id
        JOIN users receiver ON messages.receiver_id = receiver.id
        WHERE (messages.sender_id = ? AND messages.receiver_id = ?)
           OR (messages.sender_id = ? AND messages.receiver_id = ?)
        ORDER BY messages.created_at ASC
    """
    return execute_query(query, (user1_id, user2_id, user2_id, user1_id))


def get_conversation_list(user_id):
    """Get list of users the current user has conversations with"""
    query = """
        SELECT DISTINCT 
            CASE 
                WHEN messages.sender_id = ? THEN messages.receiver_id
                ELSE messages.sender_id
            END as other_user_id,
            users.username,
            users.profile_pic,
            (SELECT content FROM messages m2 
             WHERE (m2.sender_id = messages.sender_id AND m2.receiver_id = messages.receiver_id)
                OR (m2.sender_id = messages.receiver_id AND m2.receiver_id = messages.sender_id)
             ORDER BY m2.created_at DESC LIMIT 1) as last_message,
            (SELECT created_at FROM messages m3 
             WHERE (m3.sender_id = messages.sender_id AND m3.receiver_id = messages.receiver_id)
                OR (m3.sender_id = messages.receiver_id AND m3.receiver_id = messages.sender_id)
             ORDER BY m3.created_at DESC LIMIT 1) as last_message_time
        FROM messages
        JOIN users ON users.id = CASE 
            WHEN messages.sender_id = ? THEN messages.receiver_id 
            ELSE messages.sender_id 
        END
        WHERE messages.sender_id = ? OR messages.receiver_id = ?
        GROUP BY other_user_id
        ORDER BY last_message_time DESC
    """
    return execute_query(query, (user_id, user_id, user_id, user_id))


def get_message_by_id(message_id):
    """Get single message - IDOR vulnerability"""
    query = """
        SELECT messages.*, 
               sender.username as sender_name,
               receiver.username as receiver_name
        FROM messages
        JOIN users sender ON messages.sender_id = sender.id
        JOIN users receiver ON messages.receiver_id = receiver.id
        WHERE messages.id = ?
    """
    return execute_query(query, (message_id,))


def like_post(post_id, user_id):
    """Like a post - only one like per user per post"""
    query = "INSERT OR IGNORE INTO likes (post_id, user_id) VALUES (?, ?)"
    return execute_write(query, (post_id, user_id))


def unlike_post(post_id, user_id):
    """Unlike a post"""
    query = "DELETE FROM likes WHERE post_id = ? AND user_id = ?"
    return execute_write(query, (post_id, user_id))


def has_liked(post_id, user_id):
    """Check if user has liked a post"""
    query = "SELECT id FROM likes WHERE post_id = ? AND user_id = ?"
    result = execute_query(query, (post_id, user_id))
    return len(result) > 0


def get_user_liked_posts(user_id):
    """Get set of post IDs that user has liked"""
    query = "SELECT post_id FROM likes WHERE user_id = ?"
    result = execute_query(query, (user_id,))
    return {row["post_id"] for row in result}


def retweet_post(post_id, user_id):
    """Retweet a post - only one retweet per user per post"""
    query = "INSERT OR IGNORE INTO retweets (post_id, user_id) VALUES (?, ?)"
    return execute_write(query, (post_id, user_id))


def unretweet_post(post_id, user_id):
    """Remove a retweet"""
    query = "DELETE FROM retweets WHERE post_id = ? AND user_id = ?"
    return execute_write(query, (post_id, user_id))


def has_retweeted(post_id, user_id):
    """Check if user has retweeted a post"""
    query = "SELECT id FROM retweets WHERE post_id = ? AND user_id = ?"
    result = execute_query(query, (post_id, user_id))
    return len(result) > 0


def get_posts_retweeted_by_user(user_id):
    """Get all posts that a specific user has retweeted"""
    query = """
        SELECT posts.*, users.username, users.profile_pic, users.role,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count,
               (SELECT COUNT(*) FROM comments WHERE comments.post_id = posts.id) as comment_count,
               (SELECT COUNT(*) FROM retweets WHERE retweets.post_id = posts.id) as retweet_count,
               retweets.created_at as retweeted_at
        FROM retweets
        JOIN posts ON retweets.post_id = posts.id
        JOIN users ON posts.user_id = users.id
        WHERE retweets.user_id = ?
        ORDER BY retweets.created_at DESC
    """
    return execute_query(query, (user_id,))


def get_user_replies(user_id, viewer_id=None):
    """
    Get all replies (comments) by a user, including the parent post.
    Filters out replies to private posts if viewer is not allowed to see them.
    """
    viewer_id = viewer_id or -1  # Handle None viewer
    query = """
        SELECT 
            comments.id as comment_id, comments.content as comment_content, comments.created_at as comment_created_at,
            posts.id as post_id, posts.content as post_content, posts.created_at as post_created_at,
            post_author.username as post_author_username, post_author.profile_pic as post_author_pic, 
            post_author.id as post_author_id
        FROM comments
        JOIN posts ON comments.post_id = posts.id
        JOIN users as post_author ON posts.user_id = post_author.id
        WHERE comments.user_id = ?
        AND (
            post_author.is_private = 0
            OR post_author.id = ?
            OR EXISTS (SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = post_author.id)
        )
        ORDER BY comments.created_at DESC
    """
    return execute_query(query, (user_id, viewer_id, viewer_id))


def get_posts_liked_by_user(target_user_id, viewer_id=None):
    """
    Get all posts liked by a user.
    Filters out private posts if viewer is not allowed to see them.
    """
    viewer_id = viewer_id or -1
    query = """
        SELECT posts.*, author.username, author.profile_pic, author.role,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count,
               (SELECT COUNT(*) FROM comments WHERE comments.post_id = posts.id) as comment_count,
               (SELECT COUNT(*) FROM retweets WHERE retweets.post_id = posts.id) as retweet_count,
               likes.created_at as liked_at
        FROM likes
        JOIN posts ON likes.post_id = posts.id
        JOIN users as author ON posts.user_id = author.id
        WHERE likes.user_id = ?
        AND (
            author.is_private = 0
            OR author.id = ?
            OR EXISTS (SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = author.id)
        )
        ORDER BY likes.created_at DESC
    """
    return execute_query(query, (target_user_id, viewer_id, viewer_id))


def get_user_retweeted_posts(user_id):
    """Get set of post IDs that user has retweeted"""
    query = "SELECT post_id FROM retweets WHERE user_id = ?"
    result = execute_query(query, (user_id,))
    return {row["post_id"] for row in result}


def get_retweet_count(post_id):
    """Get retweet count for a post"""
    query = "SELECT COUNT(*) as count FROM retweets WHERE post_id = ?"
    result = execute_query(query, (post_id,))
    return result[0]["count"] if result else 0


def delete_post(post_id):
    """Delete post - no authorization check"""
    query = "DELETE FROM posts WHERE id = ?"
    return execute_write(query, (post_id,))


def delete_user(user_id):
    """Delete user - admin function, no proper auth"""
    query = "DELETE FROM users WHERE id = ?"
    return execute_write(query, (user_id,))


def update_user_role(user_id, role):
    """Update user role - dangerous without proper auth"""
    query = "UPDATE users SET role = ? WHERE id = ?"
    return execute_write(query, (role, user_id))


# ============== SOCIAL FEATURES ==============


def follow_user(follower_id, followed_id):
    """Create a follow relationship"""
    query = "INSERT OR IGNORE INTO follows (follower_id, followed_id) VALUES (?, ?)"
    return execute_write(query, (follower_id, followed_id))


def unfollow_user(follower_id, followed_id):
    """Remove a follow relationship"""
    query = "DELETE FROM follows WHERE follower_id = ? AND followed_id = ?"
    return execute_write(query, (follower_id, followed_id))


def is_following(follower_id, followed_id):
    """Check if user is following another user"""
    query = "SELECT id FROM follows WHERE follower_id = ? AND followed_id = ?"
    result = execute_query(query, (follower_id, followed_id))
    return len(result) > 0


def get_follower_count(user_id):
    """Get number of followers"""
    query = "SELECT COUNT(*) as count FROM follows WHERE followed_id = ?"
    result = execute_query(query, (user_id,))
    return result[0]["count"] if result else 0


def get_following_count(user_id):
    """Get number of users being followed"""
    query = "SELECT COUNT(*) as count FROM follows WHERE follower_id = ?"
    result = execute_query(query, (user_id,))
    return result[0]["count"] if result else 0


def get_followers(user_id):
    """Get list of followers"""
    query = """
        SELECT users.* FROM users
        JOIN follows ON users.id = follows.follower_id
        WHERE follows.followed_id = ?
    """
    return execute_query(query, (user_id,))


def get_following(user_id):
    """Get list of users being followed"""
    query = """
        SELECT users.* FROM users
        JOIN follows ON users.id = follows.followed_id
        WHERE follows.follower_id = ?
    """
    return execute_query(query, (user_id,))


def send_follow_request(requester_id, target_id):
    """Send a follow request to a private account"""
    query = (
        "INSERT OR IGNORE INTO follow_requests (requester_id, target_id) VALUES (?, ?)"
    )
    request_id = execute_write(query, (requester_id, target_id))
    # Create notification for target user
    create_notification(target_id, "follow_request", requester_id, request_id)
    return request_id


def has_pending_request(requester_id, target_id):
    """Check if there's a pending follow request"""
    query = "SELECT id FROM follow_requests WHERE requester_id = ? AND target_id = ? AND status = 'pending'"
    result = execute_query(query, (requester_id, target_id))
    return len(result) > 0


def get_follow_request(request_id):
    """Get a specific follow request"""
    query = """
        SELECT follow_requests.*, users.username as requester_name, users.profile_pic as requester_pic
        FROM follow_requests
        JOIN users ON follow_requests.requester_id = users.id
        WHERE follow_requests.id = ?
    """
    result = execute_query(query, (request_id,))
    return result[0] if result else None


def get_pending_requests(user_id):
    """Get pending follow requests for a user"""
    query = """
        SELECT follow_requests.*, users.username as requester_name, users.profile_pic as requester_pic
        FROM follow_requests
        JOIN users ON follow_requests.requester_id = users.id
        WHERE follow_requests.target_id = ? AND follow_requests.status = 'pending'
        ORDER BY follow_requests.created_at DESC
    """
    return execute_query(query, (user_id,))


def accept_follow_request(request_id):
    """Accept a follow request"""
    request = get_follow_request(request_id)
    if request:
        # Update request status
        query = "UPDATE follow_requests SET status = 'accepted' WHERE id = ?"
        execute_write(query, (request_id,))
        # Create follow relationship
        follow_user(request["requester_id"], request["target_id"])
        # Notify requester
        create_notification(
            request["requester_id"], "follow_accepted", request["target_id"], request_id
        )
        return True
    return False


def reject_follow_request(request_id):
    """Reject a follow request"""
    query = "UPDATE follow_requests SET status = 'rejected' WHERE id = ?"
    return execute_write(query, (request_id,))


def update_user_privacy(user_id, is_private):
    """Update user's privacy setting"""
    query = "UPDATE users SET is_private = ? WHERE id = ?"
    return execute_write(query, (1 if is_private else 0, user_id))


def create_notification(user_id, notification_type, from_user_id, reference_id=None):
    """Create a notification"""
    query = "INSERT INTO notifications (user_id, type, from_user_id, reference_id) VALUES (?, ?, ?, ?)"
    return execute_write(
        query, (user_id, notification_type, from_user_id, reference_id)
    )


def get_notifications(user_id):
    """Get notifications for a user"""
    query = """
        SELECT notifications.*, users.username as from_username, users.profile_pic as from_profile_pic
        FROM notifications
        JOIN users ON notifications.from_user_id = users.id
        WHERE notifications.user_id = ?
        ORDER BY notifications.created_at DESC
        LIMIT 50
    """
    return execute_query(query, (user_id,))


def get_unread_notification_count(user_id):
    """Get count of unread notifications"""
    query = "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND read = 0"
    result = execute_query(query, (user_id,))
    return result[0]["count"] if result else 0


def mark_notifications_read(user_id):
    """Mark all notifications as read"""
    query = "UPDATE notifications SET read = 1 WHERE user_id = ?"
    return execute_write(query, (user_id,))
