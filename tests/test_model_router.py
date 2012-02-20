from tests import ViewTestCase
from flask import abort, current_app
from .extensions import db
from .models import User
from flask_generic_views import ModelRouter


def simple_decorator(f):
    """Checks whether user is logged in or raises error 401."""
    def decorator(*args, **kwargs):
        abort(401)
    return decorator


class TestModelRouter(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)

        user = User(name=u'John Matrix')
        db.session.add(user)
        db.session.commit()

    def test_decorator_assignment(self):
        router = ModelRouter(User)
        router.decorators = [simple_decorator]
        blueprint = router.register()
        current_app.register_blueprint(blueprint, url_prefix='/users')

        response = self.client.get('/users/1')

        assert response.status_code == 401
