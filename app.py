from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText

# ---------------- APP SETUP ----------------
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    comments = db.relationship(
        "Comment",
        backref="todo",
        cascade="all, delete-orphan"
    )

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    todo_id = db.Column(db.Integer, db.ForeignKey("todo.id"), nullable=False)

# ---------------- ROUTES ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        title = request.form.get("title")
        if title and title.strip():
            todo = Todo(title=title)
            db.session.add(todo)
            db.session.commit()
        return redirect("/")

    todos = Todo.query.all()
    return render_template("index.html", todos=todos)

@app.route("/complete/<int:todo_id>")
def complete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.completed = not todo.completed
    db.session.commit()
    return redirect("/")

@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return redirect("/")

@app.route("/comment/<int:todo_id>", methods=["POST"])
def add_comment(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    content = request.form.get("content")

    if content and content.strip():
        comment = Comment(content=content, todo=todo)
        db.session.add(comment)
        db.session.commit()

    return redirect("/")

# ---------------- EMAIL FUNCTION ----------------
def send_email_reminder(todo):
    sender_email = "YOUR_EMAIL@gmail.com"
    sender_password = "YOUR_APP_PASSWORD"
    recipient_email = "YOUR_EMAIL@gmail.com"

    msg = MIMEText(f"Don't forget your todo:\n\n{todo.title}")
    msg["Subject"] = f"Reminder: {todo.title}"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Reminder sent: {todo.title}")

    except Exception as e:
        print("❌ Email failed:", e)

# ---------------- SCHEDULER JOB ----------------
def check_todos_for_reminder():
    with app.app_context():
        todos = Todo.query.all()
        for todo in todos:
            if not todo.completed:
                send_email_reminder(todo)

# ---------------- SCHEDULER SETUP ----------------
scheduler = BackgroundScheduler()
scheduler.add_job(
    check_todos_for_reminder,
    trigger="interval",
    minutes=1
)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        scheduler.start()

    app.run(debug=True)
