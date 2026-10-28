import fakeredis
import pytest

from election.admin import app as admin_module
from election.authentication import app as auth_module
from election.authentication.validation import jmbg_control_digit
from election.daemon import worker
from election.voting_station import app as station_module

SECRET = "test-secret-at-least-32-bytes-long!!"
ADMIN = {"email": "admin@admin.com", "password": "1"}


def make_jmbg(prefix="010199071000"):
    return prefix + str(jmbg_control_digit(prefix))


@pytest.fixture
def auth_app(tmp_path):
    app = auth_module.create_app(
        {"TESTING": True, "JWT_SECRET_KEY": SECRET, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/auth.db"}
    )
    auth_module.init_database(app)
    return app


@pytest.fixture
def auth(auth_app):
    return auth_app.test_client()


@pytest.fixture
def election_db(tmp_path):
    return f"sqlite:///{tmp_path}/election.db"


@pytest.fixture
def admin_app(election_db):
    app = admin_module.create_app({"TESTING": True, "JWT_SECRET_KEY": SECRET, "SQLALCHEMY_DATABASE_URI": election_db})
    admin_module.init_database(app)
    return app


@pytest.fixture
def admin(admin_app):
    return admin_app.test_client()


@pytest.fixture
def redis():
    return fakeredis.FakeRedis()


@pytest.fixture
def station(redis):
    app = station_module.create_app({"TESTING": True, "JWT_SECRET_KEY": SECRET}, redis_client=redis)
    return app.test_client()


@pytest.fixture
def daemon_app(election_db, admin_app):
    return worker.create_app({"SQLALCHEMY_DATABASE_URI": election_db})


def login(client, email, password):
    response = client.post("/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.json
    return response.json


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token(auth):
    return login(auth, **ADMIN)["accessToken"]


@pytest.fixture
def official_token(auth):
    user = {
        "jmbg": make_jmbg(),
        "forename": "Ana",
        "surname": "Anić",
        "email": "ana@example.com",
        "password": "Secret123",
    }
    assert auth.post("/register", json=user).status_code == 200
    return login(auth, user["email"], user["password"])["accessToken"]
