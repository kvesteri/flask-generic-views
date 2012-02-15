import re
from copy import copy
from datetime import datetime, date, time
from decimal import Decimal
from flask import render_template, request, redirect, url_for, flash
from flask.views import View
from flask.ext.login import login_required
from sqlalchemy import types
from monitori.extensions import db


first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def underscorize(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


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


def get_native_type(sqlalchemy_type):
    for base_type in TYPE_MAP:
        if isinstance(sqlalchemy_type, base_type):
            return TYPE_MAP[base_type]
            break
    return None


class ModelView(View):
    def __init__(self, model_class=None, resource_name=None, *args, **kwargs):
        if model_class:
            self.model_class = model_class
        if not resource_name:
            self.resource_name = underscorize(self.model_class.__name__)


class ShowView(ModelView):
    def __init__(self, template=None, context={}, *args, **kwargs):
        ModelView.__init__(self, *args, **kwargs)

        if not hasattr(self, 'context'):
            self.context = context

        if not hasattr(self, 'template'):
            if template:
                self.template = template
            else:
                self.template = '%s/show.html' % self.resource_name

    def dispatch_request(self, *args, **kwargs):
        item = self.model_class.query.get_or_404(kwargs.values()[0])
        if callable(self.context):
            context = self.context(item=item)
        else:
            context = self.context

        return render_template(self.template, item=item, **context)


class FormView(ModelView):
    methods = ['GET', 'POST']

    def __init__(self, form_class=None, *args, **kwargs):
        ModelView.__init__(self, *args, **kwargs)
        if form_class:
            self.form_class = form_class
        self.success_redirect = '%s.show' % self.resource_name


class CreateFormView(FormView):
    def __init__(self, template=None, success_message=None, *args, **kwargs):
        FormView.__init__(self, *args, **kwargs)
        self.template = '%s/create.html' % self.resource_name
        if template:
            self.template = template
        self.success_message = '%s created!' % self.model_class.__name__
        if success_message:
            self.success_message = success_message

    def dispatch_request(self):
        model = self.model_class()
        form = self.form_class(formdata=request.form, obj=model)
        if form.validate_on_submit():
            form.populate_obj(model)
            db.session.add(model)
            db.session.commit()

            flash(self.success_message, 'success')
            return redirect(url_for(self.success_redirect, id=model.id))
        return render_template(self.template, form=form)


class UpdateFormView(FormView):
    def __init__(self, template=None, success_message=None, *args, **kwargs):
        FormView.__init__(self, *args, **kwargs)
        self.template = '%s/edit.html' % self.resource_name
        if template:
            self.template = template
        self.success_message = '%s updated!' % self.model_class.__name__
        if success_message:
            self.success_message = success_message

    def dispatch_request(self, *args, **kwargs):
        item = self.model_class.query.get_or_404(kwargs.values()[0])
        form = self.form_class(obj=item, formdata=request.form)
        if form.validate_on_submit():
            form.populate_obj(item)
            db.session.commit()
            flash(self.success_message, 'success')

            return redirect(url_for(self.success_redirect, id=item.id))
        return render_template(self.template, item=item, form=form)


class DeleteView(ModelView):
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
        db.session.delete(item)
        db.session.commit()
        flash(self.success_message, 'success')
        return redirect(url_for(self.success_redirect))


class SortedListView(ModelView):
    def __init__(self,
        query_field_names=None,
        columns=None,
        query=None,
        template=None,
        form_class=None,
        *args, **kwargs):
        ModelView.__init__(self, *args, **kwargs)

        if not hasattr(self, 'form_class'):
            if form_class:
                self.form_class = form_class

        if not hasattr(self, 'query'):
            if query:
                self.query = query
            else:
                self.query = self.model_class.query

        if not hasattr(self, 'query_field_names'):
            if query_field_names:
                self.query_field_names = query_field_names
            else:
                self.query_field_names = self.default_query_field_names()

        if not hasattr(self, 'columns'):
            if columns:
                self.columns = columns
            else:
                self.columns = self.default_columns()

        if not hasattr(self, 'template'):
            if template:
                self.template = template
            else:
                self.template = '%s/index.html' % self.resource_name

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

    def execute_query(self, query):
        return query.all()

    def entity_column(self, column):
        entities = [entity.entity_zero.class_ for entity in \
            self.query._entities]

        for entity in entities:
            columns = entity.__table__.columns
            if column in columns:
                return getattr(entity, column), columns[column]
        return None

    def append_filters(self, query):
        for row in self.columns:
            name, alias = row
            if name not in request.args:
                continue

            attr, column = self.entity_column(name)
            if not attr:
                continue

            native_type = get_native_type(column.type)

            if native_type in (str, unicode):
                query = query.filter(attr.startswith(request.args[name]))
            elif native_type is bool:
                if request.args[name] == 'y':
                    query = query.filter(attr == True)
                elif request.args[name] == 'n':
                    query = query.filter(attr == False)
        return query

    def dispatch_request(self):
        query = self.query
        entities = [entity.entity_zero.class_ for entity in \
            query._entities]
        query = self.append_filters(query)

        order_by = request.args.get('orderby', '+name')
        if len(order_by) <= 1:
            sign = '+'
            order_by = 'name'
        else:
            sign, order_by = order_by[0], order_by[1:]

        if sign == '+':
            func = db.asc
        else:
            func = db.desc

        for entity in entities:
            if order_by in entity.__table__.columns:
                query = query.order_by(func(getattr(entity, order_by)))
                break

        items = self.execute_query(query)

        form = None
        if hasattr(self, 'form_class') and self.form_class:
            form = self.form_class(request.args)

        args = copy(request.args.to_dict())
        if 'orderby' in args:
            del args['orderby']

        return render_template(
            self.template,
            items=items,
            columns=self.columns,
            form=form,
            order_by=order_by,
            order_sign=sign,
            args=args
        )


class ModelRouter(object):
    def __init__(self, model_class):
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

        self.routes = {
            'index': ['', SortedListView, {}],
            'create': ['/create', CreateFormView, {}],
            'edit': ['/{primary_key}/edit', UpdateFormView, {}],
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

    def register(self, blueprint):
        for key, value in self.routes.items():
            route, view, kwargs = value
            blueprint.add_url_rule(
                route,
                view_func=login_required(view.as_view(
                    key,
                    model_class=self.model_class,
                    **kwargs
                ))
            )