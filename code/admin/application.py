
from flask import Flask,request,jsonify,make_response
from configuration import Configuration
from models import database,Participant,Election_Participant,Election,Vote
from flask_jwt_extended import JWTManager
from sqlalchemy import and_,or_,func;
from roleDecorator import roleCheck
import dateutil.parser as parser
import time

import re
import datetime


import os

application = Flask(__name__)
application.config.from_object(Configuration)
application.config['JSON_SORT_KEYS'] = False
jwt= JWTManager(application)
def validate_iso8601(str_val,match_iso8601):
    try:
        if match_iso8601( str_val ) is not None:
            return True
    except:
        pass
    return False
def check_regex(start,end):
    regex = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
    match_iso8601 = re.compile(regex).match
    if (not validate_iso8601(start,match_iso8601) or not validate_iso8601(end,match_iso8601)) :
        return False
    return True;

@application.route("/createParticipant",methods=["POST"])
@roleCheck(role="admin" )
def createParticipant():

    name= request.json.get("name", "");
    individual = request.json.get("individual", "");
    fieldname = "";
    if (len(name) == 0):
        fieldname = "name";
    if (individual=="" and fieldname == ""):
        fieldname = "individual"
    if (fieldname != ""):
        return make_response(jsonify(message=f"Field {fieldname} is missing."), 400)
    participant = Participant(name=name,individual=individual)
    database.session.add(participant)
    database.session.commit()
    return make_response(jsonify(id=participant.id),200)

@application.route("/getParticipants",methods=["GET"])
@roleCheck(role="admin" )
def getParticipants():

    participants=Participant.query.all()


    participants_json= [item.serialize for item in participants]

    return make_response(jsonify(participants=participants_json),200)

@application.route("/createElection",methods=["POST"])
@roleCheck(role="admin")
def createElection():

    start = request.json.get("start", "");
    end = request.json.get("end", "");
    individual = request.json.get("individual", "");
    participants=request.json.get("participants","none");
    fieldname = "";
    if (len(start) == 0):
        fieldname = "start";
    if (len(end)==0 and fieldname == ""):
        fieldname = "end"
    if (individual == "" and fieldname == ""):
        fieldname = "individual"

    if ( participants=="none" and fieldname == ""):
            fieldname = "participants"
    if (fieldname != ""):
        return make_response(jsonify(message=f"Field {fieldname} is missing."), 400)
    # if (not check_regex(start,end)):
    #    return make_response(jsonify(message="Invalid date and time."),400)
    try:
     ts_start = parser.isoparse(start)
     ts_start.replace(tzinfo=None)
     ts_end=parser.isoparse(end)
     ts_end.replace(tzinfo=None)
    except Exception as e:
     return make_response(jsonify(message="Invalid date and time."),400)

    # ts_start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    # ts_end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")

    if (ts_start>ts_end) :
        return make_response(jsonify(message="Invalid date and time."),400)
    elections=Election.query.filter(
        and_(Election.election_begining <= ts_start, Election.election_ending >= ts_start)).all()

    if (elections):
        return make_response(jsonify(message="Invalid date and time."),400)
    elections = Election.query.filter(
        and_(Election.election_begining <= ts_end, Election.election_ending >= ts_end)).all()
    if (elections):
        return make_response(jsonify(message="Invalid date and time."),400)
    election = Election(election_begining=ts_start,\
                        election_ending=ts_end, individual=individual)
    database.session.add(election)
    # database.session.commit()
    election_participants=[]
    if (len(participants)<2):
        return make_response(jsonify(message="Invalid participants."), 400)
    cnt=1
    for participant in participants:
        participant_exist=Participant.query.filter(Participant.id==participant).first()
        if (not participant_exist):
            return make_response(jsonify(message="Invalid participants."),400)
        if (participant_exist.individual!=election.individual):
            return make_response(jsonify(message="Invalid participants."), 400)
        election_participants.append(Election_Participant(IdElection=election.id,IdParticipant=participant,pollnumber=cnt))
        cnt+=1
    database.session.add_all(election_participants)
    database.session.commit()
    list=[*range(0+1,len(election_participants)+1)]
    return make_response(jsonify(pollNumbers=list),200)

@application.route("/getElections",methods=["GET"])
@roleCheck(role="admin")
def getElections():


    elections=Election.query.all()

    elections_json= [item.serialize for item in elections]

    return make_response(jsonify(elections=elections_json),200)


