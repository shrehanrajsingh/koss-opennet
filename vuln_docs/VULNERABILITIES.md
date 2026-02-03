# VulnNet Vulnerability Documentation

This document describes all intentional vulnerabilities in VulnNet, organized by category.

---

## 1. SQL Injection

### Location: Login Form (`/login`)
**File:** `routes/auth.py` - `unsafe_login()` function

**Vulnerable Code:**
```python
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
```

**Exploits:**
- `admin'--` as username (bypasses password check)
- `' OR '1'='1'--` as password (returns first user)

---

### Location: Search (`/search`)
**File:** `routes/search.py` and `database.py`

**Exploit:**
```
/search?q=' UNION SELECT id,username,password,email,bio,profile_pic,role,created_at FROM users--
```

---

## 2. Cross-Site Scripting (XSS)

### Stored XSS
- **Profile bio:** Edit profile with `<script>alert('XSS')</script>`
- **Posts:** Create post with malicious script
- **Comments:** Add comment with XSS payload
- **Messages:** Send message with XSS

### Reflected XSS
- **Search:** `/search?q=<script>alert(1)</script>`
- **Message preview:** `/messages/1?preview=<script>alert(1)</script>`

### DOM XSS
- **URL Hash:** `/feed#<img src=x onerror=alert('XSS')>`
- **URL Param:** `/feed?msg=<script>alert(1)</script>`
- **Eval param:** `/feed?eval=alert('XSS')`

---

## 3. Insecure Direct Object Reference (IDOR)

- **Profiles:** `/profile?id=1`, `/profile?id=2`
- **Messages:** `/messages/1`, `/api/messages?user_id=1`
- **Profile edit:** Change `user_id` hidden field

---

## 4. Broken Authentication

- **Auth bypass:** `/login?admin=true`
- **Cookie tampering:** Set `role=admin` in DevTools
- **Weak session tokens:** MD5(user_id + timestamp)
- **Plaintext passwords**

---

## 5. CSRF (Cross-Site Request Forgery)

All forms lack CSRF tokens:
- Create post
- Add comment
- Like post
- Send message
- Profile edit
- Admin actions

---

## 6. Insecure File Upload

**Location:** `/upload`

- No file type validation
- Path traversal: `../../config.py`
- Web shell upload possible

---

## 7. Broken Access Control

- Admin panel accessible via cookie tampering
- Hidden endpoints discoverable
- No server-side authorization

---

## 8. Sensitive Data Exposure

- `/api/users` - Returns all users with passwords
- `/admin/backup` - Exposes database and secret key
- Profile pages show passwords

---

## 9. Open Redirect

**Location:** `/redirect?url=http://evil.com`

---

## 10. Clickjacking

No X-Frame-Options header set.

---

## 11. Session Issues

- Cookies not HttpOnly
- Cookies not Secure
- Role stored in cookie (tamperable)
- Predictable session tokens
