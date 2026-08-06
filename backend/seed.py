import psycopg2
from faker import Faker
import random as rd
from datetime import date, timedelta
import string
import os
from dotenv import load_dotenv, dotenv_values
from hash import encrypting


fake = Faker()
load_dotenv()

# ------------ HELPERS -------------------
def generate_dates(start_date, char):
    maximum_date = date(2026, 5, 8)
    if char == 'e':
        #making 2 months the minimum time needed to enroll a course
        minimum_date = start_date + timedelta(days=60) 
    elif char == 'c':
        #making 6 months the minimum time needed to complete a course
        minimum_date = start_date + timedelta(days=180) 

    if minimum_date > maximum_date:
        return maximum_date

    final_date = fake.date_between(
        start_date=minimum_date,
        end_date=maximum_date
    )
    return final_date

def generate_session_duration(login_start, login_end):
    login_time = fake.date_time_between(
        start_date=login_start, 
        end_date=login_end
    )
    #sort between 5 minutes and 3 hours for session duration
    duration = timedelta(minutes = rd.randint(5, 180)) 
    logout_time = login_time + duration
    return login_time, logout_time

def generate_password():
    chars = string.ascii_letters + string.digits
    password = ''.join([rd.choice(chars) for _ in range(12)])
    return encrypting(password)

def generate_email(name, i):
    first_part = name.replace(" ", "").lower()
    email = first_part + str(i) + '@example.com'
    return email

def role_selection(i):
    if  i <= 4:
        role = 'ADMIN'
    elif i > 4 and i <= 58:
        role = 'INSTRUCTOR'
    else:
        role = 'STUDENT'
  
    return role

def status_selection():
    return "INACTIVE" if rd.randint(1,10) <= 2 else "ACTIVE"

def course_association(instructors_id):
    # nmr_courses = rd.randint(1,4)
    # print(instructors_id)
    instructors = rd.choice(instructors_id)
    return instructors

def enroll_association(courses_id):
    nmr_enroll = rd.randint(1,4)
    courses_set = rd.sample(courses_id, nmr_enroll)
    return courses_set

def generate_progress(enrollment_date):
    can_be_completed = (enrollment_date + timedelta(days=180)) <= date(2026, 5, 8) 
    if can_be_completed:
        progress = 100.00 if rd.random() < 0.2 else round(rd.uniform(0, 99.99), 2)
    else:
        progress = round(rd.uniform(0, 99.99), 2)
    return progress
#------------------------------------------

def connect():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

    cursor = conn.cursor()
    return conn, cursor

def generate_users(cursor):
    #generating user fake data
    for i in range(100):
        name = fake.name()
        email = generate_email(name, i)
        password = generate_password()
        status = status_selection()
        created_at = fake.date_between(start_date=date(2021, 5, 8), end_date=date(2025, 5, 8))
        role = role_selection(i)

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name, email, password, role, status, created_at) 
        )

def generate_courses(cursor):
    courses = [
    "Python Fundamentals",
    "Advanced Python",
    "Introduction to SQL",
    "React Basics",
    "TypeScript Essentials",
    "Java Programming",
    "Machine Learning",
    "Data Structures",
    "Algorithms",
    "Web Development",
    "Docker Essentials",
    "Git & GitHub",
    "REST APIs",
    "Power BI Fundamentals",
    "Computer Networks",
    "Cyber Security",
    "Power BI Advanced",
    "Software Engineering",
    "Computer Programming I",
    "Computer Programming II",
    "Object Oriented Programming",
    "Computer Architecture",
    "Operating Systems",
    "Linux",
    "Distributed Systems",
    "Optimization",
    "Data Organization"
    ]
    
    #instructors id
    cursor.execute(
        """
        SELECT id FROM users WHERE role = 'INSTRUCTOR'
        ORDER BY id
        """
    )

    instructors_ids = cursor.fetchall()
    instructors_ids = [x[0] for x in instructors_ids]

    old_courses = 19
    for j, course in enumerate(courses):
        if j <= old_courses:
            created_at = date(2021, 5, 8)
        else:
            created_at = fake.date_between(start_date=date(2022, 5, 8), end_date=date(2024, 12, 30))

        description = fake.text(max_nb_chars=500)
        instructor = course_association(instructors_ids)

        cursor.execute(
            """
            INSERT INTO courses (name, instructor_id, created_at, description)
            VALUES (%s, %s, %s, %s)
            """,
            (course, instructor, created_at, description)
        )

def generate_enrollment(cursor):
    cursor.execute(
        """
        SELECT id FROM users WHERE role = 'STUDENT'
        ORDER BY id
        """
    )
    students_id = cursor.fetchall()

    cursor.execute(
        """
        SELECT id FROM courses
        ORDER BY id
        """
    )
    courses_id = cursor.fetchall()
    courses_id = [x[0] for x in courses_id]

    for (student,) in students_id:
        courses_set = enroll_association(courses_id)

        for course in courses_set:
            #initial values
            grade = None
            completed_at = None
            status = 'IN_PROGRESS'

            cursor.execute(
                """
                SELECT created_at FROM courses
                WHERE id = %s
                """,
                (course,)
            )
            (created_at,) = cursor.fetchone()

            enrollment_date = generate_dates(created_at, 'e')
            progress = generate_progress(enrollment_date)
            
            #if progress is less than 50% for more than 2 yers, status is dropped
            if progress <= 50.00 and enrollment_date.year < 2024:
                status = 'DROPPED'
            #if progress is 100%, generate a conclusion date
            elif progress == 100.00:
                completed_at = generate_dates(enrollment_date, 'c')
                if rd.randint(1,10) <= 7:
                    grade = round(rd.uniform(0,10), 1) 
                    if grade < 6.5:
                        status = "FAILED"
                    else:
                        status = "PASSED"
            
            cursor.execute(
                """
                INSERT INTO enrollments (
                    student_id, 
                    course_id, 
                    status,
                    enrollment_date,
                    progress,
                    completed_at,
                    grade
                    )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (student, course, status, enrollment_date, progress, completed_at, grade)
            )

def generate_loginSessions(cursor):

    cursor.execute(
        """
        SELECT DISTINCT ON (student_id)
            student_id,
            enrollment_date,
            completed_at
        FROM enrollments
        ORDER BY student_id, enrollment_date;
        """
    )
    student_courses = cursor.fetchall()

    for (
        student_id, 
        enrollment_date, 
        completed_at, 
    ) in student_courses:
        sessions_count = rd.randint(5, 25)

        for _ in range (sessions_count):
            if completed_at is None:
                login_time, logout_time = generate_session_duration(enrollment_date, date(2026, 5, 8))
            else:
                login_time, logout_time = generate_session_duration(enrollment_date, completed_at)
            
            cursor.execute(
                """
                INSERT INTO login_sessions (user_id, login_time, logout_time)
                VALUES (%s, %s, %s)
                """,
                (student_id, login_time, logout_time)
            )




def main():
   print("conectando...")
   conn, cursor = connect()
#    print("gerando dados para usuários...") 
#    generate_users(cursor)
#    print("gerando dados para cursos...") 
#    generate_courses(cursor)
#    print("gerando dados para matriculas...") 
#    generate_enrollment(cursor)
   print("gerando dados para sessões...") 
   generate_loginSessions(cursor)
   conn.commit()
   print("commitando...")
   cursor.close()
   conn.close()
   print("conexão fechada.")

if __name__ == "__main__":
    main()