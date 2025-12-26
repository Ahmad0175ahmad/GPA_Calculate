import os
from flask import Flask, render_template, request, redirect, url_for
from extensions import db
import pandas as pd

BASE_DIR = "/home"   # Azure writable path
DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)                   # ✅ db is now defined

from models import Student, Subject, Marks   # ✅ safe import


@app.route('/')
def home():
    return redirect(url_for('view_results'))


# ---------------- ADD STUDENT ----------------
@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        name = request.form['name']
        class_name = request.form['class_name']

        if not roll_no or not name:
            return "Roll No and Name required"

        student = Student(
            roll_no=roll_no,
            name=name,
            class_name=class_name
        )
        db.session.add(student)
        db.session.commit()
        return redirect(url_for('view_results'))

    return render_template('add_student.html')


# ---------------- ADD SUBJECT ----------------
@app.route('/add-subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        subject = Subject(
            subject_name=request.form['subject_name'],
            credit=int(request.form['credit'])
        )
        db.session.add(subject)
        db.session.commit()
        return redirect(url_for('add_subject'))

    return render_template('add_subject.html')


# ---------------- ADD MARKS ----------------
@app.route('/add-marks', methods=['GET', 'POST'])
def add_marks():
    students = Student.query.all()
    subjects = Subject.query.all()

    if request.method == 'POST':
        marks = int(request.form['marks'])

        if marks < 0 or marks > 100:
            return "Marks must be between 0 and 100"

        m = Marks(
            student_id=request.form['student_id'],
            subject_id=request.form['subject_id'],
            marks=marks
        )
        db.session.add(m)
        db.session.commit()
        return redirect(url_for('view_results'))

    return render_template(
        'add_marks.html',
        students=students,
        subjects=subjects
    )


# ---------------- GPA CALCULATION ----------------
def calculate_gpa(student_id):
    records = Marks.query.filter_by(student_id=student_id).all()
    total_points = 0
    total_credits = 0

    for r in records:
        subject = Subject.query.get(r.subject_id)
        grade_point = r.marks / 20
        total_points += grade_point * subject.credit
        total_credits += subject.credit

    if total_credits == 0:
        return 0

    return round(total_points / total_credits, 2)


# ---------------- VIEW RESULTS ----------------
@app.route('/results')
def view_results():
    students = Student.query.all()
    results = []

    for s in students:
        results.append({
            'roll_no': s.roll_no,
            'name': s.name,
            'class': s.class_name,
            'gpa': calculate_gpa(s.id)
        })

    return render_template('view_results.html', results=results)


# ---------------- EXPORT CSV ----------------
@app.route('/export')
def export_results():
    students = Student.query.all()
    data = []

    for s in students:
        data.append({
            'Roll No': s.roll_no,
            'Name': s.name,
            'Class': s.class_name,
            'GPA': calculate_gpa(s.id)
        })

    df = pd.DataFrame(data)

    csv_path = os.path.join("/home", "results.csv")
    df.to_csv(csv_path, index=False)

    return "Results exported successfully"


if __name__ == "__main__":
    app.run()