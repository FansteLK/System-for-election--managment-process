import datetime
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy

database= SQLAlchemy()

class Election_Participant(database.Model):
    __tablename__="election_participant"
    # id=database.Column(database.Integer,primary_key=True)
    IdParticipant=database.Column(database.Integer,database.ForeignKey("participants.id"),primary_key=True)
    IdElection=database.Column(database.Integer,database.ForeignKey("election.id"),primary_key=True)
    pollnumber=database.Column(database.Integer)


class Election(database.Model):
    __tablename__="election"
    id =database.Column(database.Integer,primary_key=True)
    election_begining=database.Column(database.DateTime,nullable=False, default=datetime.datetime.utcnow)
    election_ending=database.Column(database.DateTime,nullable=False, default=datetime.datetime.utcnow)
    individual=database.Column(database.Boolean,nullable=False)
    votes=database.relationship("Vote",back_populates="election")
    participants=database.relationship("Participant",secondary=Election_Participant.__table__,back_populates="elections")
    @property
    def serialize(self):
        if (self.individual==1):
            individual=True
        else:
            individual=False
        start=self.election_begining.strftime('%Y-%m-%d %H:%M:%S')
        end=self.election_ending.strftime('%Y-%m-%d %H:%M:%S')
        participants_json=[item.serialize_election for item in self.participants]
        return {
            'id': self.id,
            'start': start,
            'end':end,
            'individual': self.individual,
            "participants":participants_json
        }


class Participant(database.Model):
    __tablename__="participants"
    id=database.Column(database.Integer,primary_key=True)
    name=database.Column(database.String(256),nullable=False)
    individual=database.Column(database.Boolean,nullable=False)
    elections=database.relationship("Election", secondary=Election_Participant.__table__, back_populates="participants")
    def __repr__(self):

        return "{} {} {}".format(self.id,self.name,self.individual)

    @property
    def serialize(self):
        if (self.individual==1):
            individual=True
        else:
            individual=False
        return {
            'id': self.id,
            'name': self.name,
            'individual': individual
        }

    @property
    def serialize_election(self):

        return {
            'id': self.id,
            'name': self.name
        }
class Vote(database.Model):
    __tablename__="vote"
    id=database.Column(database.Integer,primary_key=True)
    electionOfficialJmbg=database.Column(database.String(13),nullable=False)
    reason = database.Column(database.String(256))
    poll = database.Column(database.Integer,nullable=False)
    election= database.relationship("Election", back_populates="votes")
    IdElection=database.Column(database.Integer,database.ForeignKey("election.id"),nullable=False)
    ballotGuid = database.Column(database.String(256))



