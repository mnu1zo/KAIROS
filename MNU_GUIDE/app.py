from flask import Flask, render_template, redirect, request, url_for, flash, jsonify, request, session
import requests
import mysql.connector
import pymysql
import re
import json
from flask_cors import CORS

app = Flask(__name__)
app.config["SECRET_KEY"] = "MNU_GUIDE"
CORS(app)

# MySQL database connection configuration
db_connection = {
    'host': 'orion.mokpo.ac.kr',
    'port': 8313,
    'user': 'root',
    'password': 'ScE1234**',
    'database': 'BuildingMap',
}


# Function to establish database connection
def get_db_connection():
    return pymysql.connect(**db_connection)


# Route for user registration
@app.route("/register", methods=["POST"])
def register():
    # Extract registration data from request
    data = request.json
    student_id = data.get("student_id")
    username = data.get("username")
    password_hash = data.get("password_hash")

    # Insert data into the users table
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (student_id, username, password_hash) VALUES (%s, %s, %s)",
            (student_id, username, password_hash),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Registration successful"}), 201
    except pymysql.Error as err:
        return jsonify({"error": str(err)}), 500


users = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        userid = request.form.get('userid')
        password = request.form.get('password')

        if not (userid and password):
            flash('아이디 또는 비밀번호를 입력하세요.', 'error')
            return render_template('index.html')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE student_id = %s", (userid,))
            user = cursor.fetchone()

            if user and user[2] == password:  # user[3]은 password_hash 필드입니다.
                session['userid'] = userid
                return redirect(url_for('home'))
            else:
                flash('로그인 실패! 사용자 이름 또는 비밀번호가 잘못되었습니다.', 'error')
                return render_template('index.html')
        except pymysql.Error as err:
            flash(f'로그인 중 오류가 발생했습니다: {err}', 'error')
            return render_template('index.html')
        finally:
            cursor.close()
            conn.close()

    return render_template('index.html')

def is_valid_password(password):
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password))


@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        username = request.form['username']
        userid = request.form['userid']
        password = request.form['password']
        password2 = request.form['password2']
        
        if not (username and userid and password and password2):
            flash('모든 필드를 입력하세요.', 'error')
            return render_template('join.html')
        
        if password != password2:
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return render_template('join.html')
        
        if not is_valid_password(password):
            flash('비밀번호는 영문, 숫자, 특수문자를 모두 포함하여 8자 이상이어야 합니다.', 'error')
            return render_template('join.html')

        # JSON 데이터 패킹
        data = {
            "student_id": int(userid),
            "username": str(username),
            "password_hash": str(password)  # 비밀번호를 해싱하는 함수를 사용하여 해싱된 값 전달
        }
        
        # 요청을 보낼 URL
        url = 'http://orion.mokpo.ac.kr:8411/register'
        
        # POST 요청 보내기
        response = requests.post(url, json=data)
        
        # 서버 응답 처리
        if response.status_code == 201:
            flash('가입이 완료되었습니다!', 'success')
            return redirect(url_for('index'))
        else:
            flash('가입 중 오류가 발생했습니다.', 'error')
            return render_template('join.html')
    
    return render_template('join.html')

@app.route('/home')
def home():
    userid = session.get('userid')
    if userid:
        return render_template('home.html')
    else:
        return redirect(url_for('search_subject'))
    
@app.route('/set_overlay', methods=['POST'])
def set_overlay():
    # Get course_id from request data
    course_id = request.json.get('course_id')
    
    # Check if course_id is provided
    if not course_id:
        return jsonify({'error': 'Course ID not provided'}), 400

    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to retrieve course information using course_id
        query = """
            SELECT c.subject_name, c.professor, c.lecture_time, c.lecture_time2, b.building_name, c.classroom
            FROM courses AS c
            JOIN building AS b ON c.building_id = b.building_id
            WHERE c.course_id = %s
        """
        cursor.execute(query, (course_id,))
        
        # Fetch the result
        course_info = cursor.fetchone()

        if course_info:
            # Construct data dictionary with course information
            data = {
                "subject_name": course_info[0],
                "professor": course_info[1],
                "lecture_time": course_info[2],
                "lecture_time2": course_info[3],
                "building_name": course_info[4],
                "classroom": course_info[5]
            }
            return jsonify(data), 200
        else:
            return jsonify({'error': 'Course not found'}), 404
    except pymysql.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if conn:
            conn.close()
    

