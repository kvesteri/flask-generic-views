from tests import ViewTestCase
from .extensions import db
from .models import User
from flask_generic_views import SortedListView


class TestListView(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)
        self.view = SortedListView.as_view('index', model_class=User)
        self.app.add_url_rule('/users',
            view_func=self.view,
        )

        john = User(name=u'John Matrix', age=35)
        jack = User(name=u'Jack Daniels', age=60)
        luke = User(name=u'Luke Skywalker', age=30)
        vader = User(name=u'Darth Vadeer', age=55)
        db.session.add(john)
        db.session.add(jack)
        db.session.add(luke)
        db.session.add(vader)
        db.session.commit()

    def test_if_template_not_set_tries_to_use_default_template(self):
        response = self.client.get('/users')
        response.status_code == 200

    def test_supports_json(self):
        response = self.xhr_client.get('/users?name=John')
        assert response.status_code == 200
        assert response.json['data'][0]['name'] == u'John Matrix'

    def test_json_returns_pagination_params(self):
        response = self.xhr_client.get('/users?name=John')

        assert response.json['pagination']['total'] == 1
        assert response.json['pagination']['page'] == 1
        assert response.json['pagination']['per_page'] == 20
        assert response.json['pagination']['pages'] == 1

    def test_supports_integer_filters(self):
        response = self.xhr_client.get('/users?age=13')
        assert response.json['data'] == []

    def test_per_page_parameter(self):
        response = self.xhr_client.get('/users?page=1&per_page=2')
        assert len(response.json['data']) == 2

    def test_page_parameter(self):
        response = self.xhr_client.get('/users?page=2&per_page=1&name=J')
        assert len(response.json['data']) == 1
