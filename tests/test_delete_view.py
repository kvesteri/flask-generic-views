from datetime import datetime
from tests import ViewTestCase
from .extensions import db
from .models import User
from flask_generic_views import DeleteView, SoftDeleteView, SortedListView


class TestDeleteView(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)
        self.app.add_url_rule('/users/<int:id>',
            view_func=DeleteView.as_view('delete', model_class=User)
        )
        self.app.add_url_rule('/users',
            view_func=SortedListView.as_view('user.index', model_class=User)
        )
        user = User(name=u'John Matrix')
        db.session.add(user)
        db.session.commit()

    def test_tries_to_redirect_to_index_page_by_default(self):
        response = self.client.delete('/users/1')

        assert response.status_code == 302

    def test_supports_json(self):
        response = self.xhr_client.delete('/users/1')
        assert response.status_code == 204

    def test_redirects_to_index_view_by_default(self):
        response = self.client.delete('/users/1')
        assert response.status_code == 302
        assert response.location == 'http://localhost/users'

    def test_has_default_flash_message(self):
        self.client.delete('/users/1')
        response = self.client.get('/users')

        assert 'User deleted.' in response.data


class TestSoftDeleteView(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)
        self.app.add_url_rule('/users/<int:id>',
            view_func=SoftDeleteView.as_view('delete', model_class=User)
        )
        self.app.add_url_rule('/users',
            view_func=SortedListView.as_view('user.index', model_class=User)
        )
        user = User(name=u'John Matrix')
        db.session.add(user)
        db.session.commit()

    def test_supports_json(self):
        response = self.xhr_client.delete('/users/1')
        assert response.status_code == 204
        assert isinstance(User.query.first().deleted_at, datetime)

