from datetime import  timedelta
import os
databaseURL= os.environ["DATABASE_URL"]
class Configuration:

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseURL}/election";
    REDIS_HOST="redis"
    REDIS_VOTES_LIST="votes"
    JWT_SECRET_KEY="JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPRES= timedelta (hours=1);
    JWT_REFRESH_TOKEN_EXPIRES= timedelta (days=30);
