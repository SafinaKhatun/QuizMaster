import sqlite3

def insert_admin():
    con = sqlite3.connect('instance/quiz_master.db')
    cur = con.cursor()

     
    cur.execute('INSERT INTO admins (email, password) VALUES (?, ?)', 
                ('admin@gmail.com', 'admin123'))

    con.commit()
    con.close()
    print("Admin inserted successfully!")

 
#insert_admin()
