
from flask import Flask,request,Response,jsonify,make_response
from configuration import Configuration
from models import database,User,Role
from email.utils import  parseaddr
from flask_jwt_extended import JWTManager,create_access_token,jwt_required,create_refresh_token,get_jwt,get_jwt_identity,verify_jwt_in_request
from sqlalchemy import and_,or_;
import re
from roleDecorator import roleCheck
application = Flask(__name__)
application.config.from_object(Configuration)
application.config['JSON_SORT_KEYS'] = False
def checksum(jmbg,control_number):
    c0=int(jmbg[0])
    c1=int(jmbg[1])
    c2=int(jmbg[2])
    c3 =int(jmbg[3])
    c4 =int(jmbg[4])
    c5 =int(jmbg[5])
    c6=int(jmbg[6])
    c7 =int(jmbg[7])
    c8 =int(jmbg[8])
    c9 =int(jmbg[9])
    c10=int(jmbg[10])
    c11 =int(jmbg[11])
    c12=11-((7*(c0+c6)+6*(c1+c7)+5*(c2+c8)+4*(c3+c9)+3*(c4+c10)+2*(c5+c11))%11)
    return (c12==control_number)


def leap_year(year):
    if ((year%4==0) and not((year%100==0) and (year%400!=0))):
        return True;
    return False;
def jmbg_check(jmbg):
    if len(jmbg)!=13:
        return False
    day=jmbg[0:2];
    month=jmbg[2:4]
    year=jmbg[4:7]
    region=jmbg[7:9]
    unique_number=jmbg[9:12]
    control_number=jmbg[12]
    checked_day=day.isnumeric()
    checked_month=month.isnumeric()
    checked_year=year.isnumeric()
    checked_region=region.isnumeric();
    checked_unique_number=unique_number.isnumeric();
    checked_control_number=control_number.isnumeric();
    thirty_one_days=[1,3,5,7,8,10,12]
    thirty_days=[4,6,8,11]
    if (checked_day==False or checked_month==False or checked_year==False or checked_region==False or checked_unique_number==False or checked_control_number==False):
       return False;
    day=int(day)
    month=int(month)
    year=int(year)
    region=int(region)
    unique_number=int(unique_number)
    control_number=int(control_number)
    # upper_limit_days= 0;
    if (year<900):
       year+=2000;
    else:
      year+1000

    if (month<0 or  month>12):
       return False;

    if (month in thirty_days):
        upper_limit_days=30
    elif (month in thirty_one_days):
        upper_limit_days=31
    else:
        if (leap_year(year)):
            upper_limit_days=29
        else:
            upper_limit_days=28
    if (day<0 or day>upper_limit_days):
        return False
    if (region<70):
        return False
    return checksum(jmbg,control_number)
def  password_check(password):
    if (len(password)<8 or len(password)>255):
        return False
    if (not re.findall("[a-z]",password)):
        return False
    if (not re.findall("[A-Z]",password)):
        return False
    if (not re.findall(("[0-9]"),password)):
        return False
    return True
def  adding_user_to_database(user):
    database.session.add(user)
    database.session.commit()

def check_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if (re.match(regex, email)):
        return True

    else:
        return False
@application.route("/register",methods=["POST"])
def register():
    jmbg =request.json.get("jmbg","")
    email=request.json.get("email","");
    password = request.json.get("password", "");
    surname = request.json.get("surname", "");
    forename = request.json.get("forename", "");
    fieldname="";
    if (len(jmbg) == 0 and fieldname == ""):
        fieldname = "jmbg"
    if (len(forename) == 0 and fieldname == ""):
        fieldname = "forename"
    if (len(surname) == 0 and fieldname == ""):
        fieldname = "surname"
    if (len(email)==0 and fieldname==""):
        fieldname="email";
    if (len(password)==0 and fieldname==""):
        fieldname="password"

    if (fieldname!=""):
        return make_response(jsonify(message=f"Field {fieldname} is missing."), 400)
    if (not jmbg_check(jmbg)):
        return make_response(jsonify(message="Invalid jmbg."),400)
    if (not check_email(email)):
        return make_response(jsonify(message="Invalid email."), 400)
    if (not password_check(password)):
        return make_response(jsonify(message="Invalid password."),400)
    old_user = User.query.filter(User.email == email).first()
    # old_user = User.query.filter(or_(User.email == email, User.jmbg== jmbg)).first()
    if old_user:
        return make_response(jsonify(message="Email already exists."),400)
    idUser=Role.query.filter(Role.name=="user").first()
    user =User(email=email,password=password,surname=surname,forename=forename,jmbg=jmbg,idRole=idUser.id)
    adding_user_to_database(user)

    return Response("", status=200)
jwt= JWTManager(application)
@application.route("/login",methods=["POST"])
def login():

    email = request.json.get("email", "");
    password = request.json.get("password", "");
    fieldname = "";
    if (len(email) == 0):
        fieldname = "email";
    if (len(password) == 0 and fieldname == ""):
        fieldname = "password"
    if (fieldname != ""):
        return make_response(jsonify(message=f"Field {fieldname} is missing."),400)
    if (not check_email(email)):
        return make_response(jsonify(message="Invalid email."), 400)
    user=User.query.filter(and_(User.email==email,User.password==password)).first()
    if not user:
        return make_response(jsonify(message= "Invalid credentials."),400)
    additionalClaims=\
        {
        "forename":user.forename,
        "surname":user.surname,
        "jmbg":user.jmbg,
        "roles":str(user.roles)
        }

    accessToken=create_access_token(identity=user.email, additional_claims=additionalClaims,expires_delta=Configuration.JWT_ACCESS_TOKEN_EXPRES)
    refreshToken=create_refresh_token(identity=user.email,additional_claims=additionalClaims,expires_delta=Configuration.JWT_REFRESH_TOKEN_EXPIRES)
    return make_response(jsonify(accessToken=accessToken,refreshToken=refreshToken),200)

@application.route("/check",methods=["POST"])
@jwt_required()
def check():
    return "Token is valid"
@application.route("/refresh",methods=["POST"])
@jwt_required(refresh=True)
def refresh():

    identity=get_jwt_identity()
    if (identity==None):
        return Response(jsonify(msg="Missing Authorization Header"),status=401)
    refreshClaims=get_jwt()
    additionalClaims=\
        {
            "forename":refreshClaims["forename"],
            "surname":refreshClaims["surname"],
            "jmbg":refreshClaims["jmbg"],
            "roles":refreshClaims["roles"]
        }
    accessToken = create_access_token(identity=identity, additional_claims=additionalClaims,expires_delta=Configuration.JWT_ACCESS_TOKEN_EXPRES)
    return make_response(jsonify(accessToken= accessToken),200)
@application.route("/delete",methods=["POST"])
@roleCheck(role="admin" )
def delete():

        email=request.json.get("email","");
        if (len (email)==0):
            return make_response(jsonify(message="Field email is missing."), 400)
        if (not check_email(email)):
            return make_response(jsonify(message="Invalid email."), 400)
        user=User.query.filter(User.email==email).first()
        if (not user):
            return make_response(jsonify(message="Unknown user."), 400)


        database.session.delete(user)
        database.session.commit()
        return Response(jsonify(),status=200)




@application.route("/print",methods=["GET"])
def print():
   return str(User.query.all());
@application.route("/",methods=["GET"])
def index():
    return "Hello world"

if (__name__=="__main__"):
    database.init_app(application)
    application.run(debug=True,host="0.0.0.0", port=5002)