import sqlite3

def create_tables():
    con= sqlite3.connect('instance/quiz_master.db')
    cur= con.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            qualification TEXT,
            dob TEXT
             
        )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_id INTEGER,
        name TEXT,
        num_questions INTEGER,
        date_of_quiz TEXT,
        time_duration TEXT,
        remarks TEXT,
        FOREIGN KEY(chapter_id) REFERENCES chapters(id)
    )
    ''')
          
    cur.execute('''
    SELECT quizzes.id, quizzes.name, quizzes.date_of_quiz, quizzes.time_duration, quizzes.remarks, 
           chapters.name AS chapter_name, subjects.name AS subject_name
    FROM quizzes
    JOIN chapters ON quizzes.chapter_id = chapters.id
    JOIN subjects ON chapters.subject_id = subjects.id
    ''')
 
    cur.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            chapter_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            statement TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            correct_option INTEGER NOT NULL CHECK(correct_option BETWEEN 1 AND 4),
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
            FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
        )
    ''')
   
    cur.execute('''
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER,
        user_id INTEGER,
        time_stamp_of_attempt TEXT,
        total_scored INTEGER,
        FOREIGN KEY(quiz_id) REFERENCES quizzes(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT
    )
    ''')
  
    cur.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    ''')
 
    cur.execute('''
    CREATE TABLE IF NOT EXISTS chapters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        name TEXT,
        description TEXT,
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    )
    ''')
     
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Chapter (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        question_count INTEGER DEFAULT 0,
        FOREIGN KEY (subject_id) REFERENCES Subject(id) ON DELETE CASCADE
    )
    ''')
         
    cur.execute('''
    CREATE TABLE IF NOT EXISTS user_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        attempt_id INTEGER,
        question_id INTEGER NOT NULL,
        selected_option INTEGER NOT NULL,
        is_correct BOOLEAN NOT NULL,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
    )
''')

    con.commit()
    con.close()
 
def get_subjects_with_chapters():
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
    cur.execute('SELECT id, name, description FROM subjects')
    subjects = cur.fetchall()

    subject_chapters = []
    for subj in subjects:
        cur.execute('SELECT id, name FROM chapters WHERE subject_id = ?', (subj[0],))
        chapters = cur.fetchall()
        subject_chapters.append({
            'id': subj[0],
            'name': subj[1],
            'description': subj[2],
            'chapters': chapters
        })

    conn.close()
    return subject_chapters

def get_chapter_question_count(chapter_id):
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM questions WHERE chapter_id = ?', (chapter_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count
 
def add_subject(name, description):
    con = sqlite3.connect('instance/quiz_master.db')
    cur = con.cursor()
    cur.execute("INSERT INTO subjects (name, description) VALUES (?, ?)", (name, description))
    con.commit()
    con.close()
 
def get_subjects():
    conn = sqlite3.connect('instance/quiz_master.db')
    cur = conn.cursor()
    cur.execute('SELECT id, name, description FROM subjects')
    subjects = cur.fetchall()
    conn.close()
    return subjects

def get_all_subjects():
    conn = sqlite3.connect('instance/quiz_master.db')
    conn.row_factory = sqlite3.Row  
    cur = conn.cursor()
    cur.execute("SELECT id, name, description FROM subjects")
    subjects = cur.fetchall()  
    conn.close()
    return subjects  
 
def update_subject(subject_id, name, description):
    con = sqlite3.connect('instance/quiz_master.db')
    cur = con.cursor()
    cur.execute("UPDATE subjects SET name = ?, description = ? WHERE id = ?", (name, description, subject_id))
    con.commit()
    con.close()
 
def delete_subject(subject_id):
    con = sqlite3.connect('instance/quiz_master.db')
    cur = con.cursor()
    cur.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    con.commit()
    con.close()
 
def add_chapter(subject_id, name, description):
    con = sqlite3.connect('instance/quiz_master.db')
    cur = con.cursor()
    cur.execute("INSERT INTO chapters (subject_id, name, description) VALUES (?, ?, ?)", (subject_id, name, description))
    con.commit()
    con.close()
 
def get_chapters(subject_id):
    con = sqlite3.connect('instance/quiz_master.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM chapters WHERE subject_id = ?", (subject_id,))
    chapters = cur.fetchall()
    con.close()
    return chapters
 
def update_chapter(chapter_id, name, description):
    con = sqlite3.connect('instance/quiz_master.db')
    cur = con.cursor()
    cur.execute("UPDATE chapters SET name = ?, description = ? WHERE id = ?", (name, description, chapter_id))
    con.commit()
    con.close()
 
def delete_chapter(chapter_id):
    con = sqlite3.connect('instance/quiz_master.db')
    cur = con.cursor()
    cur.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
    con.commit()
    con.close()
 
def get_db_connection():
    conn = sqlite3.connect('instance/quiz_master.db')
    conn.row_factory = sqlite3.Row   
    return conn
 
def add_quiz(chapter_id, name, date, duration):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO quizzes (chapter_id, name, date_of_quiz, time_duration) VALUES (?, ?, ?, ?)',
        (chapter_id, name, date, duration)
    )
    conn.commit()
    conn.close()
 
def get_quizzes(chapter_id):
    conn = get_db_connection()
    quizzes = conn.execute(
        'SELECT id, name FROM quizzes WHERE chapter_id = ?', (chapter_id,)
    ).fetchall()
    conn.close()
    return quizzes

def get_questions(quiz_id):
    con = sqlite3.connect('instance/quiz_master.db')
    cur = con.cursor()
    cur.execute("SELECT id, title FROM questions WHERE quiz_id = ?", (quiz_id,))
    questions = cur.fetchall()
    con.close()
    return questions