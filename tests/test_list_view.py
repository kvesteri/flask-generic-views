from __future__ import with_statement

from flask.templating import TemplateNotFound
from flask.ext.generic_views import SortedListView
from pytest import raises

from . import TestCase


class ListTestCase(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.view = SortedListView.as_view('index', model_class=self.User)
        self.app.add_url_rule('/users',
            view_func=self.view,
        )

        john = self.User(name=u'John Matrix', age=35)
        jack = self.User(name=u'Jack Daniels', age=60)
        luke = self.User(name=u'Luke Skywalker', age=30)
        vader = self.User(name=u'Darth Vader', age=55)
        self.db.session.add(john)
        self.db.session.add(jack)
        self.db.session.add(luke)
        self.db.session.add(vader)
        self.db.session.commit()


class TestListView(ListTestCase):
    def test_if_template_not_set_tries_to_use_default_template(self):
        response = self.client.get('/users')
        response.status_code == 200

    def test_template_can_be_overridden(self):
        self.view = SortedListView.as_view('index', model_class=self.User,
            template='some_template.html')
        self.app.add_url_rule('/users',
            view_func=self.view,
        )
        with raises(TemplateNotFound):
            self.client.get('/users')
