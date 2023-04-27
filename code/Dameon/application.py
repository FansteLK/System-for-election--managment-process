import os
import time

from configuration import Configuration

from sqlalchemy import and_,or_
from models import base,Election,Election_Participant,Vote,engine,session,orm
from redis import Redis
import datetime

os.environ['TZ']='Europe/Belgrade'
time.tzset()

with Redis(host=Configuration.REDIS_HOST) as redis:

 while (1):


    try:
     session = orm.scoped_session(orm.sessionmaker())(bind=engine)
     election = session.query(Election).filter(and_(Election.election_begining <= datetime.datetime.now(), \
     Election.election_ending >= datetime.datetime.now())).first()
     # elections=session.query(Election).all()
     # elections_json = [item.serialize for item in elections]
     #
     # print (elections_json)
     # if (election):
     #   print(election.serialize)
     # session.commit()
     #
     if (election):


        byteslist =redis.lrange(Configuration.REDIS_VOTES_LIST, 0, -1)
        redis.ltrim(Configuration.REDIS_VOTES_LIST,1,0)
        if (len(byteslist) != 0):
            for byte in byteslist:
                st=byte.decode("utf-8")

                args = [item.strip() for item in st.split(",")]
                vote_exist=session.query(Vote).filter(and_(Vote.IdElection==election.id,Vote.ballotGuid==args[0])).first()
                if (vote_exist):
                    vote=Vote(ballotGuid=args[0],IdElection=election.id,electionOfficialJmbg=args[2],reason="Duplicate ballot.",poll=args[1])

                else:
                    election_participant=session.query(Election_Participant).filter(and_(Election_Participant.IdElection==election.id,Election_Participant.pollnumber==args[1])).first()
                    if (not election_participant):
                        vote = Vote(ballotGuid=args[0],IdElection=election.id, electionOfficialJmbg=args[2], reason="Invalid poll number.", poll=args[1])
                    else:
                        vote = Vote(ballotGuid=args[0],IdElection=election.id, electionOfficialJmbg=args[2],  poll=args[1])

                session.add(vote)
                session.commit()
     session.commit()
    except Exception as e:
        print(e)









