"""Authentication service: registration, login, token refresh and user deletion."""

from flask import Flask, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from election.authentication.models import Role, User, db
from election.authentication.validation import is_valid_jmbg, is_valid_password
from election.common import (
    error,
    first_missing_field,
    init_jwt,
    is_valid_email,
    register_health,
    role_required,
)
from election.config import AuthenticationConfig

ADMIN_ROLE = "admin"
OFFICIAL_ROLE = "user"


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(AuthenticationConfig)
    app.config.update(overrides or {})
    app.json.sort_keys = False
    db.init_app(app)
    init_jwt(app)
    register_health(app)

    @app.post("/register")
    def register():
        body = request.get_json(silent=True) or {}
        missing = first_missing_field(body, ["jmbg", "forename", "surname", "email", "password"])
        if missing:
            return error(f"Field {missing} is missing.")
        if not is_valid_jmbg(body["jmbg"]):
            return error("Invalid jmbg.")
        if not is_valid_email(body["email"]):
            return error("Invalid email.")
        if not is_valid_password(body["password"]):
            return error("Invalid password.")
        if User.query.filter_by(email=body["email"]).first():
            return error("Email already exists.")

        user = User(
            jmbg=body["jmbg"],
            forename=body["forename"],
            surname=body["surname"],
            email=body["email"],
            role=Role.query.filter_by(name=OFFICIAL_ROLE).one(),
        )
        user.set_password(body["password"])
        db.session.add(user)
        db.session.commit()
        return "", 200

    @app.post("/login")
    def login():
        body = request.get_json(silent=True) or {}
        missing = first_missing_field(body, ["email", "password"])
        if missing:
            return error(f"Field {missing} is missing.")
        if not is_valid_email(body["email"]):
            return error("Invalid email.")
        user = User.query.filter_by(email=body["email"]).first()
        if not user or not user.check_password(body["password"]):
            return error("Invalid credentials.")

        claims = user.token_claims()
        return {
            "accessToken": create_access_token(identity=user.email, additional_claims=claims),
            "refreshToken": create_refresh_token(identity=user.email, additional_claims=claims),
        }

    @app.post("/refresh")
    @jwt_required(refresh=True)
    def refresh():
        refresh_claims = get_jwt()
        claims = {key: refresh_claims[key] for key in ("forename", "surname", "jmbg", "roles")}
        return {"accessToken": create_access_token(identity=get_jwt_identity(), additional_claims=claims)}

    @app.post("/delete")
    @role_required(ADMIN_ROLE)
    def delete():
        body = request.get_json(silent=True) or {}
        if first_missing_field(body, ["email"]):
            return error("Field email is missing.")
        if not is_valid_email(body["email"]):
            return error("Invalid email.")
        user = User.query.filter_by(email=body["email"]).first()
        if not user:
            return error("Unknown user.")
        db.session.delete(user)
        db.session.commit()
        return "", 200

    return app


def init_database(app):
    """Create tables and seed the roles and the administrator account. Safe to run repeatedly."""
    with app.app_context():
        db.create_all()
        roles = {}
        for name in (ADMIN_ROLE, OFFICIAL_ROLE):
            roles[name] = Role.query.filter_by(name=name).first() or Role(name=name)
            db.session.add(roles[name])
        email = app.config["ADMIN_EMAIL"]
        if not User.query.filter_by(email=email).first():
            admin = User(
                jmbg="0000000000000",
                forename="admin",
                surname="admin",
                email=email,
                role=roles[ADMIN_ROLE],
            )
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
        db.session.commit()
