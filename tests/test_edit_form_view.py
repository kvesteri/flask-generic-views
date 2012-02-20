from tests import ViewTestCase
from .extensions import db
from .models import User
from flask_generic_views import UpdateFormView, SortedListView


class TestUpdateFormView(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)

        self.app.add_url_rule('/users/<int:id>/edit',
            view_func=UpdateFormView.as_view('edit',
            model_class=User,
            validator=lambda a: a),
        )
        self.app.add_url_rule('/users',
            view_func=SortedListView.as_view('user.index', model_class=User)
        )
        user = User(name=u'John Matrix')
        db.session.add(user)
        db.session.commit()

    def test_returns_404_if_not_found(self):
        response = self.xhr_client.put('/users/123123/edit')
        assert response.status_code == 404
