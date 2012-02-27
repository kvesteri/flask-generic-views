from copy import copy
from datetime import datetime, date, time
from decimal import Decimal
from flask import (render_template, request, redirect, url_for, flash,
    current_app, jsonify, Response, Blueprint)
from flask.views import View
from inflection import underscore, humanize
from sqlalchemy import types
from werkzeug.datastructures import MultiDict


def qp_url_for(endpoint, **kwargs):
    """
    Returns the url for an endpoint but preserves all request query parameters

    kwargs can be used for overriding specific query parameters

    :param endpoint: endpoint to return the url for, eg. user.index
    :param kwargs: dict containing query parameter names as keys
    """
    data = dict(MultiDict(request.args).lists())

    for key, value in kwargs.items():
        data[key] = value
    return url_for(endpoint, **data)


TYPE_MAP = {
    types.BigInteger: int,
    types.SmallInteger: int,
    types.Integer: int,
    types.DateTime: datetime,
    types.Date: date,
    types.Time: time,
    types.Text: str,
    types.Unicode: unicode,
    types.UnicodeText: unicode,
    types.Float: float,
    types.Numeric: Decimal,
    types.Boolean: bool
}


def request_wants_json():
    """
    Whether or not the request wants the response in json format
    """
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


def get_native_type(sqlalchemy_type):
    """
    Converts sqlalchemy type to python type, is smart enough to understand
    types that extend basic sqlalchemy types
    """
    for base_type in TYPE_MAP:
        if isinstance(sqlalchemy_type, base_type):
            return TYPE_MAP[base_type]
            break
    return None


class BaseView(View):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class ModelMixin(object):
    """
    Base class for all views interacting with models

    :param model_class: SQLAlchemy Model class
    """
    model_class = None

    def get_model(self):
        if not self.model_class:
            raise Exception()
        return self.model_class

    @property
    def db(self):
        return current_app.extensions['sqlalchemy'].db

    @property
    def request_params(self):
        if request.is_xhr:
            data = {}
            if request.data:
                data = request.json
        else:
            data = request.form.to_dict()

        return data

    def dispatch_request(self, *args, **kwargs):
        raise NotImplementedError()


class TemplateMixin(object):
    """
    Generic template mixin

    :param template: name of the template to be rendered on html request
    :param context: dict containing context arguments that will be passed
        to template
    """
    template = None
    context = {}

    def render_template(self, **kwargs):
        context = self.get_context(**kwargs)
        return render_template(self.get_template(), **context)

    def get_template(self):
        if not self.template:
            raise Exception()

        return self.template

    def get_context(self, **kwargs):
        if callable(self.context):
            context = self.context()
        else:
            context = self.context
        context.update(kwargs)
        return context


class ModelView(BaseView, ModelMixin, TemplateMixin):
    pk_param = 'id'
    query = None

    def get_template(self):
        return TemplateMixin.get_template(self).format(
            resource=underscore(self.model_class.__name__),
        )

    def get_query(self):
        if self.query:
            return self.query
        return self.model_class.query

    def get_object(self, **kwargs):
        pk = kwargs[self.pk_param]
        return self.get_query().get_or_404(pk)


class ShowView(ModelView):
    """
    Generic show view

    On text/html request returns html template with requested object

    On json request returns requested object in json format

    Example ::

        >>> app.add_url_rule('/users/<int:id>',
        ...     view_func=ShowUserView.as_view('show', model_class=User),
        ... )

    Now consider issuing a GET request to http://localhost:5000/users/3

    ShowView renders user/show.html template if given user exists otherwise
    returns 404

    :param model_class: SQLAlchemy Model class
    :param resource: Name of the resource, if None the resource name
        will be constructed from the model class, e.g. DeviceType ->
        device_type
    :param template: name of the template to be rendered on html request
    :param context: dict containing context arguments that will be passed
        to template
    :param template_object_name: Designates the name of the template variable
        to use in the template context. By default, this is 'item'.


    Rendered template context:

    In addition to given `context`, the template's context will be:

    item: The requested item. This variable's name depends on the
    template_object_name parameter, which is 'item' by default. If
    template_object_name is 'foo', this variable's name will be foo.
    """
    template = '{resource}/show.html'

    def dispatch_request(self, *args, **kwargs):
        item = self.get_object(**kwargs)
        if request_wants_json():
            return jsonify(data=item.as_json())
        else:
            return self.render_template(item=item)


