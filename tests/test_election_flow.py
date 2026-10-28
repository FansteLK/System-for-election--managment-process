"""End-to-end flow across services: create an election, vote, process ballots, read results."""

import io
import json
from datetime import datetime, timedelta

import pytest

from election.daemon import worker
from election.models import Election, Vote, db, local_now

from .conftest import bearer


def create_participants(admin, token, names, individual):
    ids = []
    for name in names:
        response = admin.post(
            "/createParticipant", json={"name": name, "individual": individual}, headers=bearer(token)
        )
        assert response.status_code == 200
        ids.append(response.json["id"])
    return ids


def create_election(admin, token, start, end, individual, participants):
    return admin.post(
        "/createElection",
        json={
            "start": start.isoformat(),
            "end": end.isoformat(),
            "individual": individual,
            "participants": participants,
        },
        headers=bearer(token),
    )


def upload(station, token, csv_text):
    return station.post(
        "/vote",
        data={"file": (io.BytesIO(csv_text.encode()), "votes.csv")},
        headers=bearer(token),
        content_type="multipart/form-data",
    )


def drain(daemon_app, redis):
    """Process everything currently in the queue."""
    worker.run(daemon_app, redis, "votes", timeout=1, should_stop=lambda: redis.llen("votes") == 0)


def finish_election(admin_app, election_id):
    with admin_app.app_context():
        election = db.session.get(Election, election_id)
        election.end = local_now() - timedelta(seconds=1)
        db.session.commit()


def test_admin_endpoints_require_token(admin):
    response = admin.get("/getParticipants")
    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}


def test_officials_cannot_use_admin_endpoints(admin, official_token):
    assert admin.get("/getParticipants", headers=bearer(official_token)).status_code == 401


def test_create_participant_requires_fields(admin, admin_token):
    response = admin.post("/createParticipant", json={"name": "X"}, headers=bearer(admin_token))
    assert response.json == {"message": "Field individual is missing."}


def test_create_election_validation(admin, admin_token):
    parties = create_participants(admin, admin_token, ["A", "B"], individual=False)
    people = create_participants(admin, admin_token, ["P"], individual=True)
    now = datetime.now()

    def message(**overrides):
        args = dict(start=now + timedelta(days=1), end=now + timedelta(days=2), individual=False, participants=parties)
        args.update(overrides)
        return create_election(admin, admin_token, **args).json

    assert message(end=now) == {"message": "Invalid date and time."}
    assert message(participants=parties[:1]) == {"message": "Invalid participants."}
    assert message(participants=[*parties, people[0]]) == {"message": "Invalid participants."}
    assert message(participants=[*parties, 999]) == {"message": "Invalid participants."}
    assert message() == {"pollNumbers": [1, 2]}


@pytest.mark.parametrize(
    "start_offset, end_offset",
    [
        (12, 36),  # overlaps the end of the existing election
        (-12, 12),  # overlaps the start
        (6, 18),  # inside the existing election
        (-12, 48),  # fully contains the existing election (missed by the original version)
    ],
)
def test_overlapping_elections_rejected(admin, admin_token, start_offset, end_offset):
    parties = create_participants(admin, admin_token, ["A", "B"], individual=False)
    base = datetime(2030, 1, 1)
    assert create_election(admin, admin_token, base, base + timedelta(days=1), False, parties).status_code == 200
    response = create_election(
        admin, admin_token, base + timedelta(hours=start_offset), base + timedelta(hours=end_offset), False, parties
    )
    assert response.json == {"message": "Invalid date and time."}


@pytest.mark.parametrize(
    "csv_text, message",
    [
        ("guid-1,1\nguid-2\n", "Incorrect number of values on line 1."),
        ("guid-1,1,3\n", "Incorrect number of values on line 0."),
        ("guid-1,1\nguid-2,x\n", "Incorrect poll number on line 1."),
        ("guid-1,0\n", "Incorrect poll number on line 0."),
    ],
)
def test_vote_file_validation(station, official_token, redis, csv_text, message):
    response = upload(station, official_token, csv_text)
    assert response.json == {"message": message}
    # Nothing from a rejected file is queued.
    assert redis.llen("votes") == 0


