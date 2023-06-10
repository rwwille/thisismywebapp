from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import datetime


pymysql.install_as_MySQLdb()


app = Flask(__name__)
app.secret_key = "your secret key"  # replace with a real secret key

my_password = "Ohyeah8!"

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://root:{}@localhost/webapp".format(my_password)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    activites = db.relationship("Activity", backref="user", lazy=True)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # user = db.relationship("User", backref=db.backref("activities", lazy=True))


class ActivityRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    activity = db.relationship("Activity", backref=db.backref("records", lazy=True))


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
        session["email"] = email  # log the user in
        return redirect("/dashboard")
    return render_template("signup.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        # these will grab the email and password entered in the fields
        email = request.form.get("email")
        password = request.form.get("password")

        # using the email provided we search DB for record
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user"] = {"id": user.id, "email": user.email}
            # need to figure out why "new@new.com" comes up
            # print(session["email"])

            # trying to make select activty work
            # activities = Activity.query.filter_by(user_id=user.id).all()
            return redirect(url_for("dashboard"))
        else:
            return "Invalid email or password", 401

    return render_template("signin.html")


@app.route("/dashboard")
def dashboard():
    if "user" in session:
        user = User.query.get(session["user"]["id"])
        try:
            activities = [
                activity.name for activity in user.activities
            ]  # assuming activity is an object with a 'name' attribute
        except:
            activities = None
        return render_template("dashboard.html", user=user, activities=activities)
    else:
        return redirect(url_for("signin"))


@app.route("/add_activity", methods=["GET", "POST"])
def add_activity():
    if "user" in session:
        user_id = session["user"]["id"]
        # print(user_id)
        # print(session)
        activity_name = request.json.get("name")
        print(activity_name)

        new_activity = Activity(name=activity_name, user_id=user_id)
        db.session.add(new_activity)
        db.session.commit()

        return jsonify({"id": new_activity.id, "name": new_activity.name}), 201
    else:
        return "Unauthorized", 401


# @app.route("/add_activity", methods=["POST"])
# def add_activity():
#     if "user" in session:
#         user = User.query.get(session["user"]["id"])
#         print(user)
#         activity_name = request.json.get("newActivityName")
#         print("activtiy name = ", activity_name)
#         activity = Activity(name=activity_name, user_id=user.id)
#         db.session.add(activity)
#         db.session.commit()
#         return jsonify(activity.serialize()), 201
#     else:
#         return redirect(url_for("signin"))


@app.route("/add_record", methods=["POST"])
def add_record():
    if "user" in session:
        activity_id = request.json.get("activityId")

        start_time = str(request.json.get("startTime"))[:-3]
        start_time = datetime.datetime.fromtimestamp(int(start_time))

        end_time = str(request.json.get("endTime"))[:-3]
        end_time = datetime.datetime.fromtimestamp(int(end_time))

        notes = request.json.get("notes")

        user_id = session["user"]["id"]

        new_record = ActivityRecord(
            start_time=start_time,
            end_time=end_time,
            notes=notes,
            activity_id=activity_id,
            user_id=user_id,
        )
        db.session.add(new_record)
        db.session.commit()

        return jsonify({"id": new_record.id}), 201
    else:
        return "Unauthorized", 401


if __name__ == "__main__":
    app.run(debug=True)  # host="192.168.1.73"
