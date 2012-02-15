from flask.ext.sqlalchemy import SQLAlchemy

SQLALCHEMY_SESSION_OPTIONS = {
    'expire_on_commit': True
}

db = SQLAlchemy()
