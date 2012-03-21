from flask.views import MethodView
from flask.ext.generic_views import (
    BaseView,
    ImproperlyConfigured,
    TemplateView,
)
from flexmock import flexmock
from py.test import raises


class TestBaseView(object):
    def test_inherits_from_method_view(self):
        view = BaseView()
        assert isinstance(view, MethodView)

    def test_constructor_saves_kwargs_to_the_view(self):
        view = BaseView(foo='bar')
        assert view.foo == 'bar'


class TestTemplateView(object):
    def test_responds_to_get_requests(self):
        assert TemplateView.methods == ['GET']

    def test_get_template_returns_template_attribute(self):
        view = TemplateView(template='template.html')
        assert view.get_template() == 'template.html'

    def test_get_template_raises_exception_if_template_not_defined(self):
        view = TemplateView()
        with raises(ImproperlyConfigured):
            view.get_template()

    def test_get_context_returns_context_from_attribute(self):
        view = TemplateView(context={'foo': 'bar'})
        assert view.get_context() == {'foo': 'bar', 'params': {}}

    def test_get_context_adds_kwargs_to_params_key(self):
        view = TemplateView()
        assert view.get_context(page=3) == {'params': {'page': 3}}

    def test_renders_given_template_with_given_context(self):
        from flask.ext.generic_views import core
        view = TemplateView()
        (flexmock(view)
            .should_receive('get_template')
            .with_args()
            .and_return('template.html'))
        (flexmock(view)
            .should_receive('get_context')
            .with_args(page=3)
            .and_return({'foo': 'bar', 'params': {'page': 3}}))
        (flexmock(core)
            .should_receive('render_template')
            .with_args('template.html', foo='bar', params={'page': 3})
            .and_return('a response'))
        assert view.render(page=3) == 'a response'

    def test_get_delegates_to_render(self):
        view = TemplateView()
        (flexmock(view)
            .should_receive('render')
            .with_args(page=3)
            .and_return('a response'))
        assert view.get(page=3) == 'a response'
