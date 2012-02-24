from datetime import datetime, date, time
from decimal import Decimal
from flask import (render_template, request, redirect, url_for, flash,
    current_app, jsonify, Response, Blueprint)
from flask.views import View
from inflection import underscore
from sqlalchemy import types
from werkzeug.datastructures import MultiDict


def qp_url_for(endpoint, **kwargs):
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


#: Whether or not the request wants the response in json format
def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


#: Converts sqlalchemy type into python type
def get_native_type(sqlalchemy_type):
    for base_type in TYPE_MAP:
        if isinstance(sqlalchemy_type, base_type):
            return TYPE_MAP[base_type]
            break
    return None


class ModelView(View):
    """
    Base class for all views interacting with models

    :param model_class      SqlAlchemy Model class
    :param resource_name    Name of the resource, if None the resource name
                            will be constructed from the model class,
                            eg.
                                User -> user
                                DeviceType -> device_type
    """
    def __init__(self, model_class=None, resource_name=None, *args, **kwargs):
        if model_class:
            self.model_class = model_class
        if not resource_name:
            self.resource_name = underscore(self.model_class.__name__)
        else:
            self.resource_name = resource_name

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


class TemplateView(ModelView):
    """
    Generic template view

    :param :template    name of the template to be rendered on html request
    :param :context     dict containing context arguments that will be passed
                        to template
    """
    def __init__(self, template=None, context={}, *args, **kwargs):
        ModelView.__init__(self, *args, **kwargs)
        self.context = context

        if template:
            self.template = template
        else:
            self.template = self.default_template % self.resource_name

    @property
    def default_template(self):
        raise NotImplementedError()

    def get_context(self, **kwargs):
        if callable(self.context):
            context = self.context()
        else:
            context = self.context
        context.update(kwargs)
        return context


class ShowView(TemplateView):
    default_template = '%s/show.html'
    """
    Generic show view

    On text/html request returns html template with requested item

    On json request returns requested item in json format
    """
    def __init__(self, *args, **kwargs):
        TemplateView.__init__(self, *args, **kwargs)

    def dispatch_request(self, *args, **kwargs):
        item = self.model_class.query.get_or_404(kwargs.values()[0])

        if request_wants_json():
            return jsonify(data=item.as_json(**self.get_context()))
        else:
            return render_template(self.template, **self.get_context())


class FormView(TemplateView):
    """
    Generic form view

    :param success_redirect endpoint to be redirected on success
    :param success_message  message to be flashed on success
    """

    def __init__(self,
        form_class=None,
        success_redirect=None,
        success_message=None,
        *args,
        **kwargs):
        TemplateView.__init__(self, *args, **kwargs)
        if form_class:
            self.form_class = form_class
        if success_redirect:
            self.success_redirect = success_redirect
        else:
            self.success_redirect = '%s.show' % self.resource_name

        if success_message:
            self.success_message = success_message
        else:
            self.success_message = self.success_message % \
                self.model_class.__name__


class CreateFormView(FormView):
    default_template = '%s/create.html'
    success_message = '%s created!'
    methods = ['GET', 'POST']

    def dispatch_request(self):
        model = self.model_class()
        form = self.form_class(request.form, obj=model)
        if form.validate_on_submit():
            form.populate_obj(model)
            self.db.session.add(model)
            self.db.session.commit()

            flash(self.success_message, 'success')
            return redirect(url_for(self.success_redirect, id=model.id))
        return render_template(self.template, form=form)


class UpdateFormView(FormView):
    default_template = '%s/edit.html'
    success_message = '%s updated!'
    methods = ['GET', 'POST', 'PUT']

    def dispatch_request(self, *args, **kwargs):
        item = self.model_class.query.get_or_404(kwargs.values()[0])
        form = self.form_class(request.form, obj=item)
        if form.validate_on_submit():
            form.populate_obj(item)
            self.db.session.commit()
            flash(self.success_message, 'success')
            return redirect(url_for(self.success_redirect, id=item.id))
        return render_template(self.template, item=item, form=form)


class CreateView(ModelView):
    """
    Creates a model object

    By default on html request redirects to resource.show and creates a
    simple success message

    On json request returns the create model object as json
    """
    methods = ['POST']

    def __init__(self, success_redirect=None, success_message=None, *args,
        **kwargs):
        ModelView.__init__(self, *args, **kwargs)
        self.success_redirect = '%s.show' % self.resource_name
        if success_redirect:
            self.success_redirect = success_redirect
        self.success_message = '%s created!' % self.model_class.__name__
        if success_message:
            self.success_message = success_message

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
            flash(self.success_message, 'success')
            return redirect(url_for(self.success_redirect))


