import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")

# In-memory store
entries = []  # [{"category": str, "exercise": str, "duration": int}]


def _parse_duration(value: str) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


@app.route("/", methods=["GET"])
def index():
    total = sum(e["duration"] for e in entries)
    return render_template("index.html", entries=entries, total=total)


@app.route("/add", methods=["POST"])
def add():
    category = (request.form.get("category", "").strip() or None)
    exercise = (request.form.get("exercise", "").strip() or None)
    duration_raw = request.form.get("duration", "").strip()
    duration = _parse_duration(duration_raw)
    if not category or not exercise or duration is None:
        return redirect(url_for("index"))
    # V1.1 accepts any integer, including negatives
    entries.append({"category": category, "exercise": exercise, "duration": duration})
    return redirect(url_for("index"))


@app.route("/clear", methods=["POST"])
def clear():
    entries.clear()
    return redirect(url_for("index"))


@app.route("/summary", methods=["GET"])
def summary():
    total = sum(e["duration"] for e in entries)
    return f"Total sessions: {len(entries)}, Total duration: {total}"


if __name__ == "__main__":
    app.run(debug=True)

