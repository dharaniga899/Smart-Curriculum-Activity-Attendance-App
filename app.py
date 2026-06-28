from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    students = [
        {"id": 1, "name": "Dharani", "attendance": "95%"},
        {"id": 2, "name": "Priya", "attendance": "90%"}
    ]
    return render_template('dashboard.html', students=students)

@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
