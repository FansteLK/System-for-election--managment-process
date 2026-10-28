"""Voting station service: election officials upload ballots as CSV, which are queued in Redis."""

import csv
import io
import json

from flask import Flask, request
from flask_jwt_extended import get_jwt
from redis import Redis

from election.common import error, init_jwt, register_health, role_required
from election.config import BaseConfig, RedisConfig

OFFICIAL_ROLE = "user"


def parse_ballots(text):
    """Parse CSV rows of `guid,poll_number`. Returns (ballots, error_message)."""
    ballots = []
    for line, row in enumerate(csv.reader(io.StringIO(text))):
        if len(row) != 2 or not all(value.strip() for value in row):
            return None, f"Incorrect number of values on line {line}."
        guid, poll = (value.strip() for value in row)
        if not poll.isdigit() or int(poll) <= 0:
            return None, f"Incorrect poll number on line {line}."
        ballots.append((guid, int(poll)))
    return ballots, None


def create_app(overrides=None, redis_client=None):
    app = Flask(__name__)
    app.config.from_object(BaseConfig)
    app.config.from_object(RedisConfig)
    app.config.update(overrides or {})
    init_jwt(app)
    register_health(app)
    redis = redis_client or Redis(host=app.config["REDIS_HOST"], port=app.config["REDIS_PORT"])

    @app.post("/vote")
    @role_required(OFFICIAL_ROLE)
    def vote():
        upload = request.files.get("file")
        if upload is None:
            return error("Field file is missing.")
        try:
            text = upload.stream.read().decode("utf-8")
        except UnicodeDecodeError:
            return error("Incorrect number of values on line 0.")
        ballots, message = parse_ballots(text)
        if message:
            return error(message)

        # Validate the whole file first so a bad line never leaves a partial upload queued.
        official = get_jwt()["jmbg"]
        if ballots:
            redis.rpush(
                app.config["REDIS_VOTES_LIST"],
                *(json.dumps({"guid": g, "poll": p, "official": official}) for g, p in ballots),
            )
        return "", 200

    return app