@application.route("/getResults",methods=["GET"])
@application.route("/getResults<id>",methods=["GET"])
@roleCheck ( role="admin" )
def getResults():
    print (datetime.datetime.now())
    id=request.args.get('id',"")
    if ( id==""):
     return make_response(jsonify(message="Field id is missing."),400)
    election_exist = Election.query.filter(Election.id==id).first()
    if (not election_exist):

        return make_response(jsonify(message="Election does not exist."), 400)
    election=Election.query.filter(Election.id==id).first()
    # election = Election.query.filter(and_(Election.election_ending <= datetime.datetime.now(),Election.id==id)).first()
    # if (not election):
    #
    #     return make_response(jsonify(message="Election is ongoing."), 400)
    legal_votes=[]
    illegal_votes=[]
    polls=set()
    number_of_votes=Vote.query.filter(Vote.IdElection==election.id).count()

    illegal_votes_objects=Vote.query.filter(and_(Vote.IdElection==election.id,Vote.reason!="")).all()
    for i in range(0,len(illegal_votes_objects)):
        vote = \
            {
                "electionOfficialJmbg": illegal_votes_objects[i].electionOfficialJmbg,
                "ballotGuid": illegal_votes_objects[i].ballotGuid,
                "pollNumber": illegal_votes_objects[i].poll,
                "reason": illegal_votes_objects[i].reason

            }
        illegal_votes.append(vote)
    count = func.count(Vote.poll).label("count")
    count_votes = Vote.query.filter(Vote.IdElection == election.id).group_by(Vote.poll).with_entities(Vote.poll,\
                                                                                                      count).all()
    # count_votes = Vote.query.filter(Vote.IdElection == election.id).group_by(Vote.poll).with_entities(Vote.poll, \
    #                                                                                                   count).order_by(
    #     database.desc("count")).all()
    if (election.individual):

        for l in range(0,len(count_votes)):

            election_participant=Election_Participant.query.filter(and_(Election_Participant.IdElection==election.id),Election_Participant.pollnumber==count_votes[l].poll).first()
            if (not election_participant):
                continue
            participant=Participant.query.filter(Participant.id==election_participant.IdParticipant).first()

            result=round(count_votes[l].count/number_of_votes, 2)

            vote=\
                {
                    "pollNumber":count_votes[l].poll,
                    "name":participant.name,
                    "result":result
                }
            legal_votes.append(vote)

    else:
        seats_by_polls=dhondts_system(count_votes,Configuration.CENSUS,Configuration.NUMBER_OF_SEATS,number_of_votes)

        for l in range(0, len(count_votes)):
            found=False
            election_participant = Election_Participant.query.filter(
                and_(Election_Participant.IdElection == election.id),
                Election_Participant.pollnumber == count_votes[l].poll).first()
            if (not election_participant):
                continue
            participant = Participant.query.filter(Participant.id == election_participant.IdParticipant).first()
            for l1 in range (0,len(seats_by_polls)):
                if (seats_by_polls[l1]["poll"]==count_votes[l].poll):
                    found=True
                    break
            if (found):
             vote = \
                {
                    "pollNumber": count_votes[l].poll,
                    "name": participant.name,
                    "result": seats_by_polls[l1]["seats"]
                }
            else:
                vote = \
                    {
                        "pollNumber": count_votes[l].poll,
                        "name": participant.name,
                        "result": 0
                    }

            legal_votes.append(vote)

    return make_response(jsonify(participants=legal_votes, invalidVotes=illegal_votes), 200)
def dhondts_system(counts,census,seats,number_of_votes):
    census = (census / 100 * number_of_votes)
    census_count_votes = []
    number_of_seats =[]
    for i in range(0, len(counts)):
        if (counts[i].count>census):
            census_count_votes.append(counts[i])

            number_of_seats.append( {
            "seats":0,
            "poll":counts[i].poll
        })
    number_of_divides=[0]*len(census_count_votes)
    cnt=1
    while(seats>0):
        max=-1
        max_index=-1
        for j in range (0,len(census_count_votes)):

            votes_left=census_count_votes[j].count/(number_of_divides[j]+1)
            if (votes_left>max):
                max=votes_left
                max_index=j
        # print (f"Sediste broj {cnt} je uzela stranka pod rednim brojem {number_of_seats[max_index]['poll']}")
        number_of_divides[max_index] += 1
        number_of_seats[max_index]["seats"] += 1
        seats-=1
        cnt+=1

    return number_of_seats

@application.route("/time",methods=["GET"])
def getTime():

    return str(datetime.datetime.now())





if (__name__=="__main__"):
    database.init_app(application)
    os.environ['TZ'] = 'Europe/Belgrade'
    time.tzset()
    application.run(debug=True,host="0.0.0.0", port=5001)