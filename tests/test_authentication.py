import pytest
from flask_jwt_extended import decode_token

from election.authentication.models import User
from election.authentication.validation import is_valid_jmbg, is_valid_password

from .conftest import ADMIN, bearer, login, make_jmbg

VALID_USER = {
    "jmbg": make_jmbg(),
    "forename": "Petar",
    "surname": "Petrović",
    "email": "petar@example.com",
    "password": "Password1",
}


@pytest.mark.parametrize(
    "jmbg, valid",
    [
        (make_jmbg("010199071000"), True),
        (make_jmbg("310899071000"), True),  # 31 August exists
        (make_jmbg("310999071000"), False),  # 31 September does not
        (make_jmbg("290200071000"), True),  # 2000 was a leap year
        (make_jmbg("290299971000"), False),  # 1999 was not
        (make_jmbg("010199069000"), False),  # region outside Serbia
        (make_jmbg("011399071000"), False),  # month 13
        (make_jmbg("000199071000"), False),  # day 0
        ("0101990710001", False),  # wrong control digit
        ("01019907100a3", False),
        ("123", False),
    ],
)
def test_jmbg_validation(jmbg, valid):
    assert is_valid_jmbg(jmbg) is valid


@pytest.mark.parametrize(
    "password, valid",
    [("Password1", True), ("password1", False), ("PASSWORD1", False), ("Password", False), ("Pa1", False)],
)
def test_password_validation(password, valid):
    assert is_valid_password(password) is valid


@pytest.mark.parametrize("field", ["jmbg", "forename", "surname", "email", "password"])
def test_register_reports_first_missing_field(auth, field):
    body = {**VALID_USER, field: ""}
    response = auth.post("/register", json=body)
    assert response.status_code == 400
    assert response.json == {"message": f"Field {field} is missing."}


@pytest.mark.parametrize(
    "change, message",
    [
        ({"jmbg": "1234567890123"}, "Invalid jmbg."),
        ({"email": "not-an-email"}, "Invalid email."),
        ({"password": "short"}, "Invalid password."),
    ],
)
def test_register_validation_errors(auth, change, message):
    response = auth.post("/register", json={**VALID_USER, **change})
    assert response.status_code == 400
    assert response.json == {"message": message}


def test_register_rejects_duplicate_email(auth):
    assert auth.post("/register", json=VALID_USER).status_code == 200
    response = auth.post("/register", json=VALID_USER)
    assert response.json == {"message": "Email already exists."}


def test_passwords_are_hashed(auth, auth_app):
    auth.post("/register", json=VALID_USER)
    with auth_app.app_context():
        user = User.query.filter_by(email=VALID_USER["email"]).one()
        assert user.password_hash != VALID_USER["password"]
        assert user.check_password(VALID_USER["password"])


def test_login_returns_tokens_with_user_claims(auth, auth_app):
    auth.post("/register", json=VALID_USER)
    tokens = login(auth, VALID_USER["email"], VALID_USER["password"])
    with auth_app.app_context():
        claims = decode_token(tokens["accessToken"])
    assert claims["sub"] == VALID_USER["email"]
    assert claims["jmbg"] == VALID_USER["jmbg"]
    assert claims["roles"] == ["user"]


def test_login_rejects_wrong_password(auth):
    auth.post("/register", json=VALID_USER)
    response = auth.post("/login", json={"email": VALID_USER["email"], "password": "Wrong1234"})
    assert response.json == {"message": "Invalid credentials."}


def test_refresh_issues_new_access_token(auth):
    refresh_token = login(auth, **ADMIN)["refreshToken"]
    response = auth.post("/refresh", headers=bearer(refresh_token))
    assert response.status_code == 200
    assert "accessToken" in response.json


def test_refresh_requires_header(auth):
    response = auth.post("/refresh")
    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}


def test_admin_can_delete_user(auth, admin_token):
    auth.post("/register", json=VALID_USER)
    response = auth.post("/delete", json={"email": VALID_USER["email"]}, headers=bearer(admin_token))
    assert response.status_code == 200
    response = auth.post("/delete", json={"email": VALID_USER["email"]}, headers=bearer(admin_token))
    assert response.json == {"message": "Unknown user."}


def test_official_cannot_delete_users(auth, official_token):
    response = auth.post("/delete", json={"email": ADMIN["email"]}, headers=bearer(official_token))
    assert response.status_code == 401


def test_seeding_is_idempotent(auth_app):
    from election.authentication.app import init_database

    init_database(auth_app)
    with auth_app.app_context():
        assert User.query.filter_by(email=ADMIN["email"]).count() == 1
