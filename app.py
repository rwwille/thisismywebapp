from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import datetime
import math
import config

pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.secret_key = config.app_secret_key

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:{}@localhost/{}".format(
    config.password, config.database
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# junction table
UserActivity = db.Table(
    "user_activity",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column(
        "activity_id", db.Integer, db.ForeignKey("activity.id"), primary_key=True
    ),
)

UserHabit = db.Table(
    "user_habit",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("habit_id", db.Integer, db.ForeignKey("habit.id"), primary_key=True),
    extend_existing=True,
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    activities = db.relationship(
        "Activity", secondary=UserActivity, backref=db.backref("users", lazy=True)
    )
    # Change the backref name to 'user_habits' to avoid conflicts.
    user_habits = db.relationship("Habit", secondary=UserHabit, back_populates="users")


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)

    # Use the correct back_populates value for the user_habits relationship.
    users = db.relationship("User", secondary=UserHabit, back_populates="user_habits")

    def is_completed_today(self):
        today = datetime.date.today()
        # Assuming you have a relationship between Habit and ActivityRecord called "activity_records"
        # Check if there is any activity record for the current date
        return any(record.date_completed == today for record in self.habit_records)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    # The user_id field is removed, because an activity can now belong to many users.
    # The user relationship field is also removed.


class ActivityRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    elapsed_time = db.Column(db.Integer, nullable=False)

    activity = db.relationship("Activity", backref=db.backref("records", lazy=True))


class HabitRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id"), nullable=False)
    date_completed = db.Column(db.Date, nullable=False)  # default=datetime.date.today()
    time_completed = db.Column(db.Text, nullable=False)
    # Add the relationships to the User and Habit models
    user = db.relationship("User", backref=db.backref("habit_records", lazy=True))
    habit = db.relationship("Habit", backref=db.backref("habit_records", lazy=True))


class ToDoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    item = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.datetime.now)
    date_completed = db.Column(db.DateTime, nullable=True)


with app.app_context():
    db.create_all()


def get_activity_id(activity_name):
    activity = Activity.query.filter_by(name=activity_name).first()
    if activity:
        return activity.id
    else:
        return None


def delete_record(habit_id):
    try:
        # Query the first row with habit_id and order by id in descending order
        first_habit_record = (
            HabitRecord.query.filter_by(habit_id=habit_id)
            .order_by(HabitRecord.id.desc())
            .first()
        )

        if first_habit_record:
            db.session.delete(first_habit_record)
            db.session.commit()
            print(
                f"Successfully deleted the first habit record with habit_id = {habit_id}"
            )
        else:
            print(f"No habit record found with habit_id = {habit_id}")
    except Exception as e:
        print("Error deleting the habit record:", e)


def is_today():
    return datetime.date.today()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()  # save the user
        session["email"] = email
        print(session["email"])  # log the user in
        return redirect("/signin")  # "/signin"
    return render_template("signup.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user"] = {"id": user.id, "email": user.email}

            # Retrieve habit_record data for the user
            user_habit_records = HabitRecord.query.filter_by(user_id=user.id).all()

            # Check if the habits have been completed for today
            for record in user_habit_records:
                if record.date_completed == datetime.date.today():
                    # Mark the habit as completed in the frontend (JavaScript)
                    record_id = f"habit_{record.habit_id}"
                    session["completed_habits"] = session.get("completed_habits", [])
                    session["completed_habits"].append(record_id)

            return redirect(url_for("dashboard"))
        else:
            return "Invalid email or password", 401

    return render_template("signin.html")


@app.route("/dashboard")
def dashboard():
    if "user" in session:
        user = User.query.get(session["user"]["id"])
        activities = user.activities
        habits = user.user_habits
        activity_names = [a.name for a in activities]
        habit_names = [h.name for h in habits]
        print(habit_names)
        completed_habit_ids = [
            habit.id for habit in habits if habit.is_completed_today()
        ]  # Replace this with the appropriate method to check if the habit is completed today
        print(completed_habit_ids)
        return render_template(
            "dashboard.html",
            user=user,
            activity_names=activity_names,
            activities=activities,
            habit_names=habit_names,
            completed_habit_ids=completed_habit_ids,
        )
    else:
        return redirect(url_for("signin"))


