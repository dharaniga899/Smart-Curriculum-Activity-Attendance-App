from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = 'smart_attendance_secret_2024'
DB_PATH = 'school.db'


# ── DB helper ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and seed demo data if DB does not exist."""
    if os.path.exists(DB_PATH):
        return
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            role      TEXT NOT NULL DEFAULT 'student'
        );

        CREATE TABLE IF NOT EXISTS students (
            student_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            email        TEXT UNIQUE NOT NULL,
            department   TEXT,
            year         INTEGER,
            user_id      INTEGER REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS courses (
            course_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            department  TEXT
        );

        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      INTEGER REFERENCES students(student_id),
            course_id       INTEGER REFERENCES courses(course_id),
            attendance_date TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'Present'
        );

        CREATE TABLE IF NOT EXISTS activities (
            activity_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_name TEXT NOT NULL,
            activity_date TEXT NOT NULL,
            description   TEXT,
            category      TEXT DEFAULT 'Academic'
        );

        CREATE TABLE IF NOT EXISTS student_activities (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id           INTEGER REFERENCES students(student_id),
            activity_id          INTEGER REFERENCES activities(activity_id),
            participation_status TEXT DEFAULT 'Registered'
        );
    """)

    # ── Seed demo data ──────────────────────────────────────────────────────────
    # Users
    c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)",
              ('dharani@college.edu', 'pass123', 'student'))
    c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)",
              ('priya@college.edu', 'pass123', 'student'))
    c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)",
              ('ravi@college.edu', 'pass123', 'student'))

    # Students
    c.execute("INSERT INTO students (student_name,email,department,year,user_id) VALUES (?,?,?,?,?)",
              ('Dharaniga V.R.', 'dharani@college.edu', 'AI & ML', 3, 1))
    c.execute("INSERT INTO students (student_name,email,department,year,user_id) VALUES (?,?,?,?,?)",
              ('Priya S.', 'priya@college.edu', 'AI & ML', 3, 2))
    c.execute("INSERT INTO students (student_name,email,department,year,user_id) VALUES (?,?,?,?,?)",
              ('Ravi K.', 'ravi@college.edu', 'AI & ML', 3, 3))

    # Courses
    courses = [
        ('Machine Learning', 'AI & ML'),
        ('Deep Learning', 'AI & ML'),
        ('Data Structures', 'AI & ML'),
        ('Python Programming', 'AI & ML'),
        ('Database Systems', 'AI & ML'),
    ]
    c.executemany("INSERT INTO courses (course_name, department) VALUES (?,?)", courses)

    # Attendance records (June 2026 sample data)
    attendance_data = []
    dates = ['2026-06-02','2026-06-03','2026-06-04','2026-06-05','2026-06-06',
             '2026-06-09','2026-06-10','2026-06-11','2026-06-12','2026-06-13',
             '2026-06-16','2026-06-17','2026-06-18','2026-06-19','2026-06-20',
             '2026-06-23','2026-06-24','2026-06-25','2026-06-26','2026-06-27']
    statuses = {
        1: ['Present','Present','Present','Absent','Present','Present','Present','Absent','Present','Present',
            'Present','Present','Present','Present','Absent','Present','Present','Present','Present','Present'],
        2: ['Present','Absent','Present','Present','Present','Present','Absent','Present','Present','Present',
            'Present','Present','Absent','Present','Present','Present','Present','Present','Absent','Present'],
        3: ['Present','Present','Absent','Present','Present','Absent','Present','Present','Present','Absent',
            'Present','Present','Present','Present','Present','Present','Absent','Present','Present','Present'],
    }
    for sid in [1, 2, 3]:
        for cid in range(1, 6):
            for i, d in enumerate(dates):
                st = statuses[sid][i] if i < len(statuses[sid]) else 'Present'
                attendance_data.append((sid, cid, d, st))
    c.executemany("INSERT INTO attendance (student_id,course_id,attendance_date,status) VALUES (?,?,?,?)",
                  attendance_data)

    # Activities
    activities = [
        ('Hackathon 2026',     '2026-06-15', 'Inter-college coding hackathon — 24 hrs.',   'Technical'),
        ('AI Workshop',        '2026-06-10', 'Hands-on workshop on Neural Networks.',       'Academic'),
        ('Sports Day',         '2026-06-20', 'Annual college sports event.',                'Sports'),
        ('Project Expo',       '2026-06-28', 'Final year project exhibition.',              'Academic'),
        ('Cultural Fest',      '2026-06-22', 'Annual cultural celebration event.',          'Cultural'),
        ('Resume Workshop',    '2026-06-18', 'Career development and resume tips.',         'Career'),
    ]
    c.executemany("INSERT INTO activities (activity_name,activity_date,description,category) VALUES (?,?,?,?)",
                  activities)

    # Student activities participation
    participations = [
        (1, 1, 'Participated'), (1, 2, 'Participated'), (1, 4, 'Registered'),
        (2, 1, 'Participated'), (2, 3, 'Participated'), (2, 5, 'Participated'),
        (3, 2, 'Participated'), (3, 6, 'Registered'),
    ]
    c.executemany("INSERT INTO student_activities (student_id,activity_id,participation_status) VALUES (?,?,?)",
                  participations)

    conn.commit()
    conn.close()


# ── Auth helpers ───────────────────────────────────────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def get_current_student():
    conn = get_db()
    student = conn.execute(
        "SELECT * FROM students WHERE user_id=?", (session['user_id'],)
    ).fetchone()
    conn.close()
    return student


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (email, password)
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid email or password. Please try again.'
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        dept  = request.form.get('department', '').strip()
        year  = request.form.get('year', '1')
        pwd   = request.form.get('password', '').strip()
        cpwd  = request.form.get('confirm_password', '').strip()

        if pwd != cpwd:
            error = 'Passwords do not match.'
        elif not all([name, email, dept, pwd]):
            error = 'All fields are required.'
        else:
            try:
                conn = get_db()
                c = conn.cursor()
                c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                          (email, pwd, 'student'))
                uid = c.lastrowid
                c.execute(
                    "INSERT INTO students (student_name,email,department,year,user_id) VALUES (?,?,?,?,?)",
                    (name, email, dept, int(year), uid)
                )
                conn.commit()
                conn.close()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                error = 'An account with this email already exists.'

    return render_template('register.html', error=error)


@app.route('/dashboard')
@login_required
def dashboard():
    student = get_current_student()
    conn = get_db()

    # Attendance summary
    total = conn.execute(
        "SELECT COUNT(*) as c FROM attendance WHERE student_id=?", (student['student_id'],)
    ).fetchone()['c']
    present = conn.execute(
        "SELECT COUNT(*) as c FROM attendance WHERE student_id=? AND status='Present'",
        (student['student_id'],)
    ).fetchone()['c']
    pct = round((present / total * 100) if total else 0, 1)

    # Activities count
    act_count = conn.execute(
        "SELECT COUNT(*) as c FROM student_activities WHERE student_id=?",
        (student['student_id'],)
    ).fetchone()['c']

    # Courses
    courses = conn.execute("SELECT * FROM courses WHERE department=?",
                           (student['department'],)).fetchall()

    # Recent attendance (last 5)
    recent = conn.execute("""
        SELECT a.attendance_date, a.status, c.course_name
        FROM attendance a JOIN courses c ON a.course_id=c.course_id
        WHERE a.student_id=?
        ORDER BY a.attendance_date DESC LIMIT 5
    """, (student['student_id'],)).fetchall()

    # Upcoming activities
    today = date.today().isoformat()
    upcoming = conn.execute("""
        SELECT * FROM activities WHERE activity_date >= ? ORDER BY activity_date LIMIT 3
    """, (today,)).fetchall()

    conn.close()
    return render_template('dashboard.html',
                           student=student, pct=pct, present=present,
                           total=total, act_count=act_count,
                           courses=courses, recent=recent, upcoming=upcoming)


@app.route('/attendance')
@login_required
def attendance():
    student = get_current_student()
    conn = get_db()

    selected_course = request.args.get('course', 'all')
    courses = conn.execute("SELECT * FROM courses WHERE department=?",
                           (student['department'],)).fetchall()

    if selected_course == 'all':
        records = conn.execute("""
            SELECT a.attendance_date, a.status, c.course_name, c.course_id
            FROM attendance a JOIN courses c ON a.course_id=c.course_id
            WHERE a.student_id=?
            ORDER BY a.attendance_date DESC
        """, (student['student_id'],)).fetchall()
    else:
        records = conn.execute("""
            SELECT a.attendance_date, a.status, c.course_name, c.course_id
            FROM attendance a JOIN courses c ON a.course_id=c.course_id
            WHERE a.student_id=? AND a.course_id=?
            ORDER BY a.attendance_date DESC
        """, (student['student_id'], selected_course)).fetchall()

    total = len(records)
    present = sum(1 for r in records if r['status'] == 'Present')
    absent  = total - present
    pct     = round((present / total * 100) if total else 0, 1)

    conn.close()
    return render_template('attendance.html',
                           student=student, records=records, courses=courses,
                           selected_course=selected_course,
                           total=total, present=present, absent=absent, pct=pct)


@app.route('/activities')
@login_required
def activities():
    student = get_current_student()
    conn = get_db()

    all_activities = conn.execute("SELECT * FROM activities ORDER BY activity_date").fetchall()
    my_ids = {row['activity_id'] for row in conn.execute(
        "SELECT activity_id FROM student_activities WHERE student_id=?",
        (student['student_id'],)
    ).fetchall()}

    conn.close()
    return render_template('activities.html',
                           student=student, activities=all_activities, my_ids=my_ids)


@app.route('/activities/join/<int:act_id>', methods=['POST'])
@login_required
def join_activity(act_id):
    student = get_current_student()
    conn = get_db()
    exists = conn.execute(
        "SELECT id FROM student_activities WHERE student_id=? AND activity_id=?",
        (student['student_id'], act_id)
    ).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO student_activities (student_id,activity_id,participation_status) VALUES (?,?,?)",
            (student['student_id'], act_id, 'Registered')
        )
        conn.commit()
    conn.close()
    flash('Successfully registered for activity!', 'success')
    return redirect(url_for('activities'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    student = get_current_student()
    conn = get_db()
    success = None
    error   = None

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        dept = request.form.get('department', '').strip()
        year = request.form.get('year', '1')
        try:
            conn.execute(
                "UPDATE students SET student_name=?, department=?, year=? WHERE student_id=?",
                (name, dept, int(year), student['student_id'])
            )
            conn.commit()
            success = 'Profile updated successfully!'
            student = get_current_student()
        except Exception as e:
            error = f'Update failed: {e}'

    my_activities = conn.execute("""
        SELECT ac.activity_name, ac.activity_date, sa.participation_status
        FROM student_activities sa JOIN activities ac ON sa.activity_id=ac.activity_id
        WHERE sa.student_id=?
        ORDER BY ac.activity_date DESC
    """, (student['student_id'],)).fetchall()

    conn.close()
    return render_template('profile.html',
                           student=student, my_activities=my_activities,
                           success=success, error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
