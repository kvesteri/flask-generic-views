from tests import ViewTestCase
from .models import User
from flask_generic_views import CreateView, ShowView


class TestCreateView(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)

        self.app.add_url_rule('/users',
            view_func=CreateView.as_view('create',
            model_class=User),
        )
        self.app.add_url_rule('/users/<int:id>',
            view_func=ShowView.as_view('user.show', model_class=User)
        )

    def test_html_requests_redirect_on_success(self):
        response = self.client.post('/users',
            data={'name': u'Jack Daniels'}
        )
        assert response.status_code == 302
        assert response.location == 'http://localhost/users/1'

    def test_has_flash_message_default(self):
        response = self.client.post('/users',
            data={'name': u'Jack Daniels'}
        )
        response = self.client.get('/users/1')
        assert 'User created!' in response.data
