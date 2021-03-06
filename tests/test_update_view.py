from tests import TestCase
from flask_generic_views import UpdateView, ShowView


class TestUpdateView(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)

        self.app.add_url_rule('/users/<int:id>',
            view_func=UpdateView.as_view('update',
            model_class=self.User,
            validator=lambda a: a),
        )
        self.app.add_url_rule('/users/<int:id>',
            view_func=ShowView.as_view('user.show', model_class=self.User)
        )
        user = self.User(name=u'John Matrix')
        self.db.session.add(user)
        self.db.session.commit()

    def test_returns_404_if_not_found(self):
        response = self.client.put('/users/123123')
        assert response.status_code == 404

    def test_html_requests_redirect_on_success(self):
        response = self.client.put('/users/1',
            data={'name': u'Jack Daniels'}
        )
        assert response.status_code == 302
        assert response.location == 'http://localhost/users/1'

    def test_updates_database(self):
        self.client.put('/users/1',
            data={'name': u'Jack Daniels'}
        )
        assert self.User.query.get(1).name == u'Jack Daniels'

    def test_has_flash_message_default(self):
        response = self.client.put('/users/1',
            data={'name': u'Jack Daniels'}
        )
        response = self.client.get('/users/1')
        assert 'User updated!' in response.data