class FormView(ModelView):
    """
    Generic form view

    :param success_redirect: endpoint to be redirected on success
    :param success_message: message to be flashed on success
    :param form_class: form class to be used for request params validation
    """
    form_class = None
    failure_message = ''
    success_message = ''
    success_redirect = None

    def get_success_redirect(self):
        return self.success_redirect.format(
            resource=underscore(self.model_class.__name__)
        )

    def flash(self, message, *args, **kwargs):
        if message:
            flash(message, *args, **kwargs)

    def get_success_message(self):
        return self.success_message.format(
            model=humanize(self.model_class.__name__)
        )

    def get_failure_message(self):
        return self.failure_message.format(
            model=humanize(self.model_class.__name__)
        )


class CreateFormView(FormView):
    """
    Generic create form view

    Template name:
    If template_name isn't specified, this view will use the template
    <model_name>/create.html by default, where:

    <model_name> is your model's name underscored. For a model
    StaffMember, that'd be staff_member.

    Template context:

    In addition to given context, the template's context will be:

    form: A form instance representing the form for editing the object. This
    lets you refer to form fields easily in the template system.
    """
    template = '{resource}/create.html'
    success_message = '{model} created!'
    success_redirect = '{resource}.show'
    methods = ['GET', 'POST']

    def dispatch_request(self):
        model = self.model_class()
        form = self.form_class(request.form, obj=model)
        if form.validate_on_submit():
            form.populate_obj(model)
            self.db.session.add(model)
            self.db.session.commit()

            self.flash(self.get_success_message(), 'success')
            return redirect(url_for(self.get_success_redirect(), id=model.id))
        return self.render_template(form=form, item=model)


class UpdateFormView(FormView):
    template = '{resource}/edit.html'
    success_message = '{model} updated!'
    success_redirect = '{resource}.show'
    methods = ['GET', 'POST', 'PUT']

    def dispatch_request(self, *args, **kwargs):
        item = self.get_object(**kwargs)
        form = self.form_class(request.form, obj=item)
        if form.validate_on_submit():
            form.populate_obj(item)
            self.db.session.commit()
            self.flash(self.get_success_message(), 'success')
            return redirect(url_for(self.get_success_redirect(), id=item.id))
        return self.render_template(item=item, form=form)


class CreateView(FormView):
    """
    Creates a model object

    By default on html request redirects to resource.show and creates a
    simple success message

    On json request returns the create model object as json
    """
    methods = ['POST']
    success_message = '{model} created!'
    success_redirect = '{resource}.show'

    def dispatch_request(self, *args, **kwargs):
        item = self.model_class()
        for field, value in self.request_params.items():
            setattr(item, field, value)
        self.db.session.add(item)
        self.db.session.commit()

        if request_wants_json():
            response = jsonify(data=item.as_json())
            response.status_code = 201
            return response
        else:
            self.flash(self.get_success_message(), 'success')
            return redirect(url_for(self.get_success_redirect(), id=item.id))


class UpdateView(FormView):
    """
    Updates a model object

    By default on html request redirects to resource.show and creates a
    simple success message

    On json request returns the updated model object as json
    """
    methods = ['PUT']
    success_message = '{model} updated!'
    success_redirect = '{resource}.show'

    def dispatch_request(self, *args, **kwargs):
        item = self.get_object(**kwargs)
        for field, value in self.request_params.items():
            setattr(item, field, value)
        self.db.session.commit()

        if request_wants_json():
            return jsonify(data=item.as_json())
        else:
            self.flash(self.get_success_message(), 'success')
            return redirect(url_for(self.get_success_redirect(), id=item.id))


