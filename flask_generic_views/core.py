from flask.views import MethodView


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
