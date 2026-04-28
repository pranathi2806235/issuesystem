from flask import Flask, render_template_string, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key"

MANAGER_SECRET = "manager123"

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("issues.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        status TEXT,
        created_by TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- AUTH UI ----------------
auth_ui = '''
<!DOCTYPE html>
<html>
<head>
<title>Issue System</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
body {
    font-family:Segoe UI;
    background: linear-gradient(135deg,#667eea,#764ba2);
    height:100vh;
}

.glass {
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(12px);
    padding:25px;
    border-radius:20px;
    color:white;
    box-shadow:0 10px 30px rgba(0,0,0,0.2);
}

.btn:hover { transform:scale(1.05); }
</style>
</head>

<body>

<div class="container d-flex flex-column justify-content-center align-items-center h-100">

<h2 class="text-white mb-4">🚧 Issue Tracking System</h2>

{% with messages = get_flashed_messages() %}
{% if messages %}
<div class="alert alert-warning w-50 text-center">
{% for m in messages %} {{m}} <br> {% endfor %}
</div>
{% endif %}
{% endwith %}

<div class="row w-100 justify-content-center">

<div class="col-md-5">
<div class="glass">
<h4>Login</h4>
<form method="POST" action="/login">
<input class="form-control mb-2" name="username" placeholder="Username" required>
<input class="form-control mb-3" type="password" name="password" placeholder="Password" required>
<button class="btn btn-light w-100">Login</button>
</form>
</div>
</div>

<div class="col-md-5">
<div class="glass">
<h4>Register</h4>
<form method="POST" action="/register">
<input class="form-control mb-2" name="username" placeholder="Username" required>
<input class="form-control mb-2" type="password" name="password" placeholder="Password" required>

<select class="form-control mb-2" name="role">
<option value="worker">Worker</option>
<option value="manager">Manager</option>
</select>

<input class="form-control mb-3" name="secret" placeholder="Manager Secret">
<button class="btn btn-success w-100">Register</button>
</form>
</div>
</div>

</div>
</div>

</body>
</html>
'''

# ---------------- WORKER ----------------
worker_ui = '''
<!DOCTYPE html>
<html>
<head>
<title>Worker</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
body { background:#f5f7ff; font-family:Segoe UI; }
.card { border-radius:15px; box-shadow:0 5px 15px rgba(0,0,0,0.1); }
.navbar { background:linear-gradient(90deg,#4facfe,#00f2fe); }
</style>
</head>

<body>

<nav class="navbar px-4 text-white d-flex justify-content-between">
<h5>👷 Worker Dashboard</h5>
<a href="/logout" class="btn btn-light btn-sm">Logout</a>
</nav>

<div class="container mt-4">

<h4>Welcome {{session['user']}}</h4>

<div class="card p-3 mt-3">
<form method="POST" action="/add">
<input class="form-control mb-2" name="title" placeholder="Title">
<input class="form-control mb-2" name="description" placeholder="Description">
<button class="btn btn-primary w-100">Add Issue</button>
</form>
</div>

<h5 class="mt-4">Your Issues</h5>

{% for i in issues %}
<div class="card p-3 mt-2">
<b>{{i['title']}}</b>
<p>{{i['description']}}</p>
<span class="badge bg-{{'success' if i['status']=='Resolved' else 'warning'}}">
{{i['status']}}
</span>
</div>
{% endfor %}

</div>

</body>
</html>
'''

# ---------------- MANAGER (WOW UI) ----------------
manager_ui = '''
<!DOCTYPE html>
<html>
<head>
<title>Manager</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
body { background:#eef2ff; font-family:Segoe UI; }
.card { border-radius:15px; box-shadow:0 5px 15px rgba(0,0,0,0.1); }
.navbar { background:linear-gradient(90deg,#667eea,#764ba2); color:white; }
.glass {
    background:white;
    padding:15px;
    border-radius:15px;
    box-shadow:0 5px 15px rgba(0,0,0,0.08);
}
</style>
</head>

<body>

<nav class="navbar px-4 d-flex justify-content-between">
<h5>🧑‍💼 Manager Panel</h5>
<div>
<a href="/analytics" class="btn btn-warning btn-sm">📊 Analytics</a>
<a href="/logout" class="btn btn-light btn-sm">Logout</a>
</div>
</nav>

<div class="container mt-3">

<div class="glass mb-3">
<form method="GET" class="row g-2">

<div class="col-md-6">
<input class="form-control" name="search" value="{{search}}" placeholder="🔍 Search issues">
</div>

<div class="col-md-3">
<select class="form-control" name="status">
<option value="All">All</option>
<option value="Pending">Pending</option>
<option value="Resolved">Resolved</option>
</select>
</div>

<div class="col-md-3">
<button class="btn btn-primary w-100">Filter</button>
</div>

</form>
</div>

<h4>All Issues</h4>

{% for i in issues %}
<div class="card p-3 mt-3">
<b>{{i['title']}}</b>
<p>{{i['description']}} | By {{i['created_by']}}</p>

<span class="badge bg-{{'success' if i['status']=='Resolved' else 'warning'}}">
{{i['status']}}
</span>

<div class="mt-2">
<form method="POST" action="/toggle/{{i['id']}}" style="display:inline;">
<button class="btn btn-primary btn-sm">Toggle</button>
</form>

<form method="POST" action="/delete/{{i['id']}}" style="display:inline;">
<button class="btn btn-danger btn-sm">Delete</button>
</form>
</div>

</div>
{% endfor %}

</div>

</body>
</html>
'''

# ---------------- ANALYTICS ----------------
analytics_ui = '''
<!DOCTYPE html>
<html>
<head>
<title>Analytics</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body { background:#f4f6ff; font-family:Segoe UI; }
.card { border-radius:15px; box-shadow:0 5px 15px rgba(0,0,0,0.1); }
</style>
</head>

<body>

<div class="container mt-4">

<a href="/manager" class="btn btn-dark mb-3">⬅ Back</a>

<h3>📊 Analytics Dashboard</h3>

<div class="row text-center">

<div class="col-md-4"><div class="card p-3"><h5>Total</h5><h3>{{total}}</h3></div></div>
<div class="col-md-4"><div class="card p-3"><h5>Pending</h5><h3>{{pending}}</h3></div></div>
<div class="col-md-4"><div class="card p-3"><h5>Resolved</h5><h3>{{resolved}}</h3></div></div>

</div>

<div class="card mt-4 p-4">
<canvas id="chart"></canvas>
</div>

</div>

<script>
new Chart(document.getElementById("chart"),{
type:"doughnut",
data:{
labels:["Pending","Resolved"],
datasets:[{
data:[{{pending}},{{resolved}}],
backgroundColor:["orange","green"]
}]
}
});
</script>

</body>
</html>
'''

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(auth_ui)
    return redirect('/manager' if session['role']=='manager' else '/worker')

@app.route('/register', methods=['POST'])
def register():
    u = request.form['username'].strip().lower()
    p = request.form['password']
    r = request.form['role']
    s = request.form.get('secret','')

    if not u or not p:
        flash("Empty fields not allowed")
        return redirect('/')

    if r == 'manager' and s != MANAGER_SECRET:
        flash("Wrong manager secret")
        return redirect('/')

    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                  (u, generate_password_hash(p), r))
        conn.commit()
    except:
        flash("User already exists")
        return redirect('/')

    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=?",
              (request.form['username'].strip().lower(),))
    u = c.fetchone()

    if u and check_password_hash(u['password'], request.form['password']):
        session['user'] = u['username']
        session['role'] = u['role']
        return redirect('/')

    flash("Invalid login")
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/worker')
def worker():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM issues WHERE created_by=?", (session['user'],))
    issues = c.fetchall()
    return render_template_string(worker_ui, issues=issues)

