from flask.views import MethodView
from flask.ext.generic_views import BaseView


class TestBaseView(object):
    def test_inherits_from_method_view(self):
        view = BaseView()
        assert isinstance(view, MethodView)

    def test_constructor_saves_kwargs_to_the_view(self):
        view = BaseView(foo='bar')
        assert view.foo == 'bar'
