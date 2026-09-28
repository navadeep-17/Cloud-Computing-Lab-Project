from __future__ import annotations

import functools
import sqlite3

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user() -> None:
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return

    g.user = get_db().execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


@bp.route("/register", methods=("GET", "POST"))
def register():
    if g.user is not None:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        error = None

        if len(name) < 2:
            error = "Please enter your name."
        elif "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            error = "Please enter a valid email address."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."

        if error is None:
            db = get_db()
            try:
                cursor = db.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password)),
                )
                user_id = cursor.lastrowid
                db.execute(
                    "INSERT INTO activities (user_id, action, details) VALUES (?, 'account_created', ?)",
                    (user_id, "Account created"),
                )
                db.commit()
            except sqlite3.IntegrityError:
                error = "An account with that email already exists."
            else:
                session.clear()
                session["user_id"] = user_id
                return redirect(url_for("index"))

        flash(error, "error")

    return render_template("register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user is not None:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        error = None
        if user is None or not check_password_hash(user["password_hash"], password):
            error = "Incorrect email or password."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            db.execute(
                "INSERT INTO activities (user_id, action, details) VALUES (?, 'login', ?)",
                (user["id"], "Signed in"),
            )
            db.commit()
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("index"))

        flash(error, "error")

    return render_template("login.html")


@bp.post("/logout")
@login_required
def logout():
    db = get_db()
    db.execute(
        "INSERT INTO activities (user_id, action, details) VALUES (?, 'logout', ?)",
        (g.user["id"], "Signed out"),
    )
    db.commit()
    session.clear()
    return redirect(url_for("auth.login"))
