from tests import ViewTestCase
from .models import User
from flask_generic_views import CreateView


class TestCreateView(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)

        self.app.add_url_rule('/users',
            view_func=CreateView.as_view('create',
            model_class=User,
            validator=lambda a: a),
        )

    def test_supports_json(self):
        response = self.xhr_client.post('/users',
            data={'name': 'Jack Daniels'}
        )
        assert response.status_code == 201
        assert User.query.first().name == u'Jack Daniels'

    def test_returns_404_if_not_found(self):
        response = self.xhr_client.put('/users/123123')
        assert response.status_code == 404
