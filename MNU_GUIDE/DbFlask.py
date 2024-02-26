from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)
# MySQL database connection configuration
db_connection = mysql.connector.connect(
    host="orion.mokpo.ac.kr",
    port=8313,
    user="root",
    password="ScE1234**",
    database="BuildingMap",
)


# Function to establish database connection
def get_db_connection():
    return mysql.connect(**db_connection)


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
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


if __name__ == "__main__":
    app.run(debug=True)
