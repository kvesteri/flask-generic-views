from flask import Flask, json
from .extensions import db
from werkzeug import cached_property


def xhr_test_client(client):
    """Decorates regular test client to make XMLHttpRequests with JSON data."""

    original_open = client.open

    def open(self, *args, **kwargs):
        if 'data' in kwargs:
            kwargs['data'] = json.dumps(kwargs['data'])
        kwargs['content_type'] = 'application/json'
        kwargs['headers'] = [
            ('X-Requested-With', 'XMLHttpRequest'),
            ('Accept', 'application/json')
        ]
        return original_open(self, *args, **kwargs)

    client.open = open
    return client


class JsonResponseMixin(object):
    """
    Mixin with testing helper methods
    """
    @cached_property
    def json(self):
        return json.loads(self.data)


def _make_test_response(response_class):
    class TestResponse(response_class, JsonResponseMixin):
        pass

    return TestResponse


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
        self.app.response_class = _make_test_response(self.app.response_class)
        self.client = self.app.test_client()
        self.xhr_client = xhr_test_client(self.app.test_client())

    def teardown_method(self, method):
        del self.client
        del self.xhr_client
        super(ViewTestCase, self).teardown_method(method)
