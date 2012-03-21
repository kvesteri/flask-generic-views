from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy


class TestCase(object):

    def setup_method(self, method):
        self.app = Flask(__name__)
        self.app.debug = True
        self.app.secret_key = 'not a secret'

        db = SQLAlchemy(self.app)

        class User(db.Model):
            id = db.Column(db.Integer, autoincrement=True, primary_key=True)
            name = db.Column(db.Unicode(255), index=True)
            age = db.Column(db.Integer, index=True)

        self.User = User
        self.db = db
        self.db.create_all()

        self.client = self.app.test_client()

    def teardown_method(self, method):
        self.db.drop_all()
        self.db.session.remove()
