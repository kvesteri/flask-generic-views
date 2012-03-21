from __future__ import with_statement

from flask.templating import TemplateNotFound
from flask.ext.generic_views import ShowView
from pytest import raises

from . import ViewTestCase
from .extensions import db
from .models import User


class TestShowView(ViewTestCase):
    def setup_method(self, method):
        ViewTestCase.setup_method(self, method)
        self.app.add_url_rule('/users/<int:id>',
            view_func=ShowView.as_view('show', model_class=User),
        )

        user = User(name=u'John Matrix')
        db.session.add(user)
        db.session.commit()

    def test_if_template_not_set_tries_to_use_default_template(self):
        response = self.client.get('/users/1')
        response.status_code == 200

    def test_raises_template_not_found_for_invalid_template(self):
        self.app.add_url_rule('/users/<int:id>',
            view_func=ShowView.as_view(
                'show',
                model_class=User,
                template='invalid.html'
            ),
        )
        with raises(TemplateNotFound):
            self.client.get('/users/1')

    def test_returns_404_if_not_found(self):
        response = self.client.get('/users/123123')
        assert response.status_code == 404
