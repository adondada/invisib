import os
from flask import Flask, redirect, url_for, flash, render_template, session
from auth import auth_bp
from views import views_bp
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()


app = Flask(__name__)
app.secret_key = os.environ.get("KEY")

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# reCAPTCHA Configuration
app.config['RECAPTCHA_SITE_KEY'] = os.environ.get('RECAPTCHA_SITE_KEY')
app.config['RECAPTCHA_SECRET_KEY'] = os.environ.get('RECAPTCHA_SECRET_KEY')

#cf captcha
app.config['TURNSTILE_SITE_KEY'] = os.environ.get("TURNSTILE_SITE_KEY")
app.config['TURNSTILE_SECRET_KEY'] = os.environ.get("TURNSTILE_SECRET_KEY")



# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(views_bp)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

if __name__ == "__main__":
    # Make Flask accessible externally and use port 80
    app.run(host='0.0.0.0', port=80, debug=False)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

