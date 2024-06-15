
import os
import datetime
import uuid
from flask import Flask, Blueprint, current_app, render_template, request, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define a Blueprint named 'pages' for the 'habits' module with its templates and static files
pages = Blueprint("habits", __name__, template_folder="templates", static_folder="static")

# Context processor to make a date range function available in all templates
@pages.context_processor
def add_calc_date_range():
    def date_range(start: datetime.datetime):
        dates = [start + datetime.timedelta(days=diff) for diff in range(-3, 4)]
        return dates
    return {"date_range": date_range}

def today_at_midnight():
    today = datetime.datetime.today()
    return datetime.datetime(today.year, today.month, today.day)

@pages.route("/")
def index():
    date_str = request.args.get("date")
    if date_str:
        selected_date = datetime.datetime.fromisoformat(date_str)
    else:
        selected_date = today_at_midnight()

    habits_on_date = current_app.db.habits.find({"added": {"$lte": selected_date}})
    completions = [habit["habit"] for habit in current_app.db.completions.find({"date": selected_date})]
    return render_template("index.html", habits=habits_on_date, title="Habit Tracker - Home", completions=completions, selected_date=selected_date)

@pages.route("/add", methods=["GET", "POST"])
def add_habit():
    today = today_at_midnight()
    if request.form:
        current_app.db.habits.insert_one({"_id": uuid.uuid4().hex, "added": today, "name": request.form.get("habit")})
    return render_template("add_habit.html", title="Habit Tracker - Add Habit", selected_date=today)

@pages.route("/complete", methods=["POST"])
def complete():
    date_string = request.form.get("date")
    date = datetime.datetime.fromisoformat(date_string)
    habit = request.form.get("habitId")
    current_app.db.completions.insert_one({"date": date, "habit": habit})
    return redirect(url_for(".index", date=date_string))

def create_app():
    app = Flask(__name__)
    client = MongoClient(os.environ.get("MONGODB_URL"))
    app.db = client.tracker
    app.register_blueprint(pages)
    return app

# If this file is the main program, create and run the Flask application
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

