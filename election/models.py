"""Election database models, shared by the admin service and the vote daemon."""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

from election.config import TIMEZONE

db = SQLAlchemy()


def local_now():
    """Current time as a naive datetime in the election timezone (how times are stored)."""
    return datetime.now(TIMEZONE).replace(tzinfo=None)


class ElectionParticipant(db.Model):
    __tablename__ = "election_participants"

    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("participants.id"), primary_key=True)
    poll_number = db.Column(db.Integer, nullable=False)

    participant = db.relationship("Participant")


class Participant(db.Model):
    __tablename__ = "participants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    individual = db.Column(db.Boolean, nullable=False)

    def to_json(self):
        return {"id": self.id, "name": self.name, "individual": self.individual}


class Election(db.Model):
    __tablename__ = "elections"

    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    individual = db.Column(db.Boolean, nullable=False)
    entries = db.relationship(
        "ElectionParticipant", order_by=ElectionParticipant.poll_number, cascade="all, delete-orphan"
    )
    votes = db.relationship("Vote", back_populates="election")

    def to_json(self):
        return {
            "id": self.id,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "individual": self.individual,
            "participants": [{"id": e.participant.id, "name": e.participant.name} for e in self.entries],
        }

    @staticmethod
    def active(at):
        return Election.query.filter(Election.start <= at, Election.end >= at).first()


class Vote(db.Model):
    __tablename__ = "votes"
    __table_args__ = (db.Index("ix_votes_election_ballot", "election_id", "ballot_guid"),)

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    ballot_guid = db.Column(db.String(256), nullable=False)
    poll_number = db.Column(db.Integer, nullable=False)
    official_jmbg = db.Column(db.String(13), nullable=False)
    # NULL for a valid vote, otherwise the reason it was rejected.
    invalid_reason = db.Column(db.String(256))

    election = db.relationship("Election", back_populates="votes")