class UpdateView(ModelView):
    """
    Updates a model object

    By default on html request redirects to resource.show and creates a
    simple success message

    On json request returns the updated model object as json
    """
    methods = ['PUT']

    def __init__(self,
        success_redirect=None,
        validator=None,
        success_message=None,
        *args,
        **kwargs):
        ModelView.__init__(self, *args, **kwargs)
        self.success_redirect = '%s.show' % self.resource_name
        if success_redirect:
            self.success_redirect = success_redirect
        self.success_message = '%s updated!' % self.model_class.__name__
        if success_message:
            self.success_message = success_message

    def dispatch_request(self, *args, **kwargs):
        item = self.model_class.query.get_or_404(kwargs.values()[0])
        for field, value in self.request_params.items():
            setattr(item, field, value)
        self.db.session.commit()

        if request_wants_json():
            return jsonify(data=item.as_json())
        else:
            flash(self.success_message, 'success')
            return redirect(url_for(self.success_redirect))


class DeleteView(ModelView):
    """
    Deletes a model object

    By default on html request redirects to resource.index and creates a
    simple success message

    On json request returns an empty response with status code 204
    """
    methods = ['DELETE']

    def __init__(self, success_redirect=None, success_message=None, *args,
        **kwargs):
        ModelView.__init__(self, *args, **kwargs)
        self.success_redirect = '%s.index' % self.resource_name
        if success_redirect:
            self.success_redirect = success_redirect
        self.success_message = '%s deleted.' % self.model_class.__name__
        if success_message:
            self.success_message = success_message

    def dispatch_request(self, *args, **kwargs):
        item = self.model_class.query.get(kwargs.values()[0])
        self.db.session.delete(item)
        self.db.session.commit()
        flash(self.success_message, 'success')

        if request_wants_json():
            return Response(status=204)
        else:
            return redirect(url_for(self.success_redirect))


class ListView(TemplateView):
    default_template = '%s/index.html'
    """
    Views several items as a list

    :param query    the query to be used for fetching the items, by default
                    this is model.query (= all records for given model)
    """

    def __init__(self,
        query=None,
        query_field_names=None,
        columns=None,
        *args, **kwargs):
        TemplateView.__init__(self, *args, **kwargs)
        if query:
            self.query = query
        else:
            self.query = self.model_class.query

        if query_field_names:
            self.query_field_names = query_field_names
        else:
            self.query_field_names = self.default_query_field_names()

        if columns:
            self.columns = columns
        else:
            self.columns = self.default_columns()

    def default_query_field_names(self):
        return self.query._entities[0].entity_zero.class_.__table__ \
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
            self.query._entities]

        for entity in entities:
            columns = entity.__table__.columns
            if column in columns:
                return getattr(entity, column), columns[column]
        return None


class SortedListView(ListView):
    """
    Expands ListView with filters, paging and sorting

    :param per_page     number of items to show per_page
    :param sort         the default column to use for sorting the results
                        eg. sort='name'
                            return the items ordered by name ascending
                            sort='-name'
                            return the items ordered by name descending
    """
    def __init__(self,
        form_class=None,
        per_page=20,
        sort='',
        *args,
        **kwargs):
        ListView.__init__(self, *args, **kwargs)

        if form_class:
            self.form_class = form_class

        self.per_page = per_page
        self.sort = sort

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

    def dispatch_request(self):
        query = self.query
        entities = [entity.entity_zero.class_ for entity in \
            query._entities]
        query = self.append_filters(query)

        sort = request.args.get('sort', '')
        if not sort:
            sort = self.sort

        order_by = sort
        if sort:
            if sort[0] == '-':
                func = self.db.desc
                order_by = sort[1:]
            else:
                func = self.db.asc

        if order_by:
            for entity in entities:
                if order_by in entity.__table__.columns:
                    query = query.order_by(func(getattr(entity, order_by)))
                    break

        pagination = self.append_pagination(query)
        items = self.execute_query(pagination)

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
            return render_template(
                self.template,
                items=items,
                columns=self.columns,
                sort=sort,
                per_page=pagination.per_page,
                page=pagination.page,
                total_items=pagination.total,
                pages=pagination.pages
            )


class ModelRouter(object):
    """
    Generates standard routes for given model

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
    """
    def __init__(self, model_class, decorators=[]):
        self.model_class = model_class
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

        self.decorators = decorators

        self.routes = {
            'index': ['', SortedListView, {}],
            'create': ['', CreateView, {}],
            'edit': ['/{primary_key}/edit', UpdateFormView, {}],
            'new': ['/new', CreateFormView, {}],
            'update': ['/{primary_key}', UpdateView, {}],
            'delete': ['/{primary_key}', DeleteView, {}],
            'show': ['/{primary_key}', ShowView, {}]
        }

        for key in self.routes:
            self.routes[key][0] = self.routes[key][0].format(
                primary_key=self.route_key
            )

    def bind_view(self, key, view):
        self.routes[key][1] = view

    def bind_view_args(self, key, **kwargs):
        self.routes[key][2] = kwargs

    def bind_route(self, key, route):
        self.routes[key][0] = route

    def register(self, blueprint=None):
        if not blueprint:
            blueprint = Blueprint(underscore(self.model_class.__name__),
                __name__)

        for key, value in self.routes.items():
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
