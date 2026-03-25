from flask import Flask, render_template_string, request, redirect, session, flash, get_flashed_messages
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production-use-32-random-bytes')

# ── DB config ── replace the IP below with your db-server internal IP ──────────
app.config['MYSQL_HOST']        = '10.0.2.2'
app.config['MYSQL_USER']        = 'appuser'
app.config['MYSQL_PASSWORD']    = 'StrongPass123!'         
app.config['MYSQL_DB']          = 'userapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# ── Shared CSS + base layout ────────────────────────────────────────────────────
STYLE = """
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f0f4ff;
    padding: 24px;
  }
  /* Subtle grid pattern on background */
  body::before {
    content: '';
    position: fixed; inset: 0;
    background-image:
      linear-gradient(rgba(26,115,232,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(26,115,232,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
  }
  .card {
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04),
                0 0 0 1px rgba(0,0,0,0.05);
    width: 100%;
    max-width: 440px;
    padding: 40px;
    position: relative;
  }
  /* Top accent bar */
  .card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #1a73e8, #4285f4, #34a853);
    border-radius: 16px 16px 0 0;
  }
  /* Logo / header area */
  .logo {
    text-align: center;
    margin-bottom: 32px;
  }
  .logo-icon {
    width: 48px; height: 48px;
    background: linear-gradient(135deg, #1a73e8, #4285f4);
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
  }
  .logo-icon svg { width: 24px; height: 24px; fill: white; }
  .logo h1 { font-size: 20px; font-weight: 700; color: #1a1a2e; letter-spacing: -0.3px; }
  .logo p  { font-size: 13px; color: #6b7280; margin-top: 4px; }
  /* Page title */
  h2 { font-size: 22px; font-weight: 700; color: #111827; margin-bottom: 24px; letter-spacing: -0.4px; }
  /* Form fields */
  .field { margin-bottom: 18px; }
  label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 6px;
    letter-spacing: 0.1px;
  }
  .input-wrap { position: relative; }
  .input-wrap svg {
    position: absolute; left: 12px; top: 50%;
    transform: translateY(-50%);
    width: 16px; height: 16px;
    stroke: #9ca3af; fill: none;
    pointer-events: none;
  }
  input[type="text"], input[type="email"], input[type="password"] {
    width: 100%;
    padding: 11px 14px 11px 38px;
    border: 1.5px solid #e5e7eb;
    border-radius: 10px;
    font-size: 15px;
    color: #111827;
    background: #fafafa;
    outline: none;
    transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
  }
  input:focus {
    border-color: #1a73e8;
    background: #fff;
    box-shadow: 0 0 0 3px rgba(26,115,232,0.12);
  }
  input::placeholder { color: #d1d5db; }
  /* Password strength bar */
  #strength-bar-wrap { margin-top: 6px; display: none; }
  #strength-bar-wrap.show { display: block; }
  #strength-bar {
    height: 3px; border-radius: 2px; width: 0%;
    transition: width 0.3s, background 0.3s;
  }
  #strength-text { font-size: 11px; color: #6b7280; margin-top: 3px; }
  /* Submit button */
  .btn {
    width: 100%;
    padding: 13px;
    background: linear-gradient(135deg, #1a73e8, #1558c0);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 8px;
    letter-spacing: 0.2px;
    transition: opacity 0.15s, transform 0.1s;
    position: relative;
    overflow: hidden;
  }
  .btn:hover  { opacity: 0.92; }
  .btn:active { transform: scale(0.99); }
  /* Divider */
  .divider {
    display: flex; align-items: center; gap: 12px;
    margin: 24px 0;
    color: #d1d5db; font-size: 12px;
  }
  .divider::before, .divider::after {
    content: ''; flex: 1; height: 1px; background: #e5e7eb;
  }
  /* Link row below form */
  .switch-link {
    text-align: center;
    margin-top: 20px;
    font-size: 14px;
    color: #6b7280;
  }
  .switch-link a {
    color: #1a73e8;
    text-decoration: none;
    font-weight: 600;
  }
  .switch-link a:hover { text-decoration: underline; }
  /* Flash messages */
  .flash { border-radius: 10px; padding: 12px 16px; margin-bottom: 20px; font-size: 14px; display: flex; align-items: flex-start; gap: 10px; }
  .flash svg { width: 16px; height: 16px; flex-shrink: 0; margin-top: 1px; }
  .flash-error   { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }
  .flash-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }
  .flash-info    { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; }
  /* Dashboard card styles */
  .welcome-banner {
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .avatar {
    width: 48px; height: 48px;
    background: linear-gradient(135deg, #1a73e8, #4285f4);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 20px; font-weight: 700;
    flex-shrink: 0;
  }
  .welcome-text h3 { font-size: 16px; font-weight: 700; color: #1e40af; }
  .welcome-text p  { font-size: 13px; color: #3b82f6; margin-top: 2px; }
  .info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 20px;
  }
  .info-card {
    background: #f9fafb;
    border: 1px solid #f3f4f6;
    border-radius: 10px;
    padding: 14px;
  }
  .info-card .label { font-size: 11px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
  .info-card .value { font-size: 14px; color: #111827; font-weight: 500; word-break: break-all; }
  .arch-badge {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 20px;
    font-size: 12px;
    color: #166534;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .btn-danger {
    width: 100%;
    padding: 12px;
    background: white;
    color: #dc2626;
    border: 1.5px solid #fecaca;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
  }
  .btn-danger:hover { background: #fef2f2; }
  /* Floating GCP badge bottom of card */
  .gcp-badge {
    text-align: center;
    margin-top: 28px;
    font-size: 11px;
    color: #9ca3af;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }
  .gcp-dot { width: 6px; height: 6px; border-radius: 50%; background: #34a853; display: inline-block; }
</style>
"""

