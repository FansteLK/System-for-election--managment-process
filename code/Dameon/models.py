import datetime
from configuration import Configuration
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa

base = declarative_base()
engine = sa.create_engine(Configuration.SQLALCHEMY_DATABASE_URI)
base.metadata.bind = engine
session = orm.scoped_session(orm.sessionmaker())(bind=engine)

class Election_Participant(base):
    __tablename__="election_participant"
    # id=sa.Column(sa.Integer,primary_key=True)
    IdParticipant=sa.Column(sa.Integer,sa.ForeignKey("participants.id"),primary_key=True)
    IdElection=sa.Column(sa.Integer,sa.ForeignKey("election.id"),primary_key=True)
    pollnumber=sa.Column(sa.Integer)


class Election(base):
    __tablename__="election"
    id =sa.Column(sa.Integer,primary_key=True)
    election_begining=sa.Column(sa.DateTime,nullable=False, default=datetime.datetime.utcnow)
    election_ending= sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    individual= sa.Column(sa.Boolean, nullable=False)
    votes= orm.relationship("Vote", back_populates="election")
    participants= orm.relationship("Participant", secondary=Election_Participant.__table__, back_populates="elections")
    @property
    def serialize(self):
        if (self.individual==1):
            individual=True
        else:
            individual=False
        start=self.election_begining.astimezone().isoformat()
        end=self.election_ending.astimezone().isoformat()
        participants_json=[item.serialize_election for item in self.participants]
        return {
            'id': self.id,
            'start': start,
            'end':end,
            'individual': self.individual,
            "participants":participants_json
        }





class Participant(base):
    __tablename__="participants"
    id= sa.Column(sa.Integer, primary_key=True)
    name= sa.Column(sa.String(256), nullable=False)
    individual= sa.Column(sa.Boolean, nullable=False)
    elections= orm.relationship("Election", secondary=Election_Participant.__table__, back_populates="participants")
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
class Vote(base):
    __tablename__="vote"
    id= sa.Column(sa.Integer, primary_key=True)
    electionOfficialJmbg= sa.Column(sa.String(13), nullable=False)
    reason= sa.Column(sa.String(256))
    poll=sa.Column(sa.Integer,nullable=False)
    election= orm.relationship("Election", back_populates="votes")
    IdElection= sa.Column(sa.Integer, sa.ForeignKey("election.id"), nullable=False)
    ballotGuid = sa.Column(sa.String(256))





