"""Helpers shared by the HTTP services."""

import re
from functools import wraps

from flask import jsonify
from flask_jwt_extended import JWTManager, get_jwt, verify_jwt_in_request

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def error(message, status=400):
    return jsonify(message=message), status


def is_valid_email(email):
    return len(email) <= 256 and EMAIL_PATTERN.match(email) is not None


def first_missing_field(body, fields):
    """Return the first field that is absent or an empty string, in the given order."""
    for field in fields:
        value = body.get(field)
        if value is None or (isinstance(value, str) and len(value) == 0):
            return field
    return None


def init_jwt(app):
    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def missing_header(_reason):
        return jsonify(msg="Missing Authorization Header"), 401

    return jwt


def role_required(role):
    """Allow the request only if the access token carries `role`."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if role not in get_jwt().get("roles", []):
                return jsonify(msg="Missing Authorization Header"), 401
            return view(*args, **kwargs)

        return wrapper

    return decorator


def register_health(app):
    @app.get("/health")
    def health():
        return {"status": "ok"}
