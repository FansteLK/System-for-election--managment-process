"""Vote daemon: consumes ballots queued by voting stations and records them against the active election."""

import json
import logging
import signal
import time

from flask import Flask
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from election.config import ElectionConfig, RedisConfig
from election.models import Election, ElectionParticipant, Vote, db, local_now

log = logging.getLogger("election.daemon")

DUPLICATE = "Duplicate ballot."
INVALID_POLL = "Invalid poll number."


def process_ballot(ballot, now):
    """Record one ballot. Returns the stored Vote, or None if no election is active."""
    election = Election.active(now)
    if election is None:
        return None

    duplicate = Vote.query.filter_by(election_id=election.id, ballot_guid=ballot["guid"]).first()
    known_poll = ElectionParticipant.query.filter_by(election_id=election.id, poll_number=ballot["poll"]).first()
    if duplicate:
        reason = DUPLICATE
    elif not known_poll:
        reason = INVALID_POLL
    else:
        reason = None

    vote = Vote(
        election_id=election.id,
        ballot_guid=ballot["guid"],
        poll_number=ballot["poll"],
        official_jmbg=ballot["official"],
        invalid_reason=reason,
    )
    db.session.add(vote)
    db.session.commit()
    return vote


def run(app, redis, queue, timeout=5, should_stop=lambda: False):
    """Block on the Redis queue and process ballots one at a time.

    BLPOP removes each item atomically, so ballots pushed while another one
    is being processed are never lost (unlike LRANGE followed by LTRIM).
    """
    with app.app_context():
        while not should_stop():
            try:
                item = redis.blpop([queue], timeout=timeout)
            except RedisConnectionError as exc:
                log.warning("Redis unavailable (%s), retrying", exc)
                time.sleep(1)
                continue
            if item is None:
                continue
            try:
                vote = process_ballot(json.loads(item[1]), local_now())
                if vote is None:
                    log.info("Discarded ballot: no active election")
            except Exception:
                db.session.rollback()
                log.exception("Failed to process ballot %r", item[1])


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(ElectionConfig)
    app.config.from_object(RedisConfig)
    app.config.update(overrides or {})
    db.init_app(app)
    return app


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = create_app()
    redis = Redis(host=app.config["REDIS_HOST"], port=app.config["REDIS_PORT"])
    stopping = []
    signal.signal(signal.SIGTERM, lambda *_: stopping.append(True))
    log.info("Waiting for ballots on %s", app.config["REDIS_VOTES_LIST"])
    run(app, redis, app.config["REDIS_VOTES_LIST"], should_stop=lambda: bool(stopping))


if __name__ == "__main__":
    main()
