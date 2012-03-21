from flask import Flask
from .extensions import db


class DatabaseTestCase(object):
    datasets = []

    def create_app(self):
        app = Flask(__name__)
        app.config.from_object('tests.config')
        db.init_app(app)
        return app

    def setup_method(self, method):
        self.app = self.create_app()
        self._ctx = self.app.test_request_context()
        self._ctx.push()

        db.create_all()

    def teardown_method(self, method):
        db.drop_all()
        db.session.remove()

        #self._ctx.pop()
        # Clean up to prevent memory leaks
        del self.app.extensions['sqlalchemy']
        del self.app
        del self._ctx


class ViewTestCase(DatabaseTestCase):

    def setup_method(self, method):
        super(ViewTestCase, self).setup_method(method)
        self.client = self.app.test_client()

    def teardown_method(self, method):
        del self.client
        super(ViewTestCase, self).teardown_method(method)
