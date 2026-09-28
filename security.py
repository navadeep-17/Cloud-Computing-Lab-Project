from __future__ import annotations

import secrets
from hmac import compare_digest

from flask import Flask, abort, current_app, request, session

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def get_csrf_token() -> str:
    token = session.get("_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def init_app(app: Flask) -> None:
    app.config.setdefault("CSRF_ENABLED", True)

    @app.before_request
    def protect_csrf():
        if not current_app.config.get("CSRF_ENABLED", True) or request.method in SAFE_METHODS:
            return None

        expected = session.get("_csrf_token")
        provided = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
        if not expected or not provided or not compare_digest(expected, provided):
            abort(400, description="Invalid or missing CSRF token.")
        return None

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": get_csrf_token()}

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "frame-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'",
        )
        return response
