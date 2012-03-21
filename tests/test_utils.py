from tests import TestCase
from flask_generic_views import UpdateView, SortedListView


class TestUtils(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)

        self.app.add_url_rule('/users/<int:id>',
            view_func=UpdateView.as_view('update',
            model_class=self.User,
            validator=lambda a: a),
        )
        self.app.add_url_rule('/users',
            view_func=SortedListView.as_view('user.index', model_class=self.User)
        )
        user = self.User(name=u'John Matrix')
        self.db.session.add(user)
        self.db.session.commit()
