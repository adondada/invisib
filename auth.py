from flask import Blueprint, render_template, request, redirect, session, url_for
import os
from dotenv import load_dotenv  # Add this import

load_dotenv()  # Load environment variables from .env file

auth_bp = Blueprint("auth", __name__)
USERNAME = os.getenv("ADMIN_USERNAME", "admin")  # Get from environment
PASSWORD = os.getenv("ADMIN_PASSWORD")  # Required - no default

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if not PASSWORD:
        return "System not configured", 500
        
    if request.method == "POST":
        if (request.form["username"] == USERNAME and 
            request.form["password"] == PASSWORD):
            session["logged_in"] = True
            session.permanent = False  # Session expires when browser closes
            return redirect("/moderate")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()  # Clears session data
    return redirect("/")  # Redirect to the home page
