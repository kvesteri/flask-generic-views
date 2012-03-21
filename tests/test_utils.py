from tests import ViewTestCase
from .extensions import db
from .models import User
from flask_generic_views import UpdateView, SortedListView


class TestUtils(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)

        self.app.add_url_rule('/users/<int:id>',
            view_func=UpdateView.as_view('update',
            model_class=User,
            validator=lambda a: a),
        )
        self.app.add_url_rule('/users',
            view_func=SortedListView.as_view('user.index', model_class=User)
        )
        user = User(name=u'John Matrix')
        db.session.add(user)
        db.session.commit()
