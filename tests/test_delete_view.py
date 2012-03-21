from flask_generic_views import DeleteView, SortedListView

from . import TestCase


class TestDeleteView(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.app.add_url_rule('/users/<int:id>',
            view_func=DeleteView.as_view('delete', model_class=self.User)
        )
        self.app.add_url_rule('/users',
            view_func=SortedListView.as_view('user.index', model_class=self.User)
        )
        user = self.User(name=u'John Matrix')
        self.db.session.add(user)
        self.db.session.commit()

    def test_tries_to_redirect_to_index_page_by_default(self):
        response = self.client.delete('/users/1')

        assert response.status_code == 302

    def test_redirects_to_index_view_by_default(self):
        response = self.client.delete('/users/1')
        assert response.status_code == 302
        assert response.location == 'http://localhost/users'

    def test_has_default_flash_message(self):
        self.client.delete('/users/1')
        response = self.client.get('/users')

        assert 'User deleted.' in response.data
