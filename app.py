from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Email config (set in Render environment variables)
EMAIL = os.getenv("GMAIL_ADDRESS")
PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    needs_reminder = db.Column(db.Boolean, default=True)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Pending")  # Pending/Confirmed

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form["title"]
        message = request.form["message"]
        needs_reminder = "reminder" in request.form  # Checkbox
        deadline = datetime.strptime(request.form["deadline"], "%Y-%m-%d") if request.form["deadline"] else None
        
        notice = Notice(
            title=title,
            message=message,
            needs_reminder=needs_reminder,
            deadline=deadline
        )
        db.session.add(notice)
        db.session.commit()
        
        # Send emails (simplified; expand with Student table)
        send_emails(notice)
        return redirect(url_for("index"))
    
    notices = Notice.query.all()
    return render_template("index.html", notices=notices)

def send_emails(notice):
    students = Student.query.all()  # Pretend we have 65 students
    for student in students:
        msg = MIMEText(f"""
        Hi {student.name},
        
        New notice: {notice.title}
        Message: {notice.message}
        
        Deadline: {notice.deadline or "ASAP"}
        
        ✅ Confirm here: {url_for("confirm", notice_id=notice.id, student_id=student.id, _external=True)}
        """)
        msg["Subject"] = f"📢 {notice.title}"
        msg["From"] = EMAIL
        msg["To"] = student.email
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, [student.email], msg.as_string())

@app.route("/confirm/<int:notice_id>/<int:student_id>")
def confirm(notice_id, student_id):
    notice = Notice.query.get(notice_id)
    notice.status = "Confirmed"
    db.session.commit()
    return "✅ Thanks for confirming!"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables
    app.run(debug=True)