@app.route("/add_activity", methods=["POST"])
def add_activity():
    if "user" in session:
        user_id = session["user"]["id"]
        activity_name = request.json.get("name")
        activity = Activity.query.filter_by(name=activity_name).first()
        if activity is None:
            # If not, create a new activity.
            activity = Activity(name=activity_name)
            db.session.add(activity)
        # Then, associate the user with the activity.
        user = User.query.get(user_id)
        user.activities.append(activity)
        db.session.commit()
        return jsonify({"id": activity.id, "name": activity.name}), 201
    else:
        return "Unauthorized", 401


@app.route("/add_habit", methods=["POST"])
def add_habit():
    if "user" in session:
        user_id = session["user"]["id"]
        new_habit = request.json.get("name")
        print(new_habit)
        habit = Habit.query.filter_by(name=new_habit).first()
        if habit is None:
            habit = Habit(name=new_habit)
            db.session.add(habit)
        user = User.query.get(user_id)
        user.user_habits.append(habit)
        db.session.commit()
        return redirect(
            url_for("dashboard")
        )  # Redirect to the dashboard after adding the habit
    return jsonify({"id": habit.id, "name": habit.name}), 201


@app.route("/save_record", methods=["POST"])
def save_record():
    if "user" in session:
        activity_id = request.json.get("activityId")
        user_id = session["user"]["id"]
        activity = Activity.query.filter(
            Activity.users.any(id=user_id), Activity.name == activity_id
        ).first()

        start_time = str(request.json.get("startTime"))[:-3]
        start_time = datetime.datetime.fromtimestamp(int(start_time))
        end_time = str(request.json.get("endTime"))[:-3]
        end_time = datetime.datetime.fromtimestamp(int(end_time))

        notes = request.json.get("notes")

        user_id = session["user"]["id"]
        elapsed_time = request.json.get("elapsedTime")
        new_record = ActivityRecord(
            start_time=start_time,
            end_time=end_time,
            notes=notes,
            activity_id=activity_id,
            user_id=user_id,
            elapsed_time=elapsed_time,
        )
        db.session.add(new_record)
        db.session.commit()

        return jsonify({"id": new_record.id}), 201
    else:
        return "Unauthorized", 401


@app.route("/get_activity_data/<activity_name>")
def get_activity_data(activity_name):
    # Fetch data for the activity from the database
    activity = Activity.query.filter_by(name=activity_name).first()
    if activity is not None:
        records = ActivityRecord.query.filter(
            ActivityRecord.activity_id == activity.id
        ).all()
        last_pt = str(records[-1].elapsed_time / 60000).split(".")
        last_pt[1] = str(round(float("." + last_pt[1]) * 60))
        if len(last_pt[1]) == 1:
            last_pt[1] = "0" + last_pt[1]
        last_pt = last_pt[0] + ":" + last_pt[1]

        total_time_ms = sum([record.elapsed_time for record in records])
        ten_k = total_time_ms / 36000000000
        percent = ten_k * 100
        percent = str(percent)[:5] + "%"
        total_time_min = total_time_ms / 60000
        str_time = str(total_time_min)
        decimal = str_time.find(".")
        minutes = int(str_time[:decimal])
        if minutes >= 60:
            hours = math.floor(minutes / 60)
            minutes = minutes % 60
        else:
            hours = "0"
        if len(str(minutes)) == 1:
            minutes = "0" + str(minutes)
        seconds = float(str_time[decimal:]) * 60
        seconds = math.floor(seconds)
        if len(str(seconds)) == 1:
            seconds = "0" + str(seconds)
        display_total_time = "{}:{}:{}".format(hours, minutes, seconds)
        notes = [record.notes for record in records]
        last_prac = notes[-1:][0].upper()
        print("last practice", last_pt)
        data = {
            "name": activity.name.upper(),
            "total_time": display_total_time,
            "percent": percent,
            "last_prac": last_prac,
            "last_pt": last_pt,
        }
    else:
        data = {}
    return jsonify(data)