# ── SVG icons used in inputs ─────────────────────────────────────────────────
ICON_USER  = '<svg viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
ICON_EMAIL = '<svg viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>'
ICON_LOCK  = '<svg viewBox="0 0 24 24" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path stroke-linecap="round" stroke-linejoin="round" d="M7 11V7a5 5 0 0110 0v4"/></svg>'

def render_flashes():
    """Build flash message HTML from the session."""
    icon_err  = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
    icon_ok   = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>'
    icon_info = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    icons = {'error': icon_err, 'success': icon_ok, 'info': icon_info}
    html = ''
    for cat, msg in get_flashed_messages(with_categories=True):
        ic = icons.get(cat, icon_info)
        html += f'<div class="flash flash-{cat}">{ic}<span>{msg}</span></div>'
    return html

def base_page(title, body):
    return render_template_string(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — GCP App</title>
  {STYLE}
</head>
<body>
  <div class="card">
    {body}
    <div class="gcp-badge">
      <span class="gcp-dot"></span>
      Served by GCP · App Server VM · Private network
    </div>
  </div>
</body>
</html>""")

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect('/dashboard' if 'username' in session else '/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('/dashboard')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        # Basic validation — don't reveal which field is wrong (security)
        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return redirect('/login')

        # ── DB lookup ──────────────────────────────────────────────────────────
        # This query goes from this VM → MySQL on db-server VM
        # over the private VPC network on port 3306.
        # The internet cannot see or intercept this — it's fully internal.
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        # ── Password verification ──────────────────────────────────────────────
        # check_password_hash() re-hashes the input with the same salt stored in DB
        # and compares. If they match → correct password.
        # We deliberately say "Invalid username or password" not "wrong password"
        # so attackers can't use this to enumerate valid usernames.
        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            session['email']    = user['email']
            flash(f'Welcome back, {username}!', 'success')
            return redirect('/dashboard')
        flash('Invalid username or password. Please try again.', 'error')
        return redirect('/login')

    body = f"""
    <div class="logo">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      </div>
      <h1>GCP 3-Tier App</h1>
      <p>Sign in to your account</p>
    </div>
    {render_flashes()}
    <h2>Welcome back</h2>
    <form method="POST" action="/login" autocomplete="on">
      <div class="field">
        <label for="username">Username</label>
        <div class="input-wrap">{ICON_USER}<input type="text" id="username" name="username" placeholder="Your username" autocomplete="username" required></div>
      </div>
      <div class="field">
        <label for="password">Password</label>
        <div class="input-wrap">{ICON_LOCK}<input type="password" id="password" name="password" placeholder="Your password" autocomplete="current-password" required></div>
      </div>
      <button type="submit" class="btn">Sign in</button>
    </form>
    <div class="divider">or</div>
    <div class="switch-link">Don't have an account? <a href="/register">Create one</a></div>
    """
    return base_page('Login', body)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect('/dashboard')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        # ── Input validation ───────────────────────────────────────────────────
        if not all([username, email, password, confirm]):
            flash('All fields are required.', 'error')
            return redirect('/register')
        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'error')
            return redirect('/register')
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return redirect('/register')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect('/register')

        # ── Hash the password BEFORE writing to DB ─────────────────────────────
        # generate_password_hash() uses PBKDF2-HMAC-SHA256 with a random salt.
        # The salt is embedded in the hash string itself — stored as one field.
        # Even if two users have the same password their hashes will differ.
        hashed = generate_password_hash(password)

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hashed)
            )
            mysql.connection.commit()
            cur.close()
            flash('Account created! Please sign in.', 'success')
            return redirect('/login')
        except Exception:
            # MySQL will throw an exception on UNIQUE constraint violation
            flash('That username or email is already taken.', 'error')
            return redirect('/register')

    body = f"""
    <div class="logo">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      </div>
      <h1>GCP 3-Tier App</h1>
      <p>Create your account</p>
    </div>
    {render_flashes()}
    <h2>Create account</h2>
    <form method="POST" action="/register" autocomplete="off">
      <div class="field">
        <label for="username">Username</label>
        <div class="input-wrap">{ICON_USER}<input type="text" id="username" name="username" placeholder="At least 3 characters" required></div>
      </div>
      <div class="field">
        <label for="email">Email address</label>
        <div class="input-wrap">{ICON_EMAIL}<input type="email" id="email" name="email" placeholder="you@example.com" required></div>
      </div>
      <div class="field">
        <label for="password">Password</label>
        <div class="input-wrap">{ICON_LOCK}<input type="password" id="password" name="password" placeholder="At least 8 characters" oninput="checkStrength(this.value)" required></div>
        <div id="strength-bar-wrap">
          <div id="strength-bar"></div>
          <div id="strength-text"></div>
        </div>
      </div>
      <div class="field">
        <label for="confirm">Confirm password</label>
        <div class="input-wrap">{ICON_LOCK}<input type="password" id="confirm" name="confirm" placeholder="Repeat your password" required></div>
      </div>
      <button type="submit" class="btn">Create account</button>
    </form>
    <div class="divider">or</div>
    <div class="switch-link">Already have an account? <a href="/login">Sign in</a></div>

    <script>
    function checkStrength(pw) {{
      var wrap = document.getElementById('strength-bar-wrap');
      var bar  = document.getElementById('strength-bar');
      var txt  = document.getElementById('strength-text');
      if (!pw) {{ wrap.classList.remove('show'); return; }}
      wrap.classList.add('show');
      var score = 0;
      if (pw.length >= 8)  score++;
      if (pw.length >= 12) score++;
      if (/[A-Z]/.test(pw)) score++;
      if (/[0-9]/.test(pw)) score++;
      if (/[^A-Za-z0-9]/.test(pw)) score++;
      var levels = [
        {{w:'20%',  c:'#ef4444', t:'Very weak'}},
        {{w:'40%',  c:'#f97316', t:'Weak'}},
        {{w:'60%',  c:'#eab308', t:'Fair'}},
        {{w:'80%',  c:'#22c55e', t:'Strong'}},
        {{w:'100%', c:'#16a34a', t:'Very strong'}}
      ];
      var l = levels[Math.min(score, 4)];
      bar.style.width = l.w;
      bar.style.background = l.c;
      txt.textContent = l.t;
      txt.style.color = l.c;
    }}
    </script>
    """
    return base_page('Register', body)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please sign in to continue.', 'info')
        return redirect('/login')

    # Fetch fresh data from DB every page load
    cur = mysql.connection.cursor()
    cur.execute("SELECT username, email, created_at FROM users WHERE username = %s",
                (session['username'],))
    user = cur.fetchone()
    cur.close()

    if not user:
        session.clear()
        return redirect('/login')

    initial = user['username'][0].upper()
    joined  = str(user['created_at'])[:10]  # just the date part

    body = f"""
    {render_flashes()}
    <div class="welcome-banner">
      <div class="avatar">{initial}</div>
      <div class="welcome-text">
        <h3>Hello, {user['username']}!</h3>
        <p>You're logged in securely</p>
      </div>
    </div>
    <div class="arch-badge">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      Request traveled: Internet → Load Balancer → App VM → MySQL DB VM
    </div>
    <div class="info-grid">
      <div class="info-card">
        <div class="label">Username</div>
        <div class="value">{user['username']}</div>
      </div>
      <div class="info-card">
        <div class="label">Joined</div>
        <div class="value">{joined}</div>
      </div>
      <div class="info-card" style="grid-column: span 2;">
        <div class="label">Email</div>
        <div class="value">{user['email']}</div>
      </div>
    </div>
    <form method="POST" action="/logout">
      <button type="submit" class="btn-danger">Sign out</button>
    </form>
    """
    return base_page('Dashboard', body)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been signed out.', 'info')
    return redirect('/login')

# ── Health check — the Load Balancer pings this every 5 seconds ───────────────
# If this returns 200, the LB considers the VM healthy and sends traffic to it.
# If this fails 3 times, the LB stops sending traffic (your app is "down").
@app.route('/health')
def health():
    return {'status': 'healthy', 'tier': 'app-server', 'db': 'private-vpc'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
