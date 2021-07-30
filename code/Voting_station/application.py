
from flask import Flask,request,Response,jsonify,make_response
from configuration import Configuration

from flask_jwt_extended import JWTManager,create_access_token,jwt_required,create_refresh_token,get_jwt,get_jwt_identity,verify_jwt_in_request
from sqlalchemy import and_,or_;
from roleDecorator import roleCheck
from redis import Redis
import io
import os.path

import csv

application = Flask(__name__)
application.config.from_object(Configuration)
application.config['JSON_SORT_KEYS'] = False
jwt= JWTManager(application)

@application.route("/vote",methods=["POST"])
@roleCheck(role="user")
def vote():

    if not request.files.get('file', None):
        return make_response(jsonify(message="Field file is missing."), 400)
    content=request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)
    Claims = get_jwt()
    jmbg=Claims["jmbg"]
    # return (str(content))

    cnt=0

    for row in reader:
        if (len(row)<2):
            return make_response(jsonify(message=f"Incorrect number of values on line {cnt}."), 400)
        if (not row[0] or not row[1]):
            return make_response(jsonify(message=f"Incorrect number of values on line {cnt}."),400)
        guid=row[0]
        try:
         poll=int(row[1])
        except Exception as e:
            return make_response(jsonify(message=f"Incorrect poll number on line {cnt}."), 400)
        if (poll<0):
            return make_response(jsonify(message=f"Incorrect poll number on line {cnt}."),400)
        cnt += 1

        with Redis(host=Configuration.REDIS_HOST) as redis:

             redis.rpush(Configuration.REDIS_VOTES_LIST,f"{guid},{poll},{jmbg}")

    return Response("",200)



if (__name__=="__main__"):

    application.run(debug=True,host="0.0.0.0", port=5003)