import os
import uuid
import requests
import time
from flask import Blueprint, render_template, request, redirect, send_from_directory, session, current_app, url_for, flash
from utils import login_required, is_image, find_file_by_id


views_bp = Blueprint("views", __name__)
UPLOAD_DIR = "uploads"
PENDING_DIR = "pending"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PENDING_DIR, exist_ok=True)

@views_bp.route("/")
def home():
    return render_template("home.html")

@views_bp.route("/upload", methods=["POST"])
def upload():
    captcha_response = request.form.get("cf-turnstile-response")
    if not captcha_response:
        return {"error": "CAPTCHA missing"}, 400

    verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    payload = {
        "secret": current_app.config['TURNSTILE_SECRET_KEY'],
        "response": captcha_response,
        "remoteip": request.remote_addr
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    resp = requests.post(verify_url, data=payload, headers=headers).json()
    if not resp.get("success"):
        return {"error": "CAPTCHA failed"}, 400

    # continue with file saving logic...

    file = request.files.get("file")
    if not file:
        return {"error": "No file"}, 400

    if file.content_length > 100 * 1024 * 1024:
        return {"error": "Too large"}, 400

    file_id = uuid.uuid4().hex[:8]
    ext = os.path.splitext(file.filename)[1]
    filename = file_id + ext

    with open(os.path.join("pending", filename), 'wb') as f:
        while True:
            chunk = file.stream.read(1024*1024)  # 1MB chunks
            if not chunk:
                break
            f.write(chunk)
            time.sleep(0.01)  # 10ms delay per MB

    return {
        "file_id": file_id,
        "filename": filename,
        "is_image": is_image(filename)
    }



@views_bp.route("/upload_success")
def upload_success():
    file_id = session.pop("last_uploaded", None)
    if not file_id:
        return redirect("/")
    
    # Manually reconstruct the full filename from disk
    for fname in os.listdir(PENDING_DIR):
        if fname.startswith(file_id):
            filename = fname
            break
    else:
        return redirect("/")

    return render_template("home.html", uploaded=filename, is_image=is_image(filename))




#@views_bp.route("/upload_success")
#def upload_success():
 #   uploaded = session.pop("last_uploaded", None)
  #  if not uploaded:
   #     return redirect("/")
    #return render_template("home.html", uploaded=uploaded, is_image=is_image(uploaded))


#@views_bp.route("/upload_success")
#def upload_success():
   # file_id = session.pop("last_uploaded", None)
 #   ext = session.pop("last_ext", "")
  #  if not file_id:
   #     return redirect("/")
  #  filename = file_id + ext
 #   return render_template("home.html", uploaded=filename, is_image=is_image(filename))




@views_bp.route("/view/<file_id>")
def view_file(file_id):
    folder, filename = find_file_by_id(file_id)
    if not filename:
        return render_template("view.html", not_found=True)
    return render_template("view.html", 
                         file_id=file_id, 
                         is_image=is_image(filename), 
                         folder=folder, 
                         filename=filename)

@views_bp.route("/file/<folder>/<filename>")
def serve_file(folder, filename):
    if folder not in ["uploads", "pending"]:
        return "Forbidden", 403
    return send_from_directory(folder, filename)

@views_bp.route("/moderate")
@login_required
def moderate():
    files = os.listdir("pending")
    files_info = []

    for fname in files:
        path = os.path.join("pending", fname)
        timestamp = os.path.getmtime(path)  # last modified time
        files_info.append({
            "name": fname,
            "timestamp": timestamp,
            "time_str": time.strftime("%H:%M", time.localtime(timestamp)),
            "date_str": time.strftime("%Y-%m-%d", time.localtime(timestamp)),
        })

    files_info.sort(key=lambda x: x["timestamp"], reverse=True)  # newest first
    return render_template("moderate.html", files=files_info)


@views_bp.route("/approve/<file_id>")
@login_required
def approve(file_id):
    folder, filename = find_file_by_id(file_id)
    if folder:
        os.rename(os.path.join(folder, filename), os.path.join(UPLOAD_DIR, filename))
    return redirect("/moderate")

@views_bp.route("/delete/<file_id>")
@login_required
def delete(file_id):
    folder, filename = find_file_by_id(file_id)
    if folder:
        os.remove(os.path.join(folder, filename))
    referer = request.headers.get("Referer", "/moderate")
    return redirect(referer)

@views_bp.route("/faq")
def faq():
    return render_template("faq.html")


@views_bp.route("/policies")
def policies():
	return render_template("policies.html")

@views_bp.route("/changelog")
def changelog():
	return render_template("changelog.html")

@views_bp.route("/approved")
@login_required
def approved():
    files = sorted(
        os.listdir(UPLOAD_DIR),
        key=lambda f: os.path.getctime(os.path.join(UPLOAD_DIR, f)),
        reverse=True  # newest first
    )
    return render_template("approved.html", files=files)
