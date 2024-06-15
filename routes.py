import datetime
import uuid
from flask import Blueprint, current_app, render_template, request, redirect, url_for

# Define a Blueprint named 'pages' for the 'habits' module with its templates and static files
pages = Blueprint("habits", __name__, template_folder="templates", static_folder="static")

# Context processor to make a date range function available in all templates
@pages.context_processor
def add_calc_date_range():
    # Function to calculate a date range of one week centered around a start date
    def date_range(start: datetime.datetime):
        # List comprehension to generate dates from three days before to three days after the start date
        dates = [start + datetime.timedelta(days=diff) for diff in range(-3, 4)]
        return dates
    # Return the function in a dictionary so it can be accessed in templates
    return {"date_range": date_range}

# Helper function to get today's date at midnight
def today_at_midnight():
    today = datetime.datetime.today()
    # Return a datetime object for today with time set to midnight
    return datetime.datetime(today.year, today.month, today.day)

# Route for the index page
@pages.route("/")
def index():
    # Get the 'date' parameter from the URL query string
    date_str = request.args.get("date")
    # Parse the date string into a datetime object if provided, otherwise use today's date at midnight
    if date_str:
        selected_date = datetime.datetime.fromisoformat(date_str)
    else:
        selected_date = today_at_midnight()

    # Query the database for habits added on or before the selected date
    habits_on_date = current_app.db.habits.find({"added": {"$lte": selected_date}})

    # Query the database for completions on the selected date and extract the habit names
    completions = [
        habit["habit"]
        for habit in current_app.db.completions.find({"date": selected_date})
    ]
    # Render the index template with the queried data
    return render_template("index.html", habits=habits_on_date, title="Habit Tracker - Home", completions=completions, selected_date=selected_date)

# Route to add a new habit
@pages.route("/add", methods=["GET", "POST"])
def add_habit():
    today = today_at_midnight()
    
    # Check if the form data is present
    if request.form:
        # Insert a new habit into the database with a unique ID and today's date
        current_app.db.habits.insert_one(
            {"_id": uuid.uuid4().hex, "added": today, "name": request.form.get("habit")}
        )
    # Render the add habit template
    return render_template("add_habit.html", title="Habit Tracker - Add Habit", selected_date=today)

# Route to mark a habit as complete
@pages.route("/complete", methods=["POST"])
def complete():
    # Get the 'date' and 'habitId' from the form data
    date_string = request.form.get("date")
    date = datetime.datetime.fromisoformat(date_string)
    habit = request.form.get("habitId")
    # Insert a completion record into the database
    current_app.db.completions.insert_one({"date": date, "habit": habit})

    # Redirect to the index page with the selected date
    return redirect(url_for(".index", date=date_string))
