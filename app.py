from flask import Flask, render_template, request, redirect, url_for, session, flash
import database, models
app = Flask(__name__)
app.secret_key = "dev-key"
database.init_db()
@app.route("/")
def home():
    return render_template("index.html", books=models.get_all_books())
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = models.verify_user(request.form.get("username"), request.form.get("password"))
        if user:
            session["user"] = user
            return redirect(url_for("home"))
        flash("Invalid", "danger")
    return render_template("login.html")
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        models.create_user(request.form.get("username"), request.form.get("password"), request.form.get("email"), request.form.get("username"))
        return redirect(url_for("login"))
    return render_template("register.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
if __name__ == "__main__":
    app.run(debug=True)