class DeleteView(FormView):
    """
    Deletes a model object

    By default on html request redirects to resource.index and creates a
    simple success message

    On json request returns an empty response with status code 204
    """
    methods = ['DELETE']
    success_message = '{model} deleted.'
    success_redirect = '{resource}.index'

    def dispatch_request(self, *args, **kwargs):
        item = self.get_object(**kwargs)
        self.db.session.delete(item)
        self.db.session.commit()

        if request_wants_json():
            return Response(status=204)
        else:
            self.flash(self.get_success_message(), 'success')
            return redirect(url_for(self.get_success_redirect()))


class ListView(ModelView):
    """
    Views several items as a list

    :param query    the query to be used for fetching the items, by default
                    this is model.query (= all records for given model)
    """
    template = '{resource}/index.html'

    def __init__(self,
        query_field_names=None,
        columns=None,
        *args, **kwargs):
        ModelView.__init__(self, *args, **kwargs)

        if query_field_names:
            self.query_field_names = query_field_names
        else:
            self.query_field_names = self.default_query_field_names()

        if columns:
            self.columns = columns
        else:
            self.columns = self.default_columns()

    def default_query_field_names(self):
        return self.get_query()._entities[0].entity_zero.class_.__table__ \
            .columns.keys()

    def default_columns(self):
        columns = []
        for column in self.query_field_names:
            columns.append((column, self.column_to_alias(column)))
        return columns

    def column_to_alias(self, column):
        return ' '.join([s.capitalize() for s in column.split('_')])

    def execute_query(self, pagination):
        return pagination.items

    def entity_column(self, column):
        entities = [entity.entity_zero.class_ for entity in \
            self.get_query()._entities]

        for entity in entities:
            columns = entity.__table__.columns
            if column in columns:
                return getattr(entity, column), columns[column]
        return None


class SearchMixin(object):
    def append_filters(self, query):
        for row in self.columns:
            name, alias = row
            if name not in request.args:
                continue

            attr, column = self.entity_column(name)
            if not attr:
                continue

            native_type = get_native_type(column.type)
            value = request.args[name]
            if native_type in (str, unicode):
                query = query.filter(attr.startswith(value))
            elif native_type is bool:
                if value == 'y':
                    query = query.filter(attr == True)
                elif value == 'n':
                    query = query.filter(attr == False)
            elif native_type is int:
                if value != '' and value != '__None':
                    try:
                        value = int(value)
                        query = query.filter(attr == value)
                    except ValueError:
                        pass
        return query


class SortMixin(object):
    sort = ''

    def append_sort(self, query):
        entities = [entity.entity_zero.class_ for entity in \
            self.get_query()._entities]

        self.sort = request.args.get('sort', self.sort)
        if not self.sort:
            return query

        order_by = self.sort
        if self.sort:
            if self.sort[0] == '-':
                func = self.db.desc
                order_by = self.sort[1:]
            else:
                func = self.db.asc

        if order_by:
            for entity in entities:
                if order_by in entity.__table__.columns:
                    query = query.order_by(func(getattr(entity, order_by)))
                    break
        return query


class PaginationMixin(object):
    per_page = 20
    page = 1

    def append_pagination(self, query):
        try:
            page = int(request.args.get('page', 1))
        except ValueError:
            page = 1

        try:
            per_page = int(request.args.get('per_page', self.per_page))
        except ValueError:
            per_page = self.per_page

        pagination = query.paginate(page, per_page)
        return pagination


class SortedListView(ListView, SortMixin, PaginationMixin, SearchMixin):
    """
    Expands ListView with filters, paging and sorting

    :param per_page     number of items to show per_page
    :param sort         the default column to use for sorting the results
                        eg. sort='name'
                            return the items ordered by name ascending
                            sort='-name'
                            return the items ordered by name descending
    """
    form_class = None

    def dispatch_request(self):
        query = self.append_filters(self.get_query())
        query = self.append_sort(query)
        pagination = self.append_pagination(query)
        items = self.execute_query(pagination)

        form = None
        if self.form_class:
            form = self.form_class()

        if request_wants_json():
            return jsonify(
                pagination={
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total
                    },
                sort=self.sort,
                data=[item.as_json() for item in items]
            )
        else:
            return self.render_template(
                items=items,
                columns=self.columns,
                sort=self.sort,
                per_page=pagination.per_page,
                page=pagination.page,
                total_items=pagination.total,
                pages=pagination.pages,
                form=form
            )


