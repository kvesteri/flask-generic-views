from flask import render_template
from flask.views import MethodView

from .exceptions import ImproperlyConfigured


class BaseView(MethodView):
    """Base class for all other views."""

    def __init__(self, **kwargs):
        """
        Construct the view.

        Assigns the keyword arguments passed to the view instance for
        convenience and flexibility.
        """
        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class TemplateView(BaseView):
    """Render a given template."""

    methods = ['GET']

    #: The name of the template to be rendered, or an iterable with template
    #: names the first one existing will be rendered.
    template = None

    context = {}

    def get_template(self):
        if not self.template:
            raise ImproperlyConfigured(
                'You must either specify a template, or override '
                '`get_template()` method.'
            )
        return self.template

    def get_context(self, **kwargs):
        context = {}
        context.update(self.context)
        context['params'] = kwargs
        return context

    def render(self, **kwargs):
        template = self.get_template()
        context = self.get_context(**kwargs)
        return render_template(template, **context)

    def get(self, **kwargs):
        return self.render(**kwargs)
