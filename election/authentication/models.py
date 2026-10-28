from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False, unique=True)
    users = db.relationship("User", back_populates="role")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    jmbg = db.Column(db.String(13), nullable=False)
    email = db.Column(db.String(256), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    forename = db.Column(db.String(256), nullable=False)
    surname = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    role = db.relationship("Role", back_populates="users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def token_claims(self):
        return {
            "forename": self.forename,
            "surname": self.surname,
            "jmbg": self.jmbg,
            "roles": [self.role.name],
        }
