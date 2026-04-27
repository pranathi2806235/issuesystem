from flask import Flask, render_template_string, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret123'

# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect('issues.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------- FRONTEND --------
html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Issue System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container mt-5">

<h1 class="text-center mb-4">🚧 Issue Reporting System</h1>

{% if not session.get('user') %}
<div class="card p-4 mx-auto" style="max-width:400px;">
    <h4 class="text-center">Login</h4>
    <form method="POST" action="/login">
        <input class="form-control mb-2" name="username" placeholder="Username" required>
        <input class="form-control mb-3" type="password" name="password" placeholder="Password" required>
        <button class="btn btn-primary w-100">Login</button>
    </form>
</div>

{% else %}

<div class="d-flex justify-content-between mb-3">
    <h5>Welcome {{session.get('user')}}</h5>
    <a href="/logout" class="btn btn-danger btn-sm">Logout</a>
</div>

<div class="card p-3 mb-4">
    <form method="POST" action="/add">
        <div class="row">
            <div class="col-md-4">
                <input class="form-control" name="title" placeholder="Issue Title" required>
            </div>
            <div class="col-md-6">
                <input class="form-control" name="description" placeholder="Description" required>
            </div>
            <div class="col-md-2">
                <button class="btn btn-success w-100">Add</button>
            </div>
        </div>
    </form>
</div>

<h3>Issues</h3>

<div class="row">
{% for issue in issues %}
<div class="col-md-6">
    <div class="card mb-3 shadow">
        <div class="card-body">
            <h5>{{issue[1]}}</h5>
            <p>{{issue[2]}}</p>

            <span class="badge bg-{{'success' if issue[3]=='Resolved' else 'warning'}}">
                {{issue[3]}}
            </span>

            <div class="mt-3">
                <form action="/delete/{{issue[0]}}" method="post" style="display:inline;">
                    <button class="btn btn-outline-danger btn-sm">Delete</button>
                </form>

                <form action="/toggle/{{issue[0]}}" method="post" style="display:inline;">
                    <button class="btn btn-outline-primary btn-sm">Toggle</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endfor %}
</div>

{% endif %}

</div>
</body>
</html>
'''

# -------- ROUTES --------
@app.route('/')
def home():
    conn = sqlite3.connect('issues.db')
    c = conn.cursor()
    c.execute('SELECT * FROM issues')
    data = c.fetchall()
    conn.close()
    return render_template_string(html, issues=data)

@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] == 'admin' and request.form['password'] == '1234':
        session['user'] = 'admin'
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/add', methods=['POST'])
def add():
    conn = sqlite3.connect('issues.db')
    c = conn.cursor()
    c.execute(
        'INSERT INTO issues (title, description, status) VALUES (?, ?, ?)',
        (request.form['title'], request.form['description'], 'Pending')
    )
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = sqlite3.connect('issues.db')
    c = conn.cursor()
    c.execute('DELETE FROM issues WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/toggle/<int:id>', methods=['POST'])
def toggle(id):
    conn = sqlite3.connect('issues.db')
    c = conn.cursor()

    c.execute('SELECT status FROM issues WHERE id=?', (id,))
    status = c.fetchone()

    if status:
        new_status = 'Resolved' if status[0] == 'Pending' else 'Pending'
        c.execute('UPDATE issues SET status=? WHERE id=?', (new_status, id))

    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == "__main__":
    app.run() 