@app.route("/mark_habit_completed/<string:habit_name>", methods=["POST"])
def mark_habit_completed(habit_name):
    if "user" in session:
        # the VPS time is UTC and we want to make sure things record locally
        now = datetime.datetime.now()
        user_id = session["user"]["id"]
        habit = Habit.query.filter_by(name=habit_name).first()

        # Check if the habit is already recorded for today
        today = now.date()
        existing_record = HabitRecord.query.filter_by(
            user_id=user_id, habit_id=habit.id, date_completed=today
        ).first()

        if not existing_record:
            # Record the completed habit for today
            habit_record = HabitRecord(
                user_id=user_id,
                habit_id=habit.id,
                time_completed=now.time(),
                date_completed=today,
            )
            db.session.add(habit_record)
            db.session.commit()

        return jsonify({"status": "success"}), 200

    else:
        return jsonify({"status": "error", "message": "User not logged in"}), 401


# THIS NEEDS WORK
@app.route("/unmark_habit_completed/<string:habit_name>", methods=["POST"])
def unmark_habit_completed(habit_name):
    if "user" in session:
        # user_id = session["user"]["id"]
        habit = Habit.query.filter_by(name=habit_name).first()
        delete_record(habit.id)
        # if not existing_record:
        #     # Record the completed habit for today
        #     habit_record = HabitRecord(user_id=user_id, habit_id=habit.id)
        #     db.session.add(habit_record)
        #     db.session.commit()

        return jsonify({"status": "success"}), 200

    else:
        return jsonify({"status": "error", "message": "User not logged in"}), 401


@app.route("/get_completed_habits", methods=["GET"])
def get_completed_habits():
    if "user" in session:
        user_id = session["user"]["id"]
        user_habits = HabitRecord.query.filter_by(
            user_id=user_id, date_completed=is_today()
        ).all()
        completed_habits = [habit.habit.name for habit in user_habits]
        return jsonify(completed_habits), 200
    return jsonify({"error": "User not logged in"}), 401


@app.route("/add_todo", methods=["POST"])
def add_todo():
    if "user" in session:
        user_id = session["user"]["id"]
        new_item = request.json.get("item")
        todo_item = ToDoItem(user_id=user_id, item=new_item)
        db.session.add(todo_item)
        db.session.commit()
        return jsonify({"id": todo_item.id, "item": todo_item.item}), 201
    return jsonify({"error": "User not logged in"}), 401


@app.route("/complete_todo/<int:todo_id>", methods=["POST"])
def complete_todo(todo_id):
    if "user" in session:
        user_id = session["user"]["id"]
        todo_item = ToDoItem.query.filter_by(id=todo_id, user_id=user_id).first()
        if todo_item:
            todo_item.completed = True
            todo_item.date_completed = datetime.datetime.now()
            db.session.commit()
            return jsonify({"message": "ToDo item marked as completed"}), 200
        return jsonify({"error": "ToDo item not found"}), 404
    return jsonify({"error": "User not logged in"}), 401


@app.route("/get_todos", methods=["GET"])
def get_todos():
    if "user" in session:
        user_id = session["user"]["id"]
        todo_items = ToDoItem.query.filter_by(user_id=user_id).all()
        todos = [
            {
                "id": item.id,
                "item": item.item,
                "completed": item.completed,
                "date_created": item.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_completed": item.date_completed.strftime("%Y-%m-%d %H:%M:%S")
                if item.date_completed
                else None,
            }
            for item in todo_items
        ]
        return jsonify({"todos": todos}), 200
    return jsonify({"error": "User not logged in"}), 401


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
