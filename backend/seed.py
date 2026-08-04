import psycopg2
from faker import Faker
import random as rd
from datetime import date, timedelta

fake = Faker()

def connect():
    conn = psycopg2.connect(
        dbname="YLPortal DB",
        user="postgres",
        password="121345",
        host="localhost",
        port="5432"
    )

    cursor = conn.cursor()

    # cursor.execute("SELECT current_database();")
    # print("Banco atual:", cursor.fetchone())

    return conn, cursor

def generate_dates(start_date):
    minimum_date = start_date + timedelta(days=180)

    final_date = fake.date_between(
        start_date=minimum_date,
        end_date='today'
    )
    return final_date

def generate_users(cursor):
    #db size
    instructors = 18
    admins = 2
    students = 80

    #generating student fake data
    for i in range(students):
        name = fake.name()
        email = fake.email()
        password = "fakestudent123" 
        role = "STUDENT"
        status = "INACTIVE" if rd.randint(1,10) <= 2 else "ACTIVE"
        created_at = fake.date_between(start_date='-5y')

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name, email, password, role, status, created_at) 
        )
    
    #generating instructors fake data
    for i in range(instructors):
        name = fake.name()
        email = fake.email()
        password = "fakeinstructor123" 
        role = "INSTRUCTOR"
        status = "INACTIVE" if rd.randint(1,10) <= 2 else "ACTIVE"
        created_at = fake.date_between(start_date='-5y')

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name, email, password, role, status, created_at) 
        )

    #generating admin fake data
    for i in range(admins):
        name = fake.name()
        email = fake.email()
        password = "fakeadmin123" 
        role = "ADMIN"
        status = "ACTIVE"
        created_at = fake.date_between(start_date='-5y')

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name, email, password, role, status, created_at) 
        )

    # cursor.execute("SELECT COUNT(*) FROM users;")
    # print("Quantidade de usuários:", cursor.fetchone())

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
    
    #getting the instructors id
    cursor.execute(
        """
        SELECT id FROM users WHERE role = 'INSTRUCTOR'
        ORDER BY id
        """
    )

    instructors_ids = cursor.fetchall()

    for j, (instructor,) in enumerate(instructors_ids):
        name = courses[j % len(courses)]
        created_at = fake.date_between(start_date='-5y')
        description = fake.text(max_nb_chars=500)

        cursor.execute(
            """
            INSERT INTO courses (name, instructor_id, created_at, description)
            VALUES (%s, %s, %s, %s)
            """,
            (name, instructor, created_at, description)
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

    for (student,) in students_id:
        nmr_enroll = rd.randint(1,4)
        courses_set = rd.sample(courses_id, nmr_enroll)
        for (course,) in courses_set:
            grade = None
            completed_at = None
            status = 'IN_PROGRESS'

            course_id = course
            enrollment_date = fake.date_between(start_date='-5y')
            # Só cursos com pelo menos 6 meses podem ser concluídos
            can_be_completed = enrollment_date <= date.today() - timedelta(days=180)

            if can_be_completed:
                progress = 100.00 if rd.random() < 0.2 else round(rd.uniform(0, 99.99), 2)
            else:
                progress = round(rd.uniform(0, 99.99), 2)

            if progress <= 50.00 and enrollment_date.year < 2024:
                status = 'DROPPED'
            elif progress == 100.00:
                completed_at = generate_dates(enrollment_date)
                if rd.randint(1,10) <= 7:
                    grade = round(rd.uniform(0,10), 1) 
                if grade is None:
                    status = "IN_PROGRESS"
                elif grade < 6.5:
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
                (student, course_id, status, enrollment_date, progress, completed_at, grade)
            )

def generate_loginSessions(cursor):

    cursor.execute(
        """
        SELECT
            student_id,
            enrollment_date,
            completed_at
        FROM enrollments
        ORDER BY student_id;
        """
    )
    student_courses = cursor.fetchall()

    for (
        student_id, 
        enrollment_date, 
        completed_at, 
    ) in student_courses:
        sessions_count = rd.randint(5, 25)

        for i in range (sessions_count):
            if completed_at is None:
                login_time = fake.date_time_between(start_date=enrollment_date, end_date='now')
                duration = timedelta(minutes = rd.randint(5, 180))
                logout_time = login_time + duration
            else:
                login_time = fake.date_time_between(start_date=enrollment_date, end_date=completed_at)
                duration = timedelta(minutes = rd.randint(5, 180))
                logout_time = login_time + duration
            
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
   #print("gerando dados para usuários...") 
   #generate_users(cursor)
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