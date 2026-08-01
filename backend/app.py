"""
app.py
------
Flask backend for the Mayom Holdings admin panel.

Routes
======
Public (used by your GitHub Pages frontend / contact form):
    POST /api/enquiry        -> save a new lead from the "Send enquiry" form

Admin auth:
    GET  /login               -> login page
    POST /login                -> authenticate, start session
    GET  /logout               -> end session

Admin dashboard (all require login):
    GET  /dashboard             -> dashboard page
    GET  /api/leads             -> list leads (JSON)
    PATCH /api/leads/<id>       -> update a lead's status (JSON)
    DELETE /api/leads/<id>      -> delete a lead
    GET  /api/stats             -> summary counters (JSON)

Setup
=====
    pip install -r requirements.txt
    python database.py          # creates mayom.db
    python create_admin.py      # create your first admin user
    python app.py                # run the dev server
"""

import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS

from database import init_db
from models import Admin, Lead

app = Flask(__name__)

# IMPORTANT: in production, set this via an environment variable instead
# of hardcoding it, e.g.  export SECRET_KEY="something-long-and-random"
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this-in-production")

# Allow your GitHub Pages frontend to POST to /api/enquiry from a
# different origin. Lock this down to your real domain in production.
CORS(
    app,
    resources={r"/api/enquiry": {"origins": [
        "https://awesomemen200-sudo.github.io",
        "http://localhost:5000",
    ]}},
)

# Make sure the database/tables exist as soon as the app starts
init_db()


# ---------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------
def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------
# Public API — connect this to your website's contact form
# ---------------------------------------------------------------------
@app.route("/api/enquiry", methods=["POST"])
def submit_enquiry():
    """
    Called from mayomsholding frontend's contact form via fetch(), e.g.:

    fetch("https://YOUR-BACKEND-URL/api/enquiry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            full_name: "...", organisation: "...", email: "...",
            interest: "...", message: "..."
        })
    })
    """
    data = request.get_json(silent=True) or request.form

    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()

    if not full_name or not email:
        return jsonify({"ok": False, "error": "full_name and email are required"}), 400

    Lead.create(
        full_name=full_name,
        email=email,
        organisation=(data.get("organisation") or "").strip(),
        interest=(data.get("interest") or "").strip(),
        message=(data.get("message") or "").strip(),
    )
    return jsonify({"ok": True, "message": "Enquiry received"}), 201


# ---------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("dashboard") if session.get("admin_id") else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("admin_id"):
            return redirect(url_for("dashboard"))
        return render_template("login.html", error=None)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    admin = Admin.verify_password(username, password)
    if admin is None:
        return render_template("login.html", error="Invalid username or password"), 401

    # Successful login
    session.clear()
    session["admin_id"] = admin["id"]
    session["admin_username"] = admin["username"]
    Admin.update_last_login(admin["id"])

    next_url = request.args.get("next") or url_for("dashboard")
    return redirect(next_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------
# Dashboard (HTML)
# ---------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        admin_username=session.get("admin_username"),
        stats=Lead.stats(),
        leads=Lead.get_all(),
    )


# ---------------------------------------------------------------------
# Dashboard JSON API (used by dashboard.html's JS to update the table
# live without a full page reload)
# ---------------------------------------------------------------------
@app.route("/api/stats")
@login_required
def api_stats():
    return jsonify(Lead.stats())


@app.route("/api/leads")
@login_required
def api_leads():
    status = request.args.get("status")
    return jsonify(Lead.get_all(status=status))


@app.route("/api/leads/<int:lead_id>", methods=["PATCH"])
@login_required
def api_update_lead(lead_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("new", "contacted", "closed"):
        return jsonify({"ok": False, "error": "invalid status"}), 400
    Lead.update_status(lead_id, status)
    return jsonify({"ok": True})


@app.route("/api/leads/<int:lead_id>", methods=["DELETE"])
@login_required
def api_delete_lead(lead_id):
    Lead.delete(lead_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    # debug=True is for local development only — turn off in production
    app.run(debug=True, port=5000)