@app.route('/user_table', methods=['GET'])
def user_table():
    userid = session.get('userid')
    if userid:
        try:
            # 데이터베이스 연결
            conn = get_db_connection()
            cursor = conn.cursor()
            # 사용자가 수강 중인 강의의 위치 정보를 데이터베이스에서 가져오기
            cursor.execute("""
                SELECT c.course_id, b.latitude, b.longitude
                FROM user_course_enrollment AS uce
                JOIN courses AS c ON uce.course_id = c.course_id
                JOIN building AS b ON c.building_id = b.building_id
                WHERE uce.student_id = %s
            """, (userid,))
            data = cursor.fetchall()

            conn.close()

            return jsonify(data)
        except pymysql.Error as e:
            return jsonify({'error': str(e)})
    else:
        return redirect(url_for('search_subject'))

    
@app.route('/enroll_course', methods=["POST"])
def enroll_course():
    # 세션에서 사용자 ID 가져오기
    user_id = session.get('userid')
    if user_id:
        # POST 요청으로부터 과목명 가져오기
        subject_name = request.json.get('subject_name')
        
        if not subject_name:
            return jsonify({"error": "Subject name not provided"}), 400

        # 과목명과 사용자 ID를 이용하여 user_course_enrollment 테이블에 데이터 삽입
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_course_enrollment (student_id, course_id) SELECT %s, course_id FROM courses WHERE subject_name = %s",
                (user_id, subject_name)
            )
            conn.commit()
            conn.close()
            return jsonify({"message": "Enrollment successful"}), 200
        except pymysql.Error as err:
            return jsonify({"error": str(err)}), 500
    else:
        return jsonify({"error": "User not logged in"}), 401

@app.route('/search_subject', methods=["GET", "POST"])
def search_subject():
    if request.method == 'POST':
        # Get the search query from the form
        subject_query = request.form.get("subject")
        
        # Initialize an empty list to store matching subject names
        matching_subjects = []
        
        try:
            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Execute the query to search for subject names containing the search query
            cursor.execute("SELECT subject_name FROM courses WHERE subject_name LIKE %s", ('%' + subject_query + '%',))

            # Fetch all matching subject names
            matching_subjects = [row[0] for row in cursor.fetchall()]

            # Close the database connection
            conn.close()

            # Return the matching subject names as JSON response
            return jsonify({"matching_subjects": matching_subjects}), 200
        except pymysql.Error as err:
            # Return error message if an error occurs
            return jsonify({"error": str(err)}), 500
    
    return render_template('search_subject.html')

    

@app.route('/logout')
def logout():
    session.pop('userid', None)
    return redirect(url_for('index'))

# 여기부터 카카오맵
@app.route('/maps')
def maps():
    return render_template('maps.html')

@app.route('/maps2')
def maps2():
    return render_template('maps2.html')

@app.route('/maps3')
def maps3():
    return render_template('maps3.html')

@app.route('/get_coordinates', methods=['POST'])
def get_coordinates():
    address = request.json['address']
    kakao_api_key = 'cea85fd7f36a979c619615a519f9ab45'
    url = f'https://dapi.kakao.com/v2/local/search/address.json?query={address}'
    headers = {'Authorization': f'KakaoAK {kakao_api_key}'}
    response = requests.get(url, headers=headers)
    data = response.json()
    # 여기서는 간단히 첫 번째 결과만 반환합니다.
    if data['documents']:
        coordinates = data['documents'][0]['x'], data['documents'][0]['y']
        return jsonify({'coordinates': coordinates})
    else:
        return jsonify({'error': '주소를 찾을 수 없습니다.'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)