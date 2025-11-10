import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')

# In-memory store (demo purposes)
workouts = []  # [{"workout": str, "duration": int}]


@app.route('/', methods=['GET'])
def index():
    total = sum(w['duration'] for w in workouts)
    return render_template('index.html', workouts=workouts, total=total)


@app.route('/add', methods=['POST'])
def add():
    workout = request.form.get('workout', '').strip()
    duration = request.form.get('duration', '').strip()
    if not workout or not duration:
        return redirect(url_for('index'))
    try:
        duration_i = int(duration)
    except ValueError:
        return redirect(url_for('index'))
    workouts.append({"workout": workout, "duration": duration_i})
    return redirect(url_for('index'))


@app.route('/clear', methods=['POST'])
def clear():
    workouts.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

