from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import datetime
import math

pymysql.install_as_MySQLdb()


app = Flask(__name__)
app.secret_key = "a very secret key"

password = " "

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://root:{}@localhost/timwa_62523".format(
    password
)  # web_app_live for local machine
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# The UserActivity table is created by db.Table, not db.Model.
# This table does not need an id field, because it's a junction table.
UserActivity = db.Table(
    "user_activity",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column(
        "activity_id", db.Integer, db.ForeignKey("activity.id"), primary_key=True
    ),
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    # The activities field is now a relationship field.
    activities = db.relationship(
        "Activity", secondary=UserActivity, backref=db.backref("users", lazy=True)
    )


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


with app.app_context():
    db.create_all()


def get_activity_id(activity_name):
    activity = Activity.query.filter_by(name=activity_name).first()
    if activity:
        return activity.id
    else:
        return None


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
            return redirect(url_for("dashboard"))
        else:
            return "Invalid email or password", 401

    return render_template("signin.html")


@app.route("/dashboard")
def dashboard():
    if "user" in session:
        user = User.query.get(session["user"]["id"])
        activities = user.activities  # Access the user's activities
        activity_names = [a.name for a in activities]  # Get the names of the activities
        return render_template(
            "dashboard.html",
            user=user,
            activity_names=activity_names,
            activities=activities,
        )

    else:
        return redirect(url_for("signin"))


@app.route("/add_activity", methods=["GET", "POST"])
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


@app.route("/add_record", methods=["POST"])
def add_record():
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


if __name__ == "__main__":
    app.run(debug=True)  # host="0.0.0.0"
