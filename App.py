from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

import mysql.connector

app = Flask(__name__)
app.secret_key = "your_secret_key"


# ================================
# Initialization
# ================================

# Database connection function
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Ishanka135@",
            database="vsgnsmp",
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None


# ================================
# Common Routes
# ================================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()
        if not connection:
            flash("Database connection failed. Please try again later.")
            return redirect(url_for("login"))

        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT user_id, username, role, first_name, last_name 
                FROM users 
                WHERE username=%s AND password=%s
            """
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Error during login query: {err}")
            flash("An error occurred. Please try again.")
            user = None
        finally:
            cursor.close()
            connection.close()

        if user:
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["full_name"] = f"{user['first_name']} {user['last_name']}"
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password!")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect(url_for("login"))

    workshops = get_workshops()
    social_groups = get_social_media_groups()
    available_groups = get_available_groups(session["user_id"])
    joined_groups = get_joined_groups(session["user_id"])
    announcements = get_announcements()

    connection = get_db_connection()
    users = []
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT user_id, first_name, last_name, email, role
                FROM users
                WHERE user_id != %s
            """
            cursor.execute(query, (session["user_id"],))
            users = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error fetching users: {err}")
            flash("An error occurred while fetching users.")
        finally:
            cursor.close()
            connection.close()

    return render_template(
        "db.html",
        full_name=session.get("full_name", "User"),
        role=session.get("role", "User"),
        workshops=workshops,
        social_groups=social_groups,
        available_groups=available_groups,
        joined_groups=joined_groups,
        users=users,
        announcements=announcements,  # Pass announcements to the template
    )


@app.route("/create_group", methods=["POST"])
def create_group():
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect(url_for("login"))

    group_name = request.form["group_name"]
    description = request.form["description"]
    created_by = session["user_id"]

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO study_groups (group_name, description, created_by)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (group_name, description, created_by))
        group_id = cursor.lastrowid

        query = "INSERT INTO study_group_members (group_id, user_id) VALUES (%s, %s)"
        cursor.execute(query, (group_id, created_by))

        connection.commit()
        flash("Study group created successfully!")
    except mysql.connector.Error as err:
        print(f"Error creating group: {err}")
        flash("An error occurred while creating the group.")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))


@app.route("/join_group", methods=["POST"])
def join_group():
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect(url_for("login"))

    group_id = request.form["group_id"]
    user_id = session["user_id"]

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor()
        query = "INSERT INTO study_group_members (group_id, user_id) VALUES (%s, %s)"
        cursor.execute(query, (group_id, user_id))
        connection.commit()
        flash("Successfully joined the group!")
    except mysql.connector.Error as err:
        print(f"Error joining group: {err}")
        flash("An error occurred while joining the group.")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))


@app.route("/view_group/<int:group_id>")
def view_group(group_id):
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect(url_for("login"))

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM study_groups WHERE group_id = %s"
        cursor.execute(query, (group_id,))
        group = cursor.fetchone()

        if not group:
            flash("Group not found!")
            return redirect(url_for("dashboard"))

        members = get_group_members(group_id)

        return render_template("viewgroup.html", group=group, members=members)
    except mysql.connector.Error as err:
        print(f"Error viewing group: {err}")
        flash("An error occurred while viewing the group.")
        return redirect(url_for("dashboard"))
    finally:
        cursor.close()
        connection.close()


@app.route("/add_group", methods=["POST"])
def add_group():
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect(url_for("login"))

    course_name = request.form["course_name"]
    platform = request.form["platform"]
    group_link = request.form["group_link"]
    created_by = session["user_id"]

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed. Please try again later.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO social_media_groups (course_name, platform, group_link, created_by)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (course_name, platform, group_link, created_by))
        connection.commit()
        flash("New group added successfully!")
    except mysql.connector.Error as err:
        print(f"Error adding new group: {err}")
        flash("An error occurred. Please try again.")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))


# ================================
# Admin Routes
# ================================

@app.route("/add_user", methods=["POST"])
def add_user():
    if "user_id" not in session or session["role"] != "admin":
        flash("You need to be an admin to add users!")
        return redirect(url_for("dashboard"))

    username = request.form["username"]
    password = request.form["password"]
    email = request.form["email"]
    role = request.form["role"]
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO users (username, password, email, role, first_name, last_name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (username, password, email, role, first_name, last_name))
        connection.commit()
        flash("User added successfully!")
    except mysql.connector.Error as err:
        print(f"Error adding user: {err}")
        flash("An error occurred while adding the user.")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))