@app.route('/manager')
def manager():
    search = request.args.get('search','')
    status = request.args.get('status','All')

    conn = get_db()
    c = conn.cursor()

    query = "SELECT * FROM issues WHERE 1=1"
    params = []

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if status != "All":
        query += " AND status=?"
        params.append(status)

    c.execute(query, params)
    issues = c.fetchall()

    return render_template_string(manager_ui, issues=issues, search=search, status=status)

@app.route('/add', methods=['POST'])
def add():
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO issues VALUES (NULL,?,?,?,?)",
              (request.form['title'], request.form['description'], 'Pending', session['user']))
    conn.commit()
    return redirect('/worker')

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM issues WHERE id=?", (id,))
    conn.commit()
    return redirect('/manager')

@app.route('/toggle/<int:id>', methods=['POST'])
def toggle(id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT status FROM issues WHERE id=?", (id,))
    s = c.fetchone()

    if s:
        new = "Resolved" if s['status']=="Pending" else "Pending"
        c.execute("UPDATE issues SET status=? WHERE id=?", (new,id))

    conn.commit()
    return redirect('/manager')

@app.route('/analytics')
def analytics():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM issues")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM issues WHERE status='Pending'")
    pending = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM issues WHERE status='Resolved'")
    resolved = c.fetchone()[0]

    return render_template_string(analytics_ui,
        total=total, pending=pending, resolved=resolved)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)