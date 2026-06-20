from flask import Flask, render_template

app = Flask(__name__)

students = [
    {"id": 1, "name": "Arun", "attendance": "Present"},
    {"id": 2, "name": "Priya", "attendance": "Absent"},
    {"id": 3, "name": "Rahul", "attendance": "Present"}
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', students=students)

if __name__ == '__main__':
    app.run(debug=True)