@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if "user_id" not in session or session["role"] != "admin":
        flash("You need to be an admin to delete users!")
        return redirect(url_for("dashboard"))

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor()
        query = "DELETE FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        connection.commit()
        flash("User deleted successfully!")
    except mysql.connector.Error as err:
        print(f"Error deleting user: {err}")
        flash("An error occurred while deleting the user.")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))


@app.route("/get_users", methods=["GET"])
def get_users():
    if "user_id" not in session or session["role"] != "admin":
        flash("You need to be an admin to view users!")
        return redirect(url_for("dashboard"))

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT user_id, first_name, last_name, email, role
            FROM users
            WHERE user_id != %s
        """
        cursor.execute(query, (session["user_id"],))
        users = cursor.fetchall()
        return jsonify(users)
    except mysql.connector.Error as err:
        print(f"Error fetching users: {err}")
        flash("An error occurred while fetching users.")
        return redirect(url_for("dashboard"))
    finally:
        cursor.close()
        connection.close()

# Function to get announcements
def get_announcements():
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, title, summary, date FROM announcements ORDER BY date DESC"
        cursor.execute(query)
        announcements = cursor.fetchall()
        return announcements
    except mysql.connector.Error as err:
        print(f"Error fetching announcements: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


@app.route("/post_announcement", methods=["POST"])
def post_announcement():
    if "user_id" not in session or session.get("role") != "admin":
        flash("You need admin privileges to post announcements!")
        return redirect(url_for("dashboard"))

    title = request.form.get("title")
    summary = request.form.get("summary")

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed!")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor()
        query = "INSERT INTO announcements (title, summary) VALUES (%s, %s)"
        cursor.execute(query, (title, summary))
        connection.commit()
        flash("Announcement posted successfully!")
    except mysql.connector.Error as err:
        print(f"Error posting announcement: {err}")
        flash("An error occurred while posting the announcement.")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))


@app.route("/edit_announcement/<int:announcement_id>", methods=["POST"])
def edit_announcement(announcement_id):
    if "user_id" not in session or session.get("role") != "admin":
        flash("You need admin privileges to edit announcements!")
        return redirect(url_for("dashboard"))

    title = request.form.get("title")
    summary = request.form.get("summary")

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed!")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor()
        query = """
            UPDATE announcements 
            SET title = %s, summary = %s, date = CURRENT_TIMESTAMP 
            WHERE id = %s
        """
        cursor.execute(query, (title, summary, announcement_id))
        connection.commit()
        flash("Announcement updated successfully!")
    except mysql.connector.Error as err:
        print(f"Error updating announcement: {err}")
        flash("An error occurred while updating the announcement.")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))

def get_announcements():
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, title, summary, date FROM announcements ORDER BY date DESC"
        cursor.execute(query)
        announcements = cursor.fetchall()
        return announcements
    except mysql.connector.Error as err:
        print(f"Error fetching announcements: {err}")
        return []
    finally:
        cursor.close()
        connection.close()



# ================================
# Student Routes
# ================================

def get_workshops():
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT w.workshop_name, w.workshop_description, w.start_time, z.zoom_link
        FROM workshops w
        LEFT JOIN workshop_zoom_links z ON w.workshop_id = z.workshop_id
        """
        cursor.execute(query)
        workshops = cursor.fetchall()
        return workshops
    except mysql.connector.Error as err:
        print(f"Error fetching workshops: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_social_media_groups():
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT course_name, platform, group_link 
        FROM social_media_groups 
        ORDER BY platform, course_name
        """
        cursor.execute(query)
        groups = cursor.fetchall()
        return groups
    except mysql.connector.Error as err:
        print(f"Error fetching social media groups: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_available_groups(user_id):
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT sg.*
            FROM study_groups sg
            WHERE sg.group_id NOT IN (
                SELECT group_id 
                FROM study_group_members 
                WHERE user_id = %s
            )
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching available groups: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_joined_groups(user_id):
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT sg.*
            FROM study_groups sg
            JOIN study_group_members sgm ON sg.group_id = sgm.group_id
            WHERE sgm.user_id = %s
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching joined groups: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_group_members(group_id):
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT u.first_name, u.last_name, u.username, sgm.joined_at
            FROM users u
            JOIN study_group_members sgm ON u.user_id = sgm.user_id
            WHERE sgm.group_id = %s
        """
        cursor.execute(query, (group_id,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching group members: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    app.run(debug=True)