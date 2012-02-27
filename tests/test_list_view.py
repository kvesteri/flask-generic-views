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

    def test_supports_paging_out_of_item_range(self):
        response = self.xhr_client.get('/users?page=10')
        assert response.status_code == 404

    def test_page_parameter(self):
        response = self.xhr_client.get('/users?page=2&per_page=1&name=J')
        assert len(response.json['data']) == 1

    def test_per_page_default_can_be_overridden(self):
        self.view = SortedListView.as_view('index', model_class=User,
            per_page=3)
        self.app.add_url_rule('/users',
            view_func=self.view,
        )
        response = self.xhr_client.get('/users')
        assert len(response.json['data']) == 3


class TestListViewSorting(ListViewTestCase):
    def test_sort_default_can_be_overridden(self):
        self.view = SortedListView.as_view('index', model_class=User,
            sort='age')
        self.app.add_url_rule('/users',
            view_func=self.view,
        )
        response = self.xhr_client.get('/users')
        assert response.json['sort'] == 'age'

    def test_ascending_default_sort(self):
        self.view = SortedListView.as_view('index', model_class=User,
            sort='name')
        self.app.add_url_rule('/users',
            view_func=self.view,
        )
        response = self.xhr_client.get('/users')
        data = response.json['data']
        assert data[0]['name'] == 'Darth Vader'
        assert data[1]['name'] == 'Jack Daniels'

    def test_descending_default_sort(self):
        self.view = SortedListView.as_view('index', model_class=User,
            sort='-name')
        self.app.add_url_rule('/users',
            view_func=self.view,
        )
        response = self.xhr_client.get('/users')
        data = response.json['data']
        assert data[0]['name'] == 'Luke Skywalker'
        assert data[1]['name'] == 'John Matrix'

    def test_sort_added_to_template_context(self):
        self.view = SortedListView.as_view('index', model_class=User,
            sort='-name')
        self.app.add_url_rule('/users',
            view_func=self.view,
        )
        response = self.client.get('/users')

        assert 'sort: -name' in response.data
