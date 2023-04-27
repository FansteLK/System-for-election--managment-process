import alembic.command
from flask import Flask
from configuration import  Configuration
from flask_migrate import Migrate,init,migrate,upgrade,revision,stamp
from models import database
from sqlalchemy_utils import database_exists,create_database
application= Flask(__name__)
application.config.from_object(Configuration)

migrateObject= Migrate( application ,database)
done=False
while (not done):
    try:
        if (not database_exists(application.config["SQLALCHEMY_DATABASE_URI"])):
            create_database(application.config["SQLALCHEMY_DATABASE_URI"])
        database.init_app(application)

        with application.app_context() as context:

            init()

            # revision(rev_id="0eb8ed0f03d9'")
            migrate(message="Production migration2")
            upgrade()

            done=True
    except Exception as error:
        print(error)
