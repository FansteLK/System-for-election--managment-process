import alembic.command
from flask import Flask
from configuration import  Configuration
from flask_migrate import Migrate,init,migrate,upgrade,revision
from models import database,Role ,User
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
            # revision(rev_id="849e8cd1e001")
            migrate(message="Production migration2")
            upgrade()

            adminRole = Role (name="admin")
            userRole= Role(name="user")
            database.session.add(adminRole)
            database.session.add(userRole)
            database.session.commit()
            admin= User(email="admin@admin.com",password="1",forename="admin",surname="admin",jmbg="0000000000000",idRole=adminRole.id)

            database.session.add(admin)
            database.session.commit()
            done=True
    except Exception as error:
        print(error)