class ModelRouter(object):
    """
    ModelRouter glues different views together

    index    GET     /
    new      GET     /new
    show     GET     /<int:id>
    edit     GET     /<int:id>/edit
    create   POST    /
    update   PUT     /<int:id>
    delete   DELETE  /<int:id>

    Supports both natural and surrogate primary keys for models, however it
    does not yet support composite primary keys.

    Example 1: User model with name string as primary key

    The routes would then look like:

    index    GET     /              index.html
    new      GET     /new           new.html
    show     GET     /<name>        show.html
    edit     GET     /<name>/end    edit.html
    create   POST    /              redirects to show
    update   PUT     /<name>        redirects to show
    delete   DELETE  /<name>        redirects to index

    Example ::

    Assume we have a model class called User

        >>> router = ModelRouter(User)
        >>> router.register()


    :param decorators decorators to be passed to all views within this router
    :param model_class model_class to be passed to all views
    """
    decorators = []
    route_prefix = ''
    model_class = None
    route_key = None

    def __init__(self, model_class, **kwargs):
        self.model_class = model_class
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.routes = {
            'index': ['{prefix}', SortedListView, {}],
            'create': ['{prefix}', CreateView, {}],
            'edit': ['{prefix}/{primary_key}/edit', UpdateFormView, {}],
            'new': ['{prefix}/new', CreateFormView, {}],
            'update': ['{prefix}/{primary_key}', UpdateView, {}],
            'delete': ['{prefix}/{primary_key}', DeleteView, {}],
            'show': ['{prefix}/{primary_key}', ShowView, {}]
        }

    def get_route_key(self):
        if self.route_key is not None:
            return self.route_key

        primary_key = self.model_class.__table__.primary_key.columns
        if len(primary_key.keys()) > 1:
            raise Exception('''Could not create api for model with composite
                primary keys''')
        name = primary_key.keys()[0]
        type = primary_key._data.values()[0].type
        python_type = get_native_type(type.__class__)
        if python_type == int:
            self.route_key = '<int:%s>' % name
        else:
            self.route_key = '<%s>' % name
        return self.route_key

    def get_routes(self):
        routes = copy(self.routes)
        for key in self.routes:
            routes[key][0] = self.routes[key][0].format(
                primary_key=self.get_route_key(),
                prefix=self.route_prefix
            )
        return routes

    def bind_view(self, key, view):
        """
        bind_view can be used for overriding default views

        Lets say for example that we have a custom ShowView class called
        UserShowView

        You can easily override the default show class by:

        Example ::

            >>> router.bind_view('show', UserShowView)
        """
        self.routes[key][1] = view

    def bind_view_args(self, key, **kwargs):
        """
        bind_view_args can be used for overriding specific view args

        Lets say you want to pass custom form class for edit

        You can achieve this with:

        Example ::

            >>> router.bind_view_args('edit', form_class=MyCustomForm)
        """
        self.routes[key][2] = kwargs

    def bind_route(self, key, route):
        """
        bind_route can be used for overriding default routes

        Lets say you want to route index to '/index' instead of '/'

        You can achieve this with:

        Example ::

            >>> router.bind_route('index', '/index')
        """
        self.routes[key][0] = route

    def register(self, blueprint=None):
        if not blueprint:
            blueprint = Blueprint(underscore(self.model_class.__name__),
                __name__)

        for key, value in self.get_routes().items():
            route, view, kwargs = value
            view_func = view.as_view(
                key,
                model_class=self.model_class,
                **kwargs
            )

            for decorator in self.decorators:
                view_func = decorator(view_func)

            blueprint.add_url_rule(
                route,
                view_func=view_func
            )
        return blueprint
