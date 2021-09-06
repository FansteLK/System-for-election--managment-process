
from flask import Flask,request,jsonify,make_response
from configuration import Configuration
from models import database,Participant,Election_Participant,Election,Vote
from flask_jwt_extended import JWTManager
from sqlalchemy import and_,or_,func;

import dateutil.parser as parser
import time

import re
import datetime


import os

application = Flask(__name__)
application.config.from_object(Configuration)
application.config['JSON_SORT_KEYS'] = False
jwt= JWTManager(application)
@application.route('/modifikacija')
def modifikacija():
   ime  = request.args.get('ime', None)
   id  = request.args.get('id', None)
   if (ime and id):
      participants= Election_Participant.query.filter(Election_Participant.IdElection==int (id)).join(Participant).filter(Participant.name.like(f"%{ime}%")).with_entities(Participant.id,Participant.name).all()
   elif (ime):
       participants=Participant.query.filter(Participant.name.like(f"%{ime}%")).with_entities(Participant.id,Participant.name).all()
   else:
       participants=    Election_Participant.query.filter(Election_Participant.IdElection==int (id)).join(Participant).with_entities(Participant.id,Participant.name).all()
   return str(participants)

if (__name__=="__main__"):
    database.init_app(application)
    os.environ['TZ'] = 'Europe/Belgrade'
    time.tzset()
    application.run(debug=True,host="0.0.0.0", port=5004)