def test_vote_requires_file(station, official_token):
    response = station.post("/vote", headers=bearer(official_token))
    assert response.json == {"message": "Field file is missing."}


def test_parliamentary_election_end_to_end(admin, admin_app, admin_token, station, official_token, redis, daemon_app):
    parties = create_participants(admin, admin_token, ["Alpha", "Beta", "Gamma"], individual=False)
    now = local_now()
    response = create_election(admin, admin_token, now - timedelta(minutes=1), now + timedelta(hours=1), False, parties)
    election_id = admin.get("/getElections", headers=bearer(admin_token)).json["elections"][0]["id"]

    ballots = [f"g{i},1" for i in range(60)] + [f"h{i},2" for i in range(38)] + [f"k{i},3" for i in range(2)]
    ballots += ["g0,2", "bad,9"]  # one duplicate, one unknown poll number
    assert upload(station, official_token, "\n".join(ballots)).status_code == 200
    drain(daemon_app, redis)

    response = admin.get(f"/getResults?id={election_id}", headers=bearer(admin_token))
    assert response.json == {"message": "Election is ongoing."}

    finish_election(admin_app, election_id)
    results = admin.get(f"/getResults?id={election_id}", headers=bearer(admin_token)).json
    seats = {p["name"]: p["result"] for p in results["participants"]}
    # Gamma has 2% of valid votes, below the 5% census. Invalid ballots are not counted.
    assert seats == {"Alpha": 153, "Beta": 97, "Gamma": 0}
    reasons = {v["ballotGuid"]: v["reason"] for v in results["invalidVotes"]}
    assert reasons == {"g0": "Duplicate ballot.", "bad": "Invalid poll number."}
    assert results["invalidVotes"][0]["electionOfficialJmbg"]


def test_presidential_election_shares(admin, admin_app, admin_token, station, official_token, redis, daemon_app):
    people = create_participants(admin, admin_token, ["Ana", "Bojan"], individual=True)
    now = local_now()
    create_election(admin, admin_token, now - timedelta(minutes=1), now + timedelta(hours=1), True, people)
    upload(station, official_token, "a,1\nb,1\nc,2\n")
    drain(daemon_app, redis)
    finish_election(admin_app, 1)

    results = admin.get("/getResults?id=1", headers=bearer(admin_token)).json
    assert results["participants"] == [
        {"pollNumber": 1, "name": "Ana", "result": 0.67},
        {"pollNumber": 2, "name": "Bojan", "result": 0.33},
    ]


def test_ballots_without_active_election_are_discarded(daemon_app, redis):
    redis.rpush("votes", json.dumps({"guid": "x", "poll": 1, "official": "0101990710008"}))
    drain(daemon_app, redis)
    assert redis.llen("votes") == 0
    with daemon_app.app_context():
        assert Vote.query.count() == 0


def test_results_for_unknown_election(admin, admin_token):
    assert admin.get("/getResults", headers=bearer(admin_token)).json == {"message": "Field id is missing."}
    response = admin.get("/getResults?id=42", headers=bearer(admin_token))
    assert response.json == {"message": "Election does not exist."}


def test_daemon_survives_redis_outage(daemon_app, monkeypatch):
    from redis.exceptions import ConnectionError as RedisConnectionError

    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    calls = []

    class FlakyRedis:
        def blpop(self, keys, timeout):
            calls.append(keys)
            if len(calls) == 1:
                raise RedisConnectionError("connection refused")
            return None

    worker.run(daemon_app, FlakyRedis(), "votes", should_stop=lambda: len(calls) >= 2)
    assert len(calls) == 2
