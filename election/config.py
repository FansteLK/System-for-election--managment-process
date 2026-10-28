"""Runtime configuration, read from environment variables."""

import os
from datetime import timedelta
from zoneinfo import ZoneInfo


def _env(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable {name}")
    return value


class BaseConfig:
    JWT_SECRET_KEY = _env("JWT_SECRET_KEY", "dev-only-secret-change-me-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}


class AuthenticationConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = _env("AUTH_DATABASE_URI", "sqlite:///authentication.db")
    ADMIN_EMAIL = _env("ADMIN_EMAIL", "admin@admin.com")
    ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "1")


class ElectionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = _env("ELECTION_DATABASE_URI", "sqlite:///election.db")
    NUMBER_OF_SEATS = int(_env("NUMBER_OF_SEATS", "250"))
    CENSUS_PERCENT = float(_env("CENSUS_PERCENT", "5"))


class RedisConfig:
    REDIS_HOST = _env("REDIS_HOST", "localhost")
    REDIS_PORT = int(_env("REDIS_PORT", "6379"))
    REDIS_VOTES_LIST = _env("REDIS_VOTES_LIST", "votes")


# Election times without an explicit offset are interpreted in this zone.
TIMEZONE = ZoneInfo(_env("ELECTION_TIMEZONE", "Europe/Belgrade"))
