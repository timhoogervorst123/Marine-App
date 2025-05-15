from flask import Flask, render_template, request, redirect, session, url_for
import json
import os

app = Flask(__name__)
app.secret_key = 'marine_secret_key'

TASKS_FILE = 'data/tasks.json'
STUDENTS_FILE = 'data/students.json'


# Functies om studenten te laden en op te slaan
def load_students():
    if not os.path.exists(STUDENTS_FILE):
        return {}
    with open(STUDENTS_FILE, 'r') as f:
        return json.load(f)

def save_students(students_data):
    with open(STUDENTS_FILE, 'w') as f:
        json.dump(students_data, f, indent=4)


# Geregistreerde studenten laden
students = load_students()
if not students:
    students = {
        'Tim': {'password': 'Hoogervorst'},
        'Thom': {'password': 'Zonneveld'},
        'Sem': {'password': 'Sit'}
    }
    save_students(students)


# Taken per student laden
def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}
    with open(TASKS_FILE, 'r') as f:
        return json.load(f)

# Taken opslaan
def save_tasks(all_tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(all_tasks, f, indent=4)


# Inlogscherm
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == '12345':
            session['user'] = 'admin'
            return redirect(url_for('dashboard_admin'))

        elif username in students and password == students[username]['password']:
            session['user'] = username
            return redirect(url_for('dashboard_student'))

        else:
            return render_template('login.html', error='Ongeldige inloggegevens')

    return render_template('login.html')


# Begeleidersdashboard
@app.route('/dashboard_admin')
def dashboard_admin():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))

    tasks = load_tasks()
    progress_data = {}

    for student in students:
        progress_data[student] = {
            'Nog niet begonnen': 0,
            'Bezig': 0,
            'Gehaald': 0
        }
        for task in tasks.get(student, []):
            if task['status'] in progress_data[student]:
                progress_data[student][task['status']] += 1

    return render_template('dashboard_admin_overview.html', students=students.keys(), progress_data=progress_data)


# Begeleider kan taken van een student beheren
@app.route('/student/<student_name>', methods=['GET', 'POST'])
def student_detail(student_name):
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))

    tasks = load_tasks()
    student_tasks = tasks.get(student_name, [])

    if request.method == 'POST':
        if 'update_status' in request.form:
            task_id = int(request.form['task_id'])
            new_status = request.form['new_status']
            for task in student_tasks:
                if task['id'] == task_id:
                    task['status'] = new_status

        elif 'delete_task' in request.form:
            task_id = int(request.form['task_id'])
            student_tasks = [task for task in student_tasks if task['id'] != task_id]

        tasks[student_name] = student_tasks
        save_tasks(tasks)

    return render_template('dashboard_admin_student_detail.html', student=student_name, tasks=student_tasks)


# Studenten-dashboard
@app.route('/dashboard_student')
def dashboard_student():
    user = session.get('user')
    if user not in students:
        return redirect(url_for('login'))

    all_tasks = load_tasks()
    student_tasks = all_tasks.get(user, [])

    progress_data = {
        'Nog niet begonnen': sum(1 for t in student_tasks if t['status'] == 'Nog niet begonnen'),
        'Bezig': sum(1 for t in student_tasks if t['status'] == 'Bezig'),
        'Gehaald': sum(1 for t in student_tasks if t['status'] == 'Gehaald')
    }

    return render_template('dashboard_student.html', tasks=student_tasks, student=user, progress=progress_data)


# Studentenpagina met extra informatie
@app.route('/student_info')
def student_info():
    user = session.get('user')
    if user not in students:
        return redirect(url_for('login'))
    return render_template('student_info.html', student=user)


# Student Toevoegen
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))

    message = None

    if request.method == 'POST':
        new_student = request.form['student_name']
        new_password = request.form['student_password']

        if new_student not in students:
            students[new_student] = {'password': new_password}
            save_students(students)

            tasks = load_tasks()
            tasks[new_student] = []
            save_tasks(tasks)

            message = f"✅ Student {new_student} is succesvol toegevoegd!"
        else:
            message = f"⚠️ Student {new_student} bestaat al!"

        return render_template('add_student.html', message=message)

    return render_template('add_student.html')


# Student Verwijderen
@app.route('/remove_student', methods=['POST'])
def remove_student():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))

    student_to_remove = request.form['student_name']
    if student_to_remove in students:
        students.pop(student_to_remove)
        save_students(students)

        tasks = load_tasks()
        if student_to_remove in tasks:
            tasks.pop(student_to_remove)
            save_tasks(tasks)

        message = f"✅ Student {student_to_remove} is verwijderd."
    else:
        message = f"⚠️ Student {student_to_remove} bestaat niet."

    return redirect(url_for('dashboard_admin'))


# Uitloggen
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(TASKS_FILE):
        save_tasks({})
    if not os.path.exists(STUDENTS_FILE):
        save_students(students)
    app.run(debug=True)
