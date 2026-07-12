from flask import Flask, render_template, redirect, url_for, flash, request
from models import db, User, Task
from forms import RegisterForm, LoginForm, TaskForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import case
from datetime import date
import os
app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "mysecretkey")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskmanager.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()

    if form.validate_on_submit():

        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()

        if existing_email:
            return "Email already registered!"

        # Check if username already exists
        existing_username = User.query.filter_by(username=form.username.data).first()

        if existing_username:
            return "Username already taken!"

        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")

        return redirect(url_for("home"))

    return render_template("register.html", form=form)

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/login", methods=["GET", "POST"])
def login():

    # If user is already logged in, send them to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(
            email=form.email.data
        ).first()

        if user and user.check_password(form.password.data):

            login_user(user)

            flash("Welcome back!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)

@app.route("/dashboard")
@login_required
def dashboard():

    search = request.args.get("search", "")
    filter_by = request.args.get("filter", "all")
    sort_by = request.args.get("sort", "newest")
    # Statistics (all tasks)
    all_tasks = Task.query.filter_by(user_id=current_user.id).all()

    total_tasks = len(all_tasks)
    completed_tasks = sum(task.completed for task in all_tasks)
    pending_tasks = total_tasks - completed_tasks
    high_priority_tasks = sum(task.priority == "High" for task in all_tasks)

    # Query for displayed tasks
    query = Task.query.filter_by(user_id=current_user.id)

    # Search
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    # Filter
    if filter_by == "pending":
        query = query.filter_by(completed=False)

    elif filter_by == "completed":
        query = query.filter_by(completed=True)

    elif filter_by == "high":
        query = query.filter_by(priority="High")

    if sort_by == "newest":
        query = query.order_by(Task.id.desc())

    elif sort_by == "oldest":
        query = query.order_by(Task.id.asc())

    elif sort_by == "due":
        query = query.order_by(Task.due_date.asc())

    elif sort_by == "priority":

        priority_order = case(
        (Task.priority == "High", 1),
        (Task.priority == "Medium", 2),
        (Task.priority == "Low", 3),
        else_=4
    )

        query = query.order_by(priority_order)

    tasks = query.all()

    return render_template(
        "dashboard.html",
        tasks=tasks,
        search=search,
        filter_by=filter_by,
        sort_by=sort_by,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        high_priority_tasks=high_priority_tasks,
        today=date.today()
    )

@app.route("/task/new", methods=["GET", "POST"])
@login_required
def add_task():

    form = TaskForm()

    if form.validate_on_submit():

        task = Task(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )

        db.session.add(task)
        db.session.commit()
        flash("Task added successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("task_form.html", form=form)

@app.route("/task/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_task(id):

    task = Task.query.get_or_404(id)

    # Prevent users from editing other users' tasks
    if task.user_id != current_user.id:
        return "Unauthorized", 403

    form = TaskForm(obj=task)

    if form.validate_on_submit():

        task.title = form.title.data
        task.description = form.description.data
        task.priority = form.priority.data
        task.due_date = form.due_date.data

        db.session.commit()
        flash("Task updated successfully!", "info")

        return redirect(url_for("dashboard"))

    return render_template(
        "task_form.html",
        form=form
    )

@app.route("/task/delete/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get_or_404(id)

    # Prevent users from deleting others' tasks
    if task.user_id != current_user.id:
        return "Unauthorized", 403

    db.session.delete(task)
    db.session.commit()
    flash("Task deleted successfully!", "warning")

    return redirect(url_for("dashboard"))

@app.route("/task/toggle/<int:id>")
@login_required
def toggle_task(id):

    task = Task.query.get_or_404(id)

    # Prevent users from modifying others' tasks
    if task.user_id != current_user.id:
        return "Unauthorized", 403

    task.completed = not task.completed

    db.session.commit()
    flash("Task status updated!", "success")

    return redirect(url_for("dashboard"))

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)