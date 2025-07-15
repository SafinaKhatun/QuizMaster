from flask import Flask, render_template, request, redirect, url_for, session,flash
import models
import sqlite3
from collections import defaultdict
import calendar
from werkzeug.security import generate_password_hash, check_password_hash
 
import time
import datetime
from datetime import datetime
from models import get_questions
from models import get_all_subjects
from models import get_chapter_question_count 
 
from models import create_tables 
import sqlite3
 
app = Flask(__name__)
app.secret_key ='super_secret_key'
 
create_tables()

def get_db_connection():
    conn = sqlite3.connect('instance/quiz_master.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return redirect(url_for('login'))
 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username= request.form['username']
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        qualification = request.form.get('qualification', '')
        dob = request.form.get('dob', '')
 
        con = sqlite3.connect('instance/quiz_master.db')
        cur = con.cursor()
 
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = cur.fetchone()
        if existing_user:
            flash('Email already exists! Try logging in.')
            con.close()
            return redirect(url_for('login'))
 
        cur.execute("INSERT INTO users (username, full_name, email, password, qualification, dob) VALUES (?, ?, ?, ?, ?, ?)",
                    (username, full_name, email,  password, qualification, dob))
        con.commit()
        con.close()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        con = sqlite3.connect('instance/quiz_master.db')
        cur = con.cursor()
 
        cur.execute('SELECT id, email FROM admins WHERE email=? AND password=?', (email, password))
        admin = cur.fetchone()

        if admin:
            session['admin_id'] = admin[0]   
            session['admin_email'] = admin[1]
            con.close()
            return redirect(url_for('admin_dashboard'))
 
        cur.execute('SELECT id, username, password FROM users WHERE email=?', (email,))  
        user = cur.fetchone()
        con.close()
        
        if user:
            stored_password = user[2]  
             
            if password == stored_password:   
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                return redirect(url_for('user_dashboard'))
            else:
                flash('Incorrect password! Please try again.', 'error')
        else:
            flash('Email not found! Please register first.', 'error')

    return render_template('login.html')

        
from flask import g
DATABASE = "instance/quiz_master.db"
def get_db():
    """Connect to SQLite3 Database"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  
    return db

@app.teardown_appcontext
def close_connection(_):
    """Close SQLite3 Database Connection"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect('instance/quiz_master.db')
    conn.row_factory = sqlite3.Row  
    cur = conn.cursor()
 
    cur.execute("""
        SELECT quizzes.id, quizzes.name, COUNT(questions.id) AS num_questions, 
               quizzes.date_of_quiz, quizzes.time_duration
        FROM quizzes
        LEFT JOIN questions ON quizzes.id = questions.quiz_id
        GROUP BY quizzes.id
        ORDER BY date_of_quiz ASC
    """)
    quizzes = cur.fetchall()
    conn.close()

    return render_template('user_dashboard.html', username=session['user_name'], quizzes=quizzes)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():

    conn = sqlite3.connect('instance/quiz_master.db')
    conn.row_factory = sqlite3.Row   
    cur = conn.cursor()
 
    cur.execute('SELECT id, name FROM subjects')
    subjects = cur.fetchall()

    subject_data = []
    for subj in subjects:
        subject_id = subj['id']
        subject_name = subj['name']
 
        cur.execute('SELECT id, name FROM chapters WHERE subject_id = ?', (subject_id,))
        chapters = cur.fetchall()

        chapter_list = []
        for chapter in chapters:
            chapter_id = chapter['id']
            chapter_name = chapter['name']
 
            cur.execute('SELECT COUNT(*) FROM questions WHERE quiz_id IN (SELECT id FROM quizzes WHERE chapter_id = ?)', (chapter_id,))
            question_count = cur.fetchone()[0]

            chapter_list.append({
                'id': chapter_id,
                'name': chapter_name,
                'question_count': question_count
            })

        subject_data.append({
            'id': subject_id,
            'name': subject_name,
            'chapters': chapter_list
        })

    conn.close()   

    return render_template('admin_dashboard.html', subjects=subject_data)

@app.route('/admin/search', methods=['POST'])
def admin_search():
    search_query = request.form.get('search_query', '').strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute("SELECT id, full_name, username FROM users WHERE full_name LIKE ? OR username LIKE ?", 
                   (f"%{search_query}%", f"%{search_query}%"))
    users = cursor.fetchall()
 
    cursor.execute("SELECT id, name FROM subjects WHERE name LIKE ?", (f"%{search_query}%",))
    subjects = cursor.fetchall()
 
    cursor.execute("""
        SELECT quizzes.id, COUNT(questions.id) as num_questions, quizzes.date_of_quiz, chapters.name as chapter_name
        FROM quizzes
        LEFT JOIN questions ON quizzes.id = questions.quiz_id
        INNER JOIN chapters ON quizzes.chapter_id = chapters.id
        WHERE quizzes.id LIKE ? OR chapters.name LIKE ?
        GROUP BY quizzes.id
    """, (f"%{search_query}%", f"%{search_query}%"))
    quizzes = cursor.fetchall()

    conn.close()
    
    return render_template('admin_search.html', search_query=search_query, users=users, subjects=subjects, quizzes=quizzes)

@app.route('/admin/user/<int:user_id>')
def admin_view_user(user_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, username, qualification, dob FROM users WHERE id = ?", (user_id,))
    user = cur.fetchall()
    conn.close()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_user_details.html', user=user)

@app.route('/admin/subject/<int:subject_id>')
def admin_view_subject(subject_id):
    conn = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute("SELECT id, name FROM subjects WHERE id = ?", (subject_id,))
    subject = cursor.fetchone()
 
    cursor.execute("SELECT id, name FROM chapters WHERE subject_id = ?", (subject_id,))
    chapters = cursor.fetchall()
 
    cursor.execute("""
        SELECT quizzes.id, quizzes.date, chapters.name as chapter_name
        FROM quizzes
        INNER JOIN chapters ON quizzes.chapter_id = chapters.id
        WHERE chapters.subject_id = ?
    """, (subject_id,))
    quizzes = cursor.fetchall()

    conn.close()

    if subject:
        return render_template('admin_subject_details.html', subject=subject, chapters=chapters, quizzes=quizzes)

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/quiz/<int:quiz_id>')
def admin_view_quiz(quiz_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT quizzes.id, quizzes.num_questions, quizzes.date_of_quiz, chapters.name, subjects.name
        FROM quizzes
        JOIN chapters ON quizzes.chapter_id = chapters.id
        JOIN subjects ON chapters.subject_id = subjects.id
        WHERE quizzes.id = ?
    """, (quiz_id,))
    quiz = cur.fetchone()
    conn.close()

    if not quiz:
        flash("Quiz not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_quiz_details.html', quiz=quiz)

@app.route('/admin/subjects')
def admin_subjects():
    subjects = models.get_subjects()
    return render_template('admin_subjects.html', subjects=subjects)

@app.route('/admin/subject/add', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        models.add_subject(name, description)
        return redirect(url_for('admin_dashboard'))
    return render_template('add_subject.html')

@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):     
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()

    if request.method == 'POST':
         
        new_name = request.form['name']         
        cur.execute('UPDATE subjects SET name = ? WHERE id = ?', (new_name, subject_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))   
 
    cur.execute('SELECT id, name FROM subjects WHERE id = ?', (subject_id,))
    subject = cur.fetchone()
    conn.close()

    return render_template('edit_subject.html', subject=subject)



@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
 
    cur.execute('DELETE FROM questions WHERE quiz_id IN (SELECT id FROM quizzes WHERE chapter_id IN (SELECT id FROM chapters WHERE subject_id = ?))', (subject_id,))
    cur.execute('DELETE FROM quizzes WHERE chapter_id IN (SELECT id FROM chapters WHERE subject_id = ?)', (subject_id,))
    cur.execute('DELETE FROM chapters WHERE subject_id = ?', (subject_id,))
    cur.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))

    conn.commit()
    conn.close()

    flash("Subject and related data deleted successfully", "success")
    return redirect(url_for('admin_dashboard')) 
 
@app.route('/admin/chapters/<int:subject_id>')
def admin_chapters(subject_id):
    chapters = models.get_chapters(subject_id)
    return render_template('admin_chapters.html', chapters=chapters, subject_id=subject_id)

@app.route('/admin/chapter/add/<int:subject_id>', methods=['GET', 'POST'])
def add_chapter(subject_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        models.add_chapter(subject_id, name, description)
        return redirect(url_for('admin_dashboard'))
    return render_template('add_chapter.html', subject_id=subject_id)

@app.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()

    if request.method == 'POST':
        new_name = request.form['name']
        cur.execute('UPDATE chapters SET name = ? WHERE id = ?', (new_name, chapter_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))   
 
    cur.execute('SELECT id, name FROM chapters WHERE id = ?', (chapter_id,))
    chapter = cur.fetchone()
    conn.close()

    return render_template('edit_chapter.html', chapter=chapter) 

@app.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM chapters WHERE id = ?', (chapter_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard')) 

@app.route('/admin/quizzes')
def admin_quizzes():
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
      
    cur.execute("""
        SELECT quizzes.id, quizzes.name, chapters.name AS chapter_name 
        FROM quizzes 
        JOIN chapters ON quizzes.chapter_id = chapters.id
    """)
    quizzes = cur.fetchall()

    quizzes_dict = {}

    for quiz in quizzes:
        quiz_id, quiz_name, chapter_id = quiz
 
        cur.execute("SELECT id, title FROM questions WHERE quiz_id = ?", (quiz_id,))
        questions = cur.fetchall()
 
        question_list = [{'id': q[0], 'title': q[1]} for q in questions]
 
        quizzes_dict[quiz_id] = {
            'id': quiz_id,
            'name': quiz_name,
            'chapter_id': chapter_id,
            'questions': question_list
        }

    conn.close()
    return render_template('admin_quizzes.html', quizzes=list(quizzes_dict.values()))

@app.route('/admin/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    conn = sqlite3.connect('instance/quiz_master.db')
    conn.row_factory = sqlite3.Row  
    cur = conn.cursor()
 
    cur.execute("SELECT id, name FROM chapters")  
    chapters = cur.fetchall()  
    
    if request.method == 'POST':
        quiz_name = request.form['name']
        chapter_id = request.form.get('chapter_id')
        quiz_date = request.form['date_of_quiz']  # Get date from form
        quiz_duration = request.form['time_duration']  # Ensure correct retrieval

        if not chapter_id:
            flash('Please select a chapter.', 'danger')
            return redirect(url_for('add_quiz'))

        conn = sqlite3.connect('instance/quiz_master.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO quizzes (name, chapter_id, date_of_quiz, time_duration) VALUES (?, ?, ?, ?)", 
                    (quiz_name, chapter_id, quiz_date, quiz_duration))        
        conn.commit()
        conn.close()

        flash('Quiz added successfully!', 'success')
        conn.close()
        return redirect(url_for('admin_quizzes'))
    conn.close()

    return render_template('add_quiz.html', chapters=chapters)

@app.route('/admin/quiz/edit/<int:quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        chapter_id = request.form['chapter_id']
        cur.execute('UPDATE quizzes SET name = ?, chapter_id = ? WHERE id = ?', (name, chapter_id, quiz_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_quizzes'))

    cur.execute('SELECT id, name, chapter_id FROM quizzes WHERE id = ?', (quiz_id,))
    quiz = cur.fetchone()

    cur.execute('SELECT id, name FROM chapters')
    chapters = cur.fetchall()
    conn.close()

    return render_template('edit_quiz.html', quiz=quiz, chapters=chapters)

@app.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
 
    cur.execute("DELETE FROM questions WHERE quiz_id = ?", (quiz_id,))
    cur.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))

    conn.commit()
    conn.close()
    
    flash("Quiz deleted successfully!", "success")
    return redirect(url_for('admin_quizzes'))
 
@app.route("/add_question/<int:quiz_id>", methods=["GET", "POST"])
def add_question(quiz_id):
    conn = sqlite3.connect("instance/quiz_master.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT chapters.id, chapters.name 
        FROM chapters 
        JOIN quizzes ON quizzes.chapter_id = chapters.id 
        WHERE quizzes.id = ?
    """, (quiz_id,))
    chapters = cur.fetchone()

    if request.method == "POST":
        chapter_id = chapters["id"]
        question_title = request.form.get("question_title").strip()
        question_statement = request.form.get("question_statement").strip()
        option1 = request.form.get("option1").strip()
        option2 = request.form.get("option2").strip()
        option3 = request.form.get("option3").strip()
        option4 = request.form.get("option4").strip()
        correct_option = request.form.get("correct_option")
 
        print(f"✅ Received Data: {chapter_id}, {question_title}, {question_statement}, {option1}, {option2}, {option3}, {option4}, {correct_option}")
 
        if not all([chapter_id, question_title, question_statement, option1, option2, option3, option4, correct_option]):
            flash("Please fill all fields!", "danger")
            return redirect(url_for("add_question", quiz_id=quiz_id))

        try:
            cur.execute("""
                INSERT INTO questions (quiz_id, chapter_id, title, statement, option1, option2, option3, option4, correct_option)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (quiz_id, chapter_id, question_title, question_statement, option1, option2, option3, option4, int(correct_option)))

            conn.commit()
            print("Question successfully added!")

        except sqlite3.Error as e:
            print(f"❌ SQLite Error: {e}")
            flash("Database error occurred!", "danger")

        conn.close()
        return redirect(url_for("add_question", quiz_id=quiz_id))  

    conn.close()
    return render_template("add_question.html", quiz_id=quiz_id, chapters=chapters)
 
@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    conn.row_factory = sqlite3.Row   
    cur = conn.cursor()
 
    cur.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    question = cur.fetchone()

    if not question:
        conn.close()
        flash("Question not found", "danger")
        return redirect(url_for('admin_quizzes'))
 
    cur.execute("SELECT id, name FROM chapters")
    chapters = cur.fetchall()

    if request.method == 'POST':
        chapter_id = request.form['chapter_id']
        question_title = request.form['question_title']
        question_statement = request.form['question_statement']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_option = request.form['correct_option']
 
        cur.execute("""
            UPDATE questions 
            SET chapter_id=?, title=?, statement=?, 
                option1=?, option2=?, option3=?, option4=?, correct_option=?
            WHERE id=?
        """, (chapter_id, question_title, question_statement, 
              option1, option2, option3, option4, correct_option, question_id))

        conn.commit()
        conn.close()
        
        flash("Question updated successfully!", "success")
        return redirect(url_for('admin_quizzes'))

    conn.close()
    return render_template('edit_question.html', question=question, chapters=chapters)


@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
 
    cur.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()

    flash("Question deleted successfully!", "success")
    return redirect(url_for('admin_quizzes'))

import time

@app.route('/start_quiz/<int:quiz_id>')
@app.route('/start_quiz/<int:quiz_id>/<int:q_no>')
def start_quiz(quiz_id, q_no=0):
    user_id = session.get('user_id')

    if not user_id:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
 
    cur.execute("SELECT COUNT(*) FROM scores WHERE quiz_id = ? AND user_id = ?", (quiz_id, user_id))
    attempt_count = cur.fetchone()[0]

    if attempt_count > 0:
        flash("You have already attempted this quiz.", "danger")
        conn.close()
        return redirect(url_for("user_dashboard"))  
 
    if 'attempt_id' not in session or q_no == 0:
        session['attempt_id'] = int(time.time())  

    attempt_id = session['attempt_id']
 
    cur.execute("SELECT id, statement, option1, option2, option3, option4 FROM questions WHERE quiz_id = ? ORDER BY id", (quiz_id,))
    questions = cur.fetchall()
    conn.close()

    if not questions:
        flash("No questions available for this quiz.", "danger")
        return redirect(url_for("user_dashboard"))

    if q_no >= len(questions):
        return redirect(url_for("quiz_summary", quiz_id=quiz_id))

    current_question = questions[q_no]

    return render_template(
        "quiz_attempt.html",
        quiz_id=quiz_id,
        attempt_id=attempt_id,
        q_no=q_no,
        question=current_question,
        total_questions=len(questions)
    )

@app.route('/next_question/<int:quiz_id>/<int:q_no>', methods=['POST'])
def next_question(quiz_id, q_no):
    user_answer = request.form.get("answer")
    
    if user_answer is None:
        flash("Please select an answer before proceeding.", "warning")
        return redirect(url_for("start_quiz", quiz_id=quiz_id, q_no=q_no))

    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
 
    cur.execute("SELECT COUNT(*) FROM questions WHERE quiz_id = ?", (quiz_id,))
    total_questions = cur.fetchone()[0]
 
    cur.execute("SELECT id, correct_option FROM questions WHERE quiz_id = ? ORDER BY id LIMIT 1 OFFSET ?", (quiz_id, q_no))
    question_data = cur.fetchone()
    
    if not question_data:
        conn.close()
        return redirect(url_for("quiz_summary", quiz_id=quiz_id))  

    question_id, correct_answer = question_data
 
    attempt_id = session.get('attempt_id')  
    cur.execute("""
    INSERT INTO user_answers (quiz_id, user_id, question_id, selected_option, is_correct, attempt_id)
    VALUES (?, ?, ?, ?, ?, ?)
""", (quiz_id, session['user_id'], question_id, user_answer, int(user_answer) == correct_answer, attempt_id))

    conn.commit()
    conn.close()

    q_no += 1  
 
    if q_no < total_questions:
        return redirect(url_for("start_quiz", quiz_id=quiz_id, q_no=q_no))
    else:
        flash("Quiz completed!", "success")
        return redirect(url_for("quiz_summary", quiz_id=quiz_id))

@app.route('/quiz_summary/<int:quiz_id>')
def quiz_summary(quiz_id):
    user_id = session.get('user_id')

    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
 
    attempt_id = session.get('attempt_id')
 
    cur.execute("SELECT COUNT(*) FROM scores WHERE quiz_id = ? AND user_id = ?", (quiz_id, user_id))
    existing_score = cur.fetchone()[0]

    if existing_score > 0:
        flash("You have already attempted this quiz and cannot retake it.", "warning")
        conn.close()
        return redirect(url_for("user_dashboard"))
 
    cur.execute("SELECT COUNT(*) FROM questions WHERE quiz_id = ?", (quiz_id,))
    total_questions = cur.fetchone()[0] or 0
 
    cur.execute("SELECT COUNT(DISTINCT question_id) FROM user_answers WHERE quiz_id = ? AND user_id = ? AND attempt_id = ?", (quiz_id, user_id, attempt_id))
    total_attempted = cur.fetchone()[0] or 0
 
    cur.execute("SELECT COUNT(*) FROM user_answers WHERE quiz_id = ? AND user_id = ? AND is_correct = 1 AND attempt_id = ?", (quiz_id, user_id, attempt_id))
    total_correct = cur.fetchone()[0] or 0

    total_wrong = total_attempted - total_correct
    time_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
 
    cur.execute("INSERT INTO scores (quiz_id, user_id, time_stamp_of_attempt, total_scored) VALUES (?, ?, ?, ?)", (quiz_id, user_id, time_stamp, total_correct))
    conn.commit()
    conn.close()

    return render_template("quiz_summary.html", total_questions=total_questions, total_attempted=total_attempted, total_correct=total_correct, total_wrong=total_wrong)

@app.route('/view_quiz/<int:quiz_id>')
def view_quiz(quiz_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
 
    cur.execute('''
        SELECT quizzes.id, chapters.name, quizzes.num_questions,
               quizzes.date_of_quiz, quizzes.time_duration 
        FROM quizzes
        JOIN chapters ON quizzes.chapter_id = chapters.id
        WHERE quizzes.id = ?
    ''', (quiz_id,))
    quiz = cur.fetchone()
     
    if not quiz:
        flash("Quiz not found!", "danger")
        return redirect(url_for("user_dashboard"))
    
    cur.execute('SELECT COUNT(*) FROM questions WHERE quiz_id = ?', (quiz_id,))
    num_questions = cur.fetchone()[0]
    conn.close()
        
    return render_template("view_quiz.html", quiz=quiz, num_questions=num_questions)

@app.route('/user/scores')
def user_scores():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    conn = sqlite3.connect('instance/quiz_master.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
 
    cur.execute('''
        SELECT quizzes.name AS quiz_name, scores.total_scored AS score,
        (SELECT COUNT(*) FROM questions WHERE quiz_id = scores.quiz_id) AS total_questions
        FROM scores
        JOIN quizzes ON scores.quiz_id = quizzes.id
        WHERE scores.user_id = ?
        ORDER BY scores.time_stamp_of_attempt DESC
    ''', (user_id,))
    scores = cur.fetchall()

    cur.execute('SELECT quiz_id from scores WHERE user_id = ? ', (user_id,))
    quiz_id = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM questions WHERE quiz_id = ?', (quiz_id,))
    num_questions = cur.fetchone()[0]
    conn.close()

    return render_template("user_scores.html", scores=scores )

@app.route('/user_summary')
def user_summary():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('instance/quiz_master.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
 
    cur.execute("""
        SELECT quizzes.name AS quiz_name, scores.time_stamp_of_attempt AS date_attempted, 
               scores.total_scored AS score, 
               (SELECT COUNT(*) FROM questions WHERE quiz_id = scores.quiz_id) AS total_questions
        FROM scores
        JOIN quizzes ON scores.quiz_id = quizzes.id
        WHERE scores.user_id = ?
        ORDER BY scores.time_stamp_of_attempt DESC
    """, (user_id,))
    
    quiz_attempts = cur.fetchall()

    conn.close()

    return render_template("user_summary.html", quiz_attempts=quiz_attempts)

@app.route('/admin/summary')
def admin_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM subjects")
    total_subjects = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM quizzes")
    total_quizzes = cursor.fetchone()[0]
 
    cursor.execute("""
        SELECT subjects.name, COUNT(quizzes.id)
        FROM subjects
        JOIN chapters ON subjects.id = chapters.subject_id
        JOIN quizzes ON chapters.id = quizzes.chapter_id
        GROUP BY subjects.id
    """)
    subject_wise_quizzes = dict(cursor.fetchall())
 
    cursor.execute("""
        SELECT strftime('%m', time_stamp_of_attempt) AS month, COUNT(*) 
        FROM scores 
        GROUP BY month
    """)
    month_wise_attempts = dict(cursor.fetchall())
 
    pie_chart_data = []
    total_attempts = sum(month_wise_attempts.values()) if month_wise_attempts else 1
    start_angle = 0

    colors = ["#ff9999", "#66b3ff", "#99ff99", "#ffcc99", "#c2c2f0", "#ffb3e6"]
    for index, (month, count) in enumerate(month_wise_attempts.items()):
        percentage = (count / total_attempts) * 360
        end_angle = start_angle + percentage
        pie_chart_data.append({
            "color": colors[index % len(colors)],
            "start_angle": start_angle,
            "end_angle": end_angle
        })
        start_angle = end_angle

    conn.close()
    
    return render_template('admin_summary.html',
                           total_users=total_users,
                           total_subjects=total_subjects,
                           total_quizzes=total_quizzes,
                           subject_wise_quizzes=subject_wise_quizzes,
                           pie_chart_data=pie_chart_data)


if __name__=='__main__':
    app.run(debug=True)