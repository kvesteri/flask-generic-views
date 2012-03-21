from __future__ import with_statement

from pytest import raises
from tests import ViewTestCase
from .extensions import db
from .models import User
from flask.templating import TemplateNotFound
from flask_generic_views import SortedListView


class ListViewTestCase(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)
        self.view = SortedListView.as_view('index', model_class=User)
        self.app.add_url_rule('/users',
            view_func=self.view,
        )

        john = User(name=u'John Matrix', age=35)
        jack = User(name=u'Jack Daniels', age=60)
        luke = User(name=u'Luke Skywalker', age=30)
        vader = User(name=u'Darth Vader', age=55)
        db.session.add(john)
        db.session.add(jack)
        db.session.add(luke)
        db.session.add(vader)
        db.session.commit()


class TestListView(ListViewTestCase):
    def test_if_template_not_set_tries_to_use_default_template(self):
        response = self.client.get('/users')
        response.status_code == 200

    def test_template_can_be_overridden(self):
        self.view = SortedListView.as_view('index', model_class=User,
            template='some_template.html')
        self.app.add_url_rule('/users',
            view_func=self.view,
        )
        with raises(TemplateNotFound):
            self.client.get('/users')
