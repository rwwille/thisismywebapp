from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import datetime

pymysql.install_as_MySQLdb()


app = Flask(__name__)
app.secret_key = "your secret key"  # replace with a real secret key

my_password = "Ohyeah8!"
# replace with your actual database URL
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://root:{}@localhost/timwa_database".format(my_password)

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auto_increment = True
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("activities", lazy=True))
    db.create_all()


class ActivityRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"))

    activity = db.relationship("Activity", backref=db.backref("records", lazy=True))


db.create_all()


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
        session["email"] = email  # log the user in
        return redirect("/dashboard")
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
        return render_template("dashboard.html", user=user, activities=user.activities)
    else:
        return redirect(url_for("signin"))


@app.route("/add_activity", methods=["POST"])
def add_activity():
    if "user" in session:
        user_id = session["user"]["id"]
        activity_name = request.json.get("name")

        new_activity = Activity(name=activity_name, user_id=user_id)
        db.session.add(new_activity)
        db.session.commit()

        return jsonify({"id": new_activity.id, "name": new_activity.name}), 201
    else:
        return "Unauthorized", 401


@app.route("/add_record", methods=["POST"])
def add_record():
    if "user" in session:
        activity_id = request.json.get("activityId")
        start_time = datetime.datetime.fromtimestamp(
            request.json.get("startTime") / 1000.0
        )
        end_time = datetime.datetime.fromtimestamp(request.json.get("endTime") / 1000.0)
        notes = request.json.get("notes")

        new_record = ActivityRecord(
            start_time=start_time,
            end_time=end_time,
            notes=notes,
            activity_id=activity_id,
        )
        db.session.add(new_record)
        db.session.commit()

        return jsonify({"id": new_record.id}), 201
    else:
        return "Unauthorized", 401


if __name__ == "__main__":
    app.run(debug=True)
