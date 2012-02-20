from tests import ViewTestCase
from .extensions import db
from .models import User
from .mocks import MockForm
from flask_generic_views import UpdateFormView, ShowView


class TestUpdateFormView(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)

        self.app.add_url_rule('/users/<int:id>/edit',
            view_func=UpdateFormView.as_view('edit',
            model_class=User,
            form_class=MockForm),
        )
        self.app.add_url_rule('/user/<int:id>',
            view_func=ShowView.as_view('user.show', model_class=User)
        )
        user = User(name=u'John Matrix')
        db.session.add(user)
        db.session.commit()

    def test_returns_404_if_not_found(self):
        response = self.client.put('/users/123123/edit')
        assert response.status_code == 404

    def test_renders_template_on_get_request(self):
        response = self.client.get('/users/1/edit')

        assert response.status_code == 200

    def test_redirects_on_succesful_post_request(self):
        response = self.client.put('/users/1/edit',
            data={'name': u'Jack Daniels'}
        )

        assert response.status_code == 302

    def test_updates_database_on_succesful_post_request(self):
        self.client.put('/users/1/edit',
            data={'name': u'Jack Daniels'}
        )
        assert User.query.first().name == u'Jack Daniels'
