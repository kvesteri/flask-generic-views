from flask_generic_views import ModelRouter
from flask import abort, current_app

from . import TestCase


def simple_decorator(f):
    """Checks whether user is logged in or raises error 401."""
    def decorator(*args, **kwargs):
        abort(401)
    return decorator


class TestModelRouter(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)

        user = self.User(name=u'John Matrix')
        self.db.session.add(user)
        self.db.session.commit()

    def test_decorator_assignment(self):
        router = ModelRouter(self.User)
        router.decorators = [simple_decorator]
        blueprint = router.register()
        self.app.register_blueprint(blueprint, url_prefix='/users')

        response = self.client.get('/users/1')

        assert response.status_code == 401
