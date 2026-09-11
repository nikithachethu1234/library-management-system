import os
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import database
import models

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "library_super_secret_key_2026_x9k2m")

# Initialize database on startup
database.init_db()

# --- Auth Decorators ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        if session["user"].get("role") != "admin":
            flash("Access denied: Admin privileges required.", "danger")
            return redirect(url_for("user_dashboard"))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_globals():
    return {
        "current_user": session.get("user"),
        "current_year": datetime.now().year
    }

# --- General & Auth Routes ---

@app.route("/")
def index():
    if "user" in session:
        if session["user"]["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("user_dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please provide both username and password.", "danger")
            return render_template("login.html")

        user = models.authenticate_user(username, password)
        if user:
            session["user"] = {
                "id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"]
            }
            flash(f"Welcome back, {user['full_name']}!", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("user_dashboard"))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not (username and full_name and email and password):
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 4:
            flash("Password must be at least 4 characters long.", "danger")
            return render_template("register.html")

        if models.get_user_by_username(username):
            flash("Username already taken. Please choose another.", "danger")
            return render_template("register.html")

        if models.get_user_by_email(email):
            flash("Email address is already registered.", "danger")
            return render_template("register.html")

        user_id, err = models.create_user(username, password, full_name, email, role="user")
        if err:
            flash(f"Registration error: {err}", "danger")
            return render_template("register.html")

        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))

# --- Admin Routes ---

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    stats = models.get_admin_dashboard_stats()
    return render_template("admin/dashboard.html", stats=stats)

@app.route("/333")

@admin_required
def admin_books():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "")
    books = models.get_all_books(search_query=search, category=category)
    categories = models.get_all_categories()
    return render_template("admin/books.html", books=books, categories=categories, current_search=search, current_category=category)

@app.route("/admin/books/add", methods=["POST"])
@admin_required
def admin_add_book():
    isbn = request.form.get("isbn", "").strip()
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    category = request.form.get("category", "").strip()
    total_copies = request.form.get("total_copies", 1)
    description = request.form.get("description", "").strip()
    published_year = request.form.get("published_year") or None

    if not (isbn and title and author and category):
        flash("ISBN, Title, Author, and Category are required.", "danger")
        return redirect(url_for("admin_books"))

    if models.get_book_by_isbn(isbn):
        flash(f"A book with ISBN '{isbn}' already exists.", "danger")
        return redirect(url_for("admin_books"))

    book_id, err = models.add_book(isbn, title, author, category, total_copies, description, published_year)
    if err:
        flash(f"Error adding book: {err}", "danger")
    else:
        flash(f"Book '{title}' added successfully!", "success")

    return redirect(url_for("admin_books"))

@app.route("/admin/books/edit/<int:book_id>", methods=["POST"])
@admin_required
def admin_edit_book(book_id):
    isbn = request.form.get("isbn", "").strip()
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    category = request.form.get("category", "").strip()
    total_copies = request.form.get("total_copies", 1)
    description = request.form.get("description", "").strip()
    published_year = request.form.get("published_year") or None

    existing = models.get_book_by_isbn(isbn)
    if existing and existing["id"] != book_id:
        flash(f"Another book already uses ISBN '{isbn}'.", "danger")
        return redirect(url_for("admin_books"))

    success, err = models.update_book(book_id, isbn, title, author, category, total_copies, description, published_year)
    if success:
        flash(f"Book '{title}' updated successfully.", "success")
    else:
        flash(f"Failed to update book: {err}", "danger")

    return redirect(url_for("admin_books"))

@app.route("/admin/books/delete/<int:book_id>", methods=["POST"])
@admin_required
def admin_delete_book(book_id):
    book = models.get_book_by_id(book_id)
    title = book["title"] if book else "Book"
    success, err = models.delete_book(book_id)
    if success:
        flash(f"Book '{title}' was deleted successfully.", "success")
    else:
        flash(f"Cannot delete book: {err}", "danger")

    return redirect(url_for("admin_books"))

@app.route("/admin/issues")
@admin_required
def admin_issues():
    status_filter = request.args.get("status", "all")
    records = models.get_all_borrow_records(status_filter=status_filter)
    books = models.get_all_books()
    users = [u for u in models.get_all_users() if u["role"] == "user"]
    return render_template("admin/issue_return.html", records=records, books=books, users=users, current_status=status_filter)

@app.route("/admin/issue", methods=["POST"])
@admin_required
def admin_issue_book():
    book_id = request.form.get("book_id", type=int)
    user_id = request.form.get("user_id", type=int)
    days = request.form.get("days", default=14, type=int)

    if not book_id or not user_id:
        flash("Please select both a book and a user.", "danger")
        return redirect(url_for("admin_issues"))

    success, msg = models.issue_book(book_id, user_id, days)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")

    return redirect(url_for("admin_issues"))

@app.route("/admin/return/<int:record_id>", methods=["POST"])
@admin_required
def admin_return_book(record_id):
    success, msg = models.return_book(record_id)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(request.referrer or url_for("admin_issues"))

@app.route("/admin/users")
@admin_required
def admin_users():
    users = models.get_all_users()
    return render_template("admin/users.html", users=users)

@app.route("/admin/users/<int:user_id>")
@admin_required
def admin_user_details(user_id):
    user = models.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin_users"))
    history = models.get_user_borrows(user_id)
    return render_template("admin/user_details.html", user=user, history=history)

# --- Member / User Routes ---

@app.route("/user/dashboard")
@login_required
def user_dashboard():
    user_id = session["user"]["id"]
    stats = models.get_user_dashboard_stats(user_id)
    return render_template("user/dashboard.html", stats=stats)

@app.route("/user/books")
@login_required
def user_books():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "")
    books = models.get_all_books(search_query=search, category=category)
    categories = models.get_all_categories()
    user_borrows = models.get_user_borrows(session["user"]["id"], active_only=True)
    borrowed_book_ids = [b["book_id"] for b in user_borrows]

    return render_template(
        "user/books.html",
        books=books,
        categories=categories,
        current_search=search,
        current_category=category,
        borrowed_book_ids=borrowed_book_ids
    )

@app.route("/user/borrow/<int:book_id>", methods=["POST"])
@login_required
def user_borrow_book(book_id):
    user_id = session["user"]["id"]
    success, msg = models.issue_book(book_id, user_id, days=14)
    if success:
        flash(f"Success! {msg} Please return it within 14 days.", "success")
    else:
        flash(msg, "danger")
    return redirect(url_for("user_books"))

@app.route("/user/my-books")
@login_required
def user_my_books():
    user_id = session["user"]["id"]
    active_borrows = models.get_user_borrows(user_id, active_only=True)
    all_borrows = models.get_user_borrows(user_id, active_only=False)
    return render_template("user/my_books.html", active_borrows=active_borrows, all_borrows=all_borrows)
@app.route("/user/return/<int:record_id>", methods=["POST"])
@login_required
def user_return_book(record_id):
    record = models.get_borrow_record_by_id(record_id)
    if not record or record["user_id"] != session["user"]["id"]:
        flash("Unauthorized action or record not found.", "danger")
        return redirect(url_for("user_my_books"))

    success, msg = models.return_book(record_id)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for("user_my_books"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
