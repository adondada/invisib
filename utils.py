import os
from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper

def is_image(filename):
    return os.path.splitext(filename)[1].lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]

def find_file_by_id(file_id):
    for folder in ["uploads", "pending"]:
        for filename in os.listdir(folder):
            if filename.startswith(file_id):
                return folder, filename
    return None, None
