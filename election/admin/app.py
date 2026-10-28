"""Admin service: participants, elections and results."""

from datetime import datetime

from flask import Flask, request
from sqlalchemy import func

from election.admin.results import dhondt, vote_shares
from election.common import error, first_missing_field, init_jwt, register_health, role_required
from election.config import TIMEZONE, ElectionConfig
from election.models import Election, ElectionParticipant, Participant, Vote, db, local_now

ADMIN_ROLE = "admin"


def parse_datetime(value):
    """Parse an ISO 8601 string into a naive datetime in the election timezone."""
    if not isinstance(value, str):
        raise ValueError("not a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(TIMEZONE).replace(tzinfo=None)
    return parsed


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(ElectionConfig)
    app.config.update(overrides or {})
    app.json.sort_keys = False
    db.init_app(app)
    init_jwt(app)
    register_health(app)

    @app.post("/createParticipant")
    @role_required(ADMIN_ROLE)
    def create_participant():
        body = request.get_json(silent=True) or {}
        missing = first_missing_field(body, ["name", "individual"])
        if missing:
            return error(f"Field {missing} is missing.")
        participant = Participant(name=body["name"], individual=bool(body["individual"]))
        db.session.add(participant)
        db.session.commit()
        return {"id": participant.id}

    @app.get("/getParticipants")
    @role_required(ADMIN_ROLE)
    def get_participants():
        return {"participants": [p.to_json() for p in Participant.query.order_by(Participant.id)]}

    @app.post("/createElection")
    @role_required(ADMIN_ROLE)
    def create_election():
        body = request.get_json(silent=True) or {}
        missing = first_missing_field(body, ["start", "end", "individual", "participants"])
        if missing:
            return error(f"Field {missing} is missing.")

        try:
            start, end = parse_datetime(body["start"]), parse_datetime(body["end"])
        except ValueError:
            return error("Invalid date and time.")
        # Two intervals overlap unless one ends before the other starts.
        overlapping = Election.query.filter(Election.start <= end, Election.end >= start).first()
        if start >= end or overlapping:
            return error("Invalid date and time.")

        individual = bool(body["individual"])
        ids = body["participants"]
        if not isinstance(ids, list) or len(ids) < 2 or not all(isinstance(i, int) for i in ids):
            return error("Invalid participants.")
        participants = {p.id: p for p in Participant.query.filter(Participant.id.in_(ids))}
        if len(set(ids)) != len(ids) or any(
            pid not in participants or participants[pid].individual != individual for pid in ids
        ):
            return error("Invalid participants.")

        election = Election(start=start, end=end, individual=individual)
        election.entries = [
            ElectionParticipant(participant_id=pid, poll_number=i) for i, pid in enumerate(ids, start=1)
        ]
        db.session.add(election)
        db.session.commit()
        return {"pollNumbers": list(range(1, len(ids) + 1))}

    @app.get("/getElections")
    @role_required(ADMIN_ROLE)
    def get_elections():
        return {"elections": [e.to_json() for e in Election.query.order_by(Election.start)]}

    @app.get("/getResults")
    @role_required(ADMIN_ROLE)
    def get_results():
        election_id = request.args.get("id", "")
        if election_id == "":
            return error("Field id is missing.")
        election = db.session.get(Election, election_id) if election_id.isdigit() else None
        if election is None:
            return error("Election does not exist.")
        if election.end > local_now():
            return error("Election is ongoing.")

        valid_counts = dict(
            db.session.query(Vote.poll_number, func.count(Vote.id))
            .filter(Vote.election_id == election.id, Vote.invalid_reason.is_(None))
            .group_by(Vote.poll_number)
        )
        votes_by_poll = {e.poll_number: valid_counts.get(e.poll_number, 0) for e in election.entries}
        if election.individual:
            results = vote_shares(votes_by_poll, sum(votes_by_poll.values()))
        else:
            results = dhondt(votes_by_poll, app.config["NUMBER_OF_SEATS"], app.config["CENSUS_PERCENT"])

        invalid = Vote.query.filter(Vote.election_id == election.id, Vote.invalid_reason.isnot(None)).order_by(Vote.id)
        return {
            "participants": [
                {"pollNumber": e.poll_number, "name": e.participant.name, "result": results[e.poll_number]}
                for e in election.entries
            ],
            "invalidVotes": [
                {
                    "electionOfficialJmbg": v.official_jmbg,
                    "ballotGuid": v.ballot_guid,
                    "pollNumber": v.poll_number,
                    "reason": v.invalid_reason,
                }
                for v in invalid
            ],
        }

    return app


def init_database(app):
    with app.app_context():
        db.create